"""
Роутер аналитики — статистика по рынку труда для университетов и работодателей.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from collections import Counter

from app.middleware.auth import get_current_user, CurrentUser
from app.db.supabase_client import get_supabase

router = APIRouter(prefix="/analytics")

supabase = get_supabase()


@router.get("/top-skills")
async def get_top_skills(
    limit: int = Query(default=20, ge=5, le=50, description="Количество навыков в ответе"),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Топ навыков и технологий, востребованных работодателями.
    Анализирует все активные вакансии и считает частоту упоминания навыков.
    """
    # Получаем все активные вакансии
    vacancies_resp = (
        supabase.table("vacancies")
        .select("required_skills, required_technologies, soft_skills")
        .eq("is_active", True)
        .execute()
    )
    vacancies = vacancies_resp.data or []

    # Считаем частоту навыков
    tech_counter: Counter = Counter()
    skill_counter: Counter = Counter()

    for vacancy in vacancies:
        for tech in vacancy.get("required_technologies", []):
            tech_counter[tech] += 1
        for skill in vacancy.get("required_skills", []) + vacancy.get("soft_skills", []):
            skill_counter[skill] += 1

    return {
        "total_vacancies_analyzed": len(vacancies),
        "top_technologies": [
            {"name": tech, "count": count, "demand_percent": round(count / max(len(vacancies), 1) * 100)}
            for tech, count in tech_counter.most_common(limit)
        ],
        "top_skills": [
            {"name": skill, "count": count, "demand_percent": round(count / max(len(vacancies), 1) * 100)}
            for skill, count in skill_counter.most_common(limit)
        ],
    }


@router.get("/readiness")
async def get_student_readiness(
    specialty: Optional[str] = Query(None, description="Фильтр по специальности"),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Оценка готовности студентов к трудоустройству.
    Возвращает распределение profile_completion и среднее по навыкам.
    """
    query = supabase.table("student_profiles").select(
        "specialty, profile_completion, skills, technologies, career_interests"
    )

    if specialty:
        query = query.ilike("specialty", f"%{specialty}%")

    students_resp = query.execute()
    students = students_resp.data or []

    if not students:
        return {
            "total_students": 0,
            "message": "Нет данных по студентам",
        }

    # Вычисляем статистику
    completions = [s["profile_completion"] for s in students]
    avg_completion = sum(completions) / len(completions)

    # Распределение по уровням готовности
    low = sum(1 for c in completions if c < 40)
    medium = sum(1 for c in completions if 40 <= c < 70)
    high = sum(1 for c in completions if c >= 70)

    # Средние навыки студентов
    all_techs: Counter = Counter()
    for s in students:
        for tech in s.get("technologies", []):
            all_techs[tech] += 1

    # Группировка по специальностям
    specialties: Counter = Counter()
    for s in students:
        if s.get("specialty"):
            specialties[s["specialty"]] += 1

    return {
        "total_students": len(students),
        "average_profile_completion": round(avg_completion, 1),
        "readiness_distribution": {
            "low_under_40_percent": {"count": low, "percent": round(low / len(students) * 100)},
            "medium_40_70_percent": {"count": medium, "percent": round(medium / len(students) * 100)},
            "high_over_70_percent": {"count": high, "percent": round(high / len(students) * 100)},
        },
        "top_student_technologies": [
            {"name": tech, "count": count}
            for tech, count in all_techs.most_common(15)
        ],
        "top_specialties": [
            {"specialty": spec, "count": count}
            for spec, count in specialties.most_common(10)
        ],
    }


@router.get("/trends")
async def get_market_trends(
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Тренды рынка труда по технологиям и специальностям.
    Сравнивает спрос работодателей с предложением студентов.
    """
    # Спрос: технологии в вакансиях
    vacancies_resp = (
        supabase.table("vacancies")
        .select("required_technologies, experience_years, created_at")
        .eq("is_active", True)
        .execute()
    )
    vacancies = vacancies_resp.data or []

    # Предложение: технологии студентов
    students_resp = (
        supabase.table("student_profiles")
        .select("technologies, specialty")
        .execute()
    )
    students = students_resp.data or []

    demand: Counter = Counter()
    for v in vacancies:
        for tech in v.get("required_technologies", []):
            demand[tech] += 1

    supply: Counter = Counter()
    for s in students:
        for tech in s.get("technologies", []):
            supply[tech] += 1

    # Gap-анализ: технологии с высоким спросом и низким предложением
    gap_analysis = []
    for tech, demand_count in demand.most_common(30):
        supply_count = supply.get(tech, 0)
        gap_ratio = demand_count / max(supply_count, 1)
        gap_analysis.append({
            "technology": tech,
            "demand_count": demand_count,
            "supply_count": supply_count,
            "gap_ratio": round(gap_ratio, 2),
            "status": "deficit" if gap_ratio > 2 else "balanced" if gap_ratio > 0.5 else "surplus",
        })

    # Сортируем по дефициту
    gap_analysis.sort(key=lambda x: x["gap_ratio"], reverse=True)

    # Статистика по опыту в вакансиях
    exp_distribution = Counter()
    for v in vacancies:
        years = v.get("experience_years", 0)
        if years == 0:
            exp_distribution["Без опыта (0 лет)"] += 1
        elif years <= 1:
            exp_distribution["Джуниор (до 1 года)"] += 1
        elif years <= 3:
            exp_distribution["Мидл (1-3 года)"] += 1
        else:
            exp_distribution["Сеньор (3+ лет)"] += 1

    return {
        "total_active_vacancies": len(vacancies),
        "total_student_profiles": len(students),
        "technology_gap_analysis": gap_analysis[:20],
        "experience_demand_distribution": dict(exp_distribution),
        "most_demanded_technologies": [
            {"technology": t, "count": c} for t, c in demand.most_common(10)
        ],
        "most_common_student_technologies": [
            {"technology": t, "count": c} for t, c in supply.most_common(10)
        ],
    }
