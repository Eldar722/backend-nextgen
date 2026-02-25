"""
Роутер AI — дополнительные AI-функции для студентов.
Включает прямые запросы к AI сервисам.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from app.middleware.auth import get_current_user, require_student, CurrentUser
from app.db.supabase_client import get_supabase
from app.models.match import RecommendationsResponse, AIRecommendation
from app.services.gemini_service import gemini_service
from app.services.groq_service import groq_service

router = APIRouter(prefix="/ai")

supabase = get_supabase()


class SkillAnalysisRequest(BaseModel):
    """Запрос на анализ навыков по произвольному тексту."""
    text: str
    context: Optional[str] = None


class SkillAnalysisResponse(BaseModel):
    """Результат анализа навыков."""
    extracted_skills: List[str]
    extracted_technologies: List[str]
    message: str


@router.post("/analyze-skills", response_model=SkillAnalysisResponse)
async def analyze_skills_from_text(
    request: SkillAnalysisRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Извлекает навыки и технологии из произвольного текста через Groq.
    Полезно для добавления навыков из описания проектов, сертификатов и т.д.
    """
    if len(request.text) > 3000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текст слишком длинный. Максимум 3000 символов.",
        )

    # Используем Groq для быстрого извлечения навыков
    structured = await groq_service.structure_resume_data(request.text)

    return SkillAnalysisResponse(
        extracted_skills=structured.get("skills", []),
        extracted_technologies=structured.get("technologies", []),
        message=f"Обнаружено {len(structured.get('skills', []))} навыков и {len(structured.get('technologies', []))} технологий",
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_ai_recommendations(
    current_user: CurrentUser = Depends(require_student),
):
    """
    Генерирует персонализированные AI рекомендации по развитию карьеры.
    Используется Gemini 1.5 Flash для глубокого анализа.
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
            detail="Профиль студента не найден. Создайте профиль сначала.",
        )

    student_profile = profile_result.data

    # Получаем актуальные вакансии для контекста рынка
    vacancies_resp = (
        supabase.table("vacancies")
        .select("title, company, required_technologies, required_skills")
        .eq("is_active", True)
        .limit(10)
        .execute()
    )
    top_vacancies = vacancies_resp.data or []

    # Генерируем рекомендации через Gemini
    raw = await gemini_service.generate_recommendations(student_profile, top_vacancies)

    recommendations = [
        AIRecommendation(**rec)
        for rec in raw.get("recommendations", [])
    ]

    return RecommendationsResponse(
        student_id=student_profile["id"],
        recommendations=recommendations,
        summary=raw.get("summary", ""),
        generated_at=datetime.now(timezone.utc),
    )
