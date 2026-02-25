"""
Сервис матчинга — главная бизнес-логика приложения.
Проверяет кеш, вызывает Gemini при необходимости, сохраняет результаты.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.db.supabase_client import get_supabase
from app.services.gemini_service import gemini_service
from app.models.match import GeminiMatchPayload, MatchResult
from app.config import get_settings

settings = get_settings()


class MatchingService:
    """Сервис для поиска совместимых пар студент-вакансия."""

    def __init__(self):
        self.supabase = get_supabase()

    async def get_matches_for_student(
        self, student_id: str, limit: int = 10
    ) -> List[MatchResult]:
        """
        Находит топ вакансий для студента.
        
        Алгоритм:
        1. Получить профиль студента
        2. Получить активные вакансии
        3. Для каждой вакансии: проверить кеш → вызвать Gemini если нужно
        4. Отсортировать по match_percent и вернуть топ
        
        Args:
            student_id: ID профиля студента
            limit: Максимальное количество результатов
        """
        # Шаг 1: Загружаем профиль студента
        student_resp = (
            self.supabase.table("student_profiles")
            .select("*")
            .eq("id", student_id)
            .single()
            .execute()
        )
        if not student_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Профиль студента не найден",
            )
        student = student_resp.data

        # Шаг 2: Загружаем активные вакансии
        vacancies_resp = (
            self.supabase.table("vacancies")
            .select("*")
            .eq("is_active", True)
            .limit(50)
            .execute()
        )
        vacancies = vacancies_resp.data or []

        if not vacancies:
            return []

        results: List[MatchResult] = []

        for vacancy in vacancies:
            match_result = await self._get_or_compute_match(student, vacancy)
            results.append(match_result)

        # Сортируем по проценту совпадения (убывание)
        results.sort(key=lambda x: x.match_percent, reverse=True)
        return results[:limit]

    async def get_candidates_for_vacancy(
        self, vacancy_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Находит топ кандидатов для конкретной вакансии.
        
        Args:
            vacancy_id: ID вакансии
            limit: Максимальное количество кандидатов
        """
        # Получаем вакансию
        vacancy_resp = (
            self.supabase.table("vacancies")
            .select("*")
            .eq("id", vacancy_id)
            .single()
            .execute()
        )
        if not vacancy_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вакансия не найдена",
            )
        vacancy = vacancy_resp.data

        # Получаем всех студентов с завершёнными профилями
        students_resp = (
            self.supabase.table("student_profiles")
            .select("*")
            .gte("profile_completion", 30)  # Минимальная заполненность 30%
            .execute()
        )
        students = students_resp.data or []

        candidates = []
        for student in students:
            match_result = await self._get_or_compute_match(student, vacancy)
            candidates.append({
                "student_id": student["id"],
                "name": student.get("name", ""),
                "university": student.get("university", ""),
                "specialty": student.get("specialty", ""),
                "match_percent": match_result.match_percent,
                "strong_skills": match_result.strong_skills,
                "missing_skills": match_result.missing_skills,
                "explanation": match_result.explanation,
                "github_url": student.get("github_url"),
                "resume_url": student.get("resume_url"),
            })

        # Сортируем по проценту совпадения
        candidates.sort(key=lambda x: x["match_percent"], reverse=True)
        return candidates[:limit]

    async def _get_or_compute_match(
        self, student: Dict[str, Any], vacancy: Dict[str, Any]
    ) -> MatchResult:
        """
        Возвращает результат матчинга из кеша или вычисляет через Gemini.
        Кеш действителен в течение MATCH_CACHE_HOURS часов.
        """
        student_id = student["id"]
        vacancy_id = vacancy["id"]
        cache_threshold = datetime.now(timezone.utc) - timedelta(hours=settings.match_cache_hours)

        # Проверяем кеш в таблице matches
        cached_resp = (
            self.supabase.table("matches")
            .select("*")
            .eq("student_id", student_id)
            .eq("vacancy_id", vacancy_id)
            .gte("cached_at", cache_threshold.isoformat())
            .limit(1)
            .execute()
        )

        if cached_resp.data:
            # Кеш актуален — возвращаем без вызова AI
            cached = cached_resp.data[0]
            return MatchResult(
                vacancy_id=vacancy_id,
                title=vacancy.get("title", ""),
                company=vacancy.get("company", ""),
                match_percent=cached["match_percent"],
                strong_skills=cached.get("strong_skills", []),
                missing_skills=cached.get("missing_skills", []),
                explanation=cached.get("explanation", ""),
                cached=True,
                cached_at=cached.get("cached_at"),
            )

        # Кеша нет — вызываем Gemini для анализа
        payload = GeminiMatchPayload(
            student_name=student.get("name", ""),
            student_skills=student.get("skills", []),
            student_technologies=student.get("technologies", []),
            student_experience=student.get("experience_text"),
            vacancy_title=vacancy.get("title", ""),
            vacancy_company=vacancy.get("company", ""),
            vacancy_description=vacancy.get("description", ""),
            vacancy_required_skills=vacancy.get("required_skills", []),
            vacancy_required_technologies=vacancy.get("required_technologies", []),
            vacancy_experience_years=vacancy.get("experience_years", 0),
        )

        gemini_result = await gemini_service.analyze_match(payload)

        # Сохраняем результат в кеш (upsert — обновляем если уже есть)
        match_data = {
            "student_id": student_id,
            "vacancy_id": vacancy_id,
            "match_percent": gemini_result["match_percent"],
            "strong_skills": gemini_result["strong_skills"],
            "missing_skills": gemini_result["missing_skills"],
            "explanation": gemini_result["explanation"],
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self.supabase.table("matches").upsert(
            match_data,
            on_conflict="student_id,vacancy_id",
        ).execute()

        return MatchResult(
            vacancy_id=vacancy_id,
            title=vacancy.get("title", ""),
            company=vacancy.get("company", ""),
            match_percent=gemini_result["match_percent"],
            strong_skills=gemini_result["strong_skills"],
            missing_skills=gemini_result["missing_skills"],
            explanation=gemini_result["explanation"],
            cached=False,
        )


# Синглтон сервиса
matching_service = MatchingService()
