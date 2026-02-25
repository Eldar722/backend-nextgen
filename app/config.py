"""
Конфигурация приложения — читает переменные окружения из .env файла.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str

    # AI APIs
    gemini_api_key: str
    groq_api_key: str

    # GitHub
    github_token: str

    # JWT (секрет из Supabase Settings → API → JWT Secret)
    jwt_secret: str

    # Приложение
    app_name: str = "NextGen Career Matching API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Кеш матчинга в часах
    match_cache_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Кешированный экземпляр настроек — создаётся один раз."""
    return Settings()
