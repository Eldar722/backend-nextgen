"""
Pydantic модели для профиля студента.
Используются для валидации входящих данных и сериализации ответов.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class StudentProfileCreate(BaseModel):
    """Данные для создания или обновления профиля студента."""
    name: str = Field(..., min_length=2, max_length=100, description="ФИО студента")
    university: str = Field(..., min_length=2, max_length=200, description="Название университета")
    specialty: str = Field(..., min_length=2, max_length=200, description="Специальность/направление")
    skills: List[str] = Field(default_factory=list, description="Список навыков (soft skills)")
    technologies: List[str] = Field(default_factory=list, description="Технологии и инструменты")
    experience_text: Optional[str] = Field(None, max_length=5000, description="Описание опыта работы")
    github_url: Optional[str] = Field(None, description="Ссылка на GitHub профиль")
    career_interests: List[str] = Field(default_factory=list, description="Карьерные интересы")


class StudentProfileResponse(BaseModel):
    """Ответ с полными данными профиля студента."""
    id: str
    user_id: str
    name: str
    university: str
    specialty: str
    skills: List[str]
    technologies: List[str]
    experience_text: Optional[str]
    github_url: Optional[str]
    resume_url: Optional[str]
    career_interests: List[str]
    profile_completion: int = Field(description="Процент заполненности профиля (0-100)")
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GitHubConnectRequest(BaseModel):
    """Запрос на привязку GitHub аккаунта."""
    github_url: str = Field(..., description="URL GitHub профиля пользователя")


class GitHubConnectResponse(BaseModel):
    """Результат парсинга GitHub профиля."""
    github_url: str
    detected_technologies: List[str] = Field(description="Обнаруженные технологии из репозиториев")
    top_repos: List[dict] = Field(description="Топ репозиториев по активности")
    total_commits: int
    message: str


class ResumeUploadResponse(BaseModel):
    """Результат загрузки и парсинга резюме."""
    resume_url: str = Field(description="Публичный URL загруженного файла в Supabase Storage")
    extracted_skills: List[str]
    extracted_technologies: List[str]
    extracted_experience: Optional[str]
    message: str


def calculate_profile_completion(profile: dict) -> int:
    """
    Вычисляет процент заполненности профиля студента.
    Каждое заполненное поле добавляет очки.
    """
    score = 0
    checks = [
        (bool(profile.get("name")), 15),
        (bool(profile.get("university")), 15),
        (bool(profile.get("specialty")), 15),
        (len(profile.get("skills", [])) > 0, 15),
        (len(profile.get("technologies", [])) > 0, 15),
        (bool(profile.get("experience_text")), 10),
        (bool(profile.get("github_url")), 10),
        (bool(profile.get("resume_url")), 5),
    ]
    for condition, points in checks:
        if condition:
            score += points
    return min(score, 100)
