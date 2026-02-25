"""
Сервис для парсинга GitHub профилей студентов.
Анализирует репозитории, определяет технологии и активность.
"""
from github import Github, GithubException, UnknownObjectException
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.config import get_settings
import asyncio

settings = get_settings()


class GitHubService:
    """Получение данных о разработчике из публичного GitHub профиля."""

    def __init__(self):
        # PyGithub клиент с токеном для увеличенного rate limit
        self._client = Github(settings.github_token)

    def _extract_username(self, github_url: str) -> str:
        """Извлекает username из URL вида https://github.com/username."""
        url = github_url.rstrip("/")
        username = url.split("/")[-1]
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный URL GitHub профиля",
            )
        return username

    async def analyze_profile(self, github_url: str) -> Dict[str, Any]:
        """
        Асинхронно анализирует GitHub профиль пользователя.
        Запускает синхронный код PyGithub в executor для неблокирующей работы.
        
        Returns:
            Словарь с технологиями, топ репозиториями и статистикой
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_analyze, github_url)

    def _sync_analyze(self, github_url: str) -> Dict[str, Any]:
        """Синхронная реализация парсинга (запускается в executor)."""
        username = self._extract_username(github_url)
        
        try:
            user = self._client.get_user(username)
        except UnknownObjectException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GitHub пользователь '{username}' не найден",
            )
        except GithubException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка GitHub API: {str(e)}",
            )

        # Получаем публичные репозитории (не форки)
        repos = list(user.get_repos())
        own_repos = [r for r in repos if not r.fork]

        # Подсчёт языков программирования по всем репозиториям
        language_counts: Dict[str, int] = {}
        for repo in own_repos[:50]:  # Ограничиваем для производительности
            if repo.language:
                language_counts[repo.language] = language_counts.get(repo.language, 0) + 1

        # Сортируем языки по частоте использования
        sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        detected_technologies = [lang for lang, _ in sorted_languages]

        # Топ-5 репозиториев по количеству звёзд
        top_repos = sorted(own_repos, key=lambda r: r.stargazers_count, reverse=True)[:5]
        top_repos_data = [
            {
                "name": repo.name,
                "description": repo.description or "",
                "language": repo.language or "Unknown",
                "stars": repo.stargazers_count,
                "url": repo.html_url,
            }
            for repo in top_repos
        ]

        # Общее количество коммитов (приблизительно через contributions)
        total_commits = sum(
            getattr(repo, "pushed_at", None) and repo.get_commits().totalCount or 0
            for repo in own_repos[:10]  # Только первые 10 для скорости
        ) if own_repos else 0

        return {
            "github_url": github_url,
            "username": username,
            "detected_technologies": detected_technologies,
            "language_stats": dict(sorted_languages),
            "top_repos": top_repos_data,
            "total_commits": total_commits,
            "public_repos_count": user.public_repos,
            "followers": user.followers,
        }


# Синглтон сервиса
github_service = GitHubService()
