"""
Роутер студентов — управление профилями, резюме и GitHub.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List
from datetime import datetime, timezone

from app.middleware.auth import get_current_user, require_student, CurrentUser
from app.db.supabase_client import get_supabase
from app.models.student import (
    StudentProfileCreate,
    StudentProfileResponse,
    GitHubConnectRequest,
    GitHubConnectResponse,
    ResumeUploadResponse,
    calculate_profile_completion,
)
from app.models.match import MatchResult, RecommendationsResponse, AIRecommendation
from app.services.pdf_service import pdf_service
from app.services.groq_service import groq_service
from app.services.github_service import github_service
from app.services.matching_service import matching_service
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/students")

supabase = get_supabase()


@router.post("/profile", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def upsert_student_profile(
    profile_data: StudentProfileCreate,
    current_user: CurrentUser = Depends(require_student),
):
    """
    Создаёт или обновляет профиль студента.
    Автоматически вычисляет процент заполненности и сохраняет снапшот навыков.
    """
    profile_dict = profile_data.model_dump()
    profile_dict["user_id"] = current_user.user_id
    profile_dict["profile_completion"] = calculate_profile_completion(profile_dict)

    # Проверяем: существует ли уже профиль этого пользователя
    existing = (
        supabase.table("student_profiles")
        .select("id, resume_url")
        .eq("user_id", current_user.user_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        # Обновляем существующий профиль
        profile_id = existing.data[0]["id"]
        # Сохраняем resume_url если новый профиль его не указывает
        if not profile_dict.get("resume_url"):
            profile_dict["resume_url"] = existing.data[0].get("resume_url")

        result = (
            supabase.table("student_profiles")
            .update(profile_dict)
            .eq("id", profile_id)
            .execute()
        )
    else:
        # Создаём новый профиль
        result = supabase.table("student_profiles").insert(profile_dict).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить профиль",
        )

    saved_profile = result.data[0]

    # Сохраняем снапшот навыков в skill_history
    _save_skill_snapshot(saved_profile["id"], profile_data.technologies + profile_data.skills)

    return StudentProfileResponse(**saved_profile)


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: CurrentUser = Depends(require_student),
):
    """Возвращает профиль текущего авторизованного студента."""
    result = (
        supabase.table("student_profiles")
        .select("*")
        .eq("user_id", current_user.user_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден. Создайте профиль через POST /students/profile",
        )

    return StudentProfileResponse(**result.data)


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_student),
):
    """
    Загружает PDF резюме, извлекает текст и структурирует данные через Groq.
    Файл сохраняется в Supabase Storage, URL записывается в профиль.
    """
    # Проверка типа файла
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допускаются только PDF файлы",
        )

    # Читаем файл
    file_bytes = await file.read()
    pdf_service.validate_file_size(len(file_bytes))

    # Извлекаем текст из PDF
    resume_text = await pdf_service.extract_text(file_bytes)

    # Структурируем данные через Groq
    structured_data = await groq_service.structure_resume_data(resume_text)

    # Загружаем файл в Supabase Storage
    storage_path = f"resumes/{current_user.user_id}/{file.filename}"
    supabase.storage.from_("resumes").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )

    # Получаем публичный URL файла
    public_url = supabase.storage.from_("resumes").get_public_url(storage_path)

    # Обновляем профиль студента — добавляем навыки из резюме
    profile_result = (
        supabase.table("student_profiles")
        .select("*")
        .eq("user_id", current_user.user_id)
        .limit(1)
        .execute()
    )

    if profile_result.data:
        profile = profile_result.data[0]
        # Объединяем существующие и новые навыки (без дубликатов)
        merged_skills = list(set(profile.get("skills", []) + structured_data["skills"]))
        merged_techs = list(set(profile.get("technologies", []) + structured_data["technologies"]))

        update_data = {
            "resume_url": public_url,
            "skills": merged_skills,
            "technologies": merged_techs,
            "experience_text": structured_data.get("experience") or profile.get("experience_text"),
        }
        update_data["profile_completion"] = calculate_profile_completion({**profile, **update_data})

        supabase.table("student_profiles").update(update_data).eq(
            "user_id", current_user.user_id
        ).execute()

    return ResumeUploadResponse(
        resume_url=public_url,
        extracted_skills=structured_data["skills"],
        extracted_technologies=structured_data["technologies"],
        extracted_experience=structured_data.get("experience"),
        message="Резюме успешно загружено и проанализировано",
    )


@router.post("/connect-github", response_model=GitHubConnectResponse)
async def connect_github(
    request: GitHubConnectRequest,
    current_user: CurrentUser = Depends(require_student),
):
    """
    Привязывает GitHub аккаунт к профилю.
    Парсит репозитории и добавляет обнаруженные технологии к профилю.
    """
    # Анализируем GitHub профиль
    github_data = await github_service.analyze_profile(request.github_url)

    # Обновляем профиль студента
    profile_result = (
        supabase.table("student_profiles")
        .select("*")
        .eq("user_id", current_user.user_id)
        .limit(1)
        .execute()
    )

    if profile_result.data:
        profile = profile_result.data[0]
        # Добавляем технологии из GitHub к существующим
        existing_techs = profile.get("technologies", [])
        new_techs = github_data["detected_technologies"]
        merged_techs = list(set(existing_techs + new_techs))

        update_data = {
            "github_url": request.github_url,
            "technologies": merged_techs,
        }
        update_data["profile_completion"] = calculate_profile_completion({**profile, **update_data})

        supabase.table("student_profiles").update(update_data).eq(
            "user_id", current_user.user_id
        ).execute()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сначала создайте профиль через POST /students/profile",
        )

    return GitHubConnectResponse(
        github_url=request.github_url,
        detected_technologies=github_data["detected_technologies"],
        top_repos=github_data["top_repos"],
        total_commits=github_data.get("total_commits", 0),
        message=f"GitHub успешно привязан. Обнаружено {len(github_data['detected_technologies'])} технологий.",
    )


@router.get("/matches", response_model=List[MatchResult])
async def get_student_matches(
    limit: int = 10,
    current_user: CurrentUser = Depends(require_student),
):
    """
    Возвращает топ вакансий, подходящих студенту.
    Использует кеш или вызывает Gemini для новых пар.
    """
    # Находим profile_id по user_id
    profile_result = (
        supabase.table("student_profiles")
        .select("id")
        .eq("user_id", current_user.user_id)
        .single()
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден. Создайте профиль чтобы получать рекомендации вакансий.",
        )

    student_id = profile_result.data["id"]
    matches = await matching_service.get_matches_for_student(student_id, limit=min(limit, 20))
    return matches


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    current_user: CurrentUser = Depends(require_student),
):
    """
    Генерирует персонализированные AI рекомендации для карьерного развития.
    Использует Gemini с учётом профиля и актуальных вакансий.
    """
    # Получаем профиль студента
    profile_result = (
        supabase.table("student_profiles")
        .select("*")
        .eq("user_id", current_user.user_id)
        .single()
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден",
        )

    student_profile = profile_result.data

    # Получаем актуальные вакансии для контекста
    vacancies_resp = (
        supabase.table("vacancies")
        .select("title, company, required_technologies, required_skills")
        .eq("is_active", True)
        .limit(10)
        .execute()
    )
    top_vacancies = vacancies_resp.data or []

    # Генерируем рекомендации через Gemini
    raw_recommendations = await gemini_service.generate_recommendations(
        student_profile, top_vacancies
    )

    # Преобразуем в Pydantic модели
    recommendations = [
        AIRecommendation(**rec) for rec in raw_recommendations.get("recommendations", [])
    ]

    return RecommendationsResponse(
        student_id=student_profile["id"],
        recommendations=recommendations,
        summary=raw_recommendations.get("summary", ""),
        generated_at=datetime.now(timezone.utc),
    )


def _save_skill_snapshot(student_id: str, skills: list) -> None:
    """
    Сохраняет снапшот навыков студента в таблицу skill_history.
    Вызывается при каждом обновлении профиля.
    """
    try:
        supabase.table("skill_history").insert({
            "student_id": student_id,
            "skills": skills,
            "snapshot_date": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        # Ошибка снапшота не должна блокировать основной запрос
        pass
