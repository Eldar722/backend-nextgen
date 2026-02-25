"""
Pydantic модели для результатов матчинга студентов и вакансий.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MatchResult(BaseModel):
    """Результат AI матчинга для одной пары студент-вакансия."""
    vacancy_id: str
    title: str
    company: str
    match_percent: int = Field(ge=0, le=100, description="Процент совпадения (0-100)")
    strong_skills: List[str] = Field(description="Навыки, совпавшие с требованиями вакансии")
    missing_skills: List[str] = Field(description="Навыки, которых не хватает для вакансии")
    explanation: str = Field(description="AI объяснение результата матчинга")
    cached: bool = Field(default=False, description="True если результат взят из кеша")
    cached_at: Optional[datetime] = None


class MatchListResponse(BaseModel):
    """Список найденных вакансий для студента."""
    student_id: str
    matches: List[MatchResult]
    total: int


class AIRecommendation(BaseModel):
    """AI рекомендация по развитию карьеры студента."""
    priority: str = Field(description="high / medium / low")
    category: str = Field(description="Категория рекомендации: skill/project/course/networking")
    title: str
    description: str
    action_items: List[str] = Field(description="Конкретные шаги для выполнения рекомендации")


class RecommendationsResponse(BaseModel):
    """Полный список AI рекомендаций для студента."""
    student_id: str
    recommendations: List[AIRecommendation]
    summary: str = Field(description="Общее резюме карьерного потенциала")
    generated_at: datetime


class GeminiMatchPayload(BaseModel):
    """
    Внутренний payload для отправки в Gemini API.
    Не используется в HTTP ответах.
    """
    student_name: str
    student_skills: List[str]
    student_technologies: List[str]
    student_experience: Optional[str]
    vacancy_title: str
    vacancy_company: str
    vacancy_description: str
    vacancy_required_skills: List[str]
    vacancy_required_technologies: List[str]
    vacancy_experience_years: int
