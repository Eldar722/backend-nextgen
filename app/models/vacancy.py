"""
Pydantic модели для вакансий работодателей.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VacancyCreate(BaseModel):
    """Данные для создания новой вакансии."""
    title: str = Field(..., min_length=3, max_length=200, description="Название должности")
    company: str = Field(..., min_length=2, max_length=200, description="Название компании")
    description: str = Field(..., min_length=20, max_length=10000, description="Описание вакансии")
    required_skills: List[str] = Field(default_factory=list, description="Требуемые soft skills")
    required_technologies: List[str] = Field(default_factory=list, description="Требуемые технологии")
    experience_years: int = Field(default=0, ge=0, le=20, description="Лет опыта работы")
    soft_skills: List[str] = Field(default_factory=list, description="Личностные качества")


class VacancyUpdate(BaseModel):
    """Данные для обновления вакансии (все поля опциональны)."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    company: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=10000)
    required_skills: Optional[List[str]] = None
    required_technologies: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=20)
    soft_skills: Optional[List[str]] = None
    is_active: Optional[bool] = None


class VacancyResponse(BaseModel):
    """Полные данные вакансии в ответе API."""
    id: str
    employer_id: str
    title: str
    company: str
    description: str
    required_skills: List[str]
    required_technologies: List[str]
    experience_years: int
    soft_skills: List[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    """Кандидат на вакансию с результатами матчинга."""
    student_id: str
    name: str
    university: str
    specialty: str
    match_percent: int
    strong_skills: List[str]
    missing_skills: List[str]
    explanation: str
    github_url: Optional[str]
    resume_url: Optional[str]
