"""
Роутер работодателей — управление вакансиями и просмотр кандидатов.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.middleware.auth import require_employer, CurrentUser
from app.db.supabase_client import get_supabase
from app.models.vacancy import (
    VacancyCreate,
    VacancyUpdate,
    VacancyResponse,
    CandidateResponse,
)
from app.services.matching_service import matching_service

router = APIRouter(prefix="/employers")

supabase = get_supabase()


@router.post("/vacancies", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy_data: VacancyCreate,
    current_user: CurrentUser = Depends(require_employer),
):
    """
    Создаёт новую вакансию от имени работодателя.
    Вакансия сразу становится активной.
    """
    vacancy_dict = vacancy_data.model_dump()
    vacancy_dict["employer_id"] = current_user.user_id
    vacancy_dict["is_active"] = True

    result = supabase.table("vacancies").insert(vacancy_dict).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать вакансию",
        )

    return VacancyResponse(**result.data[0])


@router.get("/vacancies", response_model=List[VacancyResponse])
async def list_employer_vacancies(
    current_user: CurrentUser = Depends(require_employer),
):
    """
    Возвращает список всех вакансий текущего работодателя.
    Включает как активные, так и деактивированные.
    """
    result = (
        supabase.table("vacancies")
        .select("*")
        .eq("employer_id", current_user.user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [VacancyResponse(**v) for v in (result.data or [])]


@router.put("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    vacancy_id: str,
    vacancy_data: VacancyUpdate,
    current_user: CurrentUser = Depends(require_employer),
):
    """
    Обновляет существующую вакансию.
    Проверяет что вакансия принадлежит текущему работодателю.
    """
    # Проверяем владельца вакансии
    existing = (
        supabase.table("vacancies")
        .select("id, employer_id")
        .eq("id", vacancy_id)
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена",
        )

    if existing.data["employer_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на редактирование этой вакансии",
        )

    # Обновляем только переданные поля (exclude_none=True)
    update_dict = vacancy_data.model_dump(exclude_none=True)

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления",
        )

    result = (
        supabase.table("vacancies")
        .update(update_dict)
        .eq("id", vacancy_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить вакансию",
        )

    return VacancyResponse(**result.data[0])


@router.get("/vacancies/{vacancy_id}/candidates", response_model=List[CandidateResponse])
async def get_vacancy_candidates(
    vacancy_id: str,
    limit: int = 10,
    current_user: CurrentUser = Depends(require_employer),
):
    """
    Возвращает топ кандидатов на вакансию по результатам AI матчинга.
    Проверяет что вакансия принадлежит текущему работодателю.
    """
    # Проверяем владельца вакансии
    existing = (
        supabase.table("vacancies")
        .select("id, employer_id")
        .eq("id", vacancy_id)
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена",
        )

    if existing.data["employer_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на просмотр кандидатов для этой вакансии",
        )

    candidates = await matching_service.get_candidates_for_vacancy(
        vacancy_id, limit=min(limit, 20)
    )

    return [CandidateResponse(**c) for c in candidates]
