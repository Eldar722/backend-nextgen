"""
Gemini сервис — глубокий AI анализ для матчинга и рекомендаций.
Используется для сложных задач где важно качество, а не скорость.
"""
import json
import re
import asyncio
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from app.config import get_settings
from app.models.match import GeminiMatchPayload, AIRecommendation

settings = get_settings()

# Инициализация Gemini SDK
genai.configure(api_key=settings.gemini_api_key)


class GeminiService:
    """Клиент Google Gemini для AI анализа."""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        # Настройки безопасности и генерации
        self.generation_config = genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2048,
        )

    async def analyze_match(self, payload: GeminiMatchPayload) -> Dict[str, Any]:
        """
        Анализирует совместимость студента и вакансии.
        Возвращает процент совпадения, сильные стороны и пробелы.
        
        Args:
            payload: Данные студента и вакансии для анализа
            
        Returns:
            Словарь с match_percent, strong_skills, missing_skills, explanation
        """
        prompt = f"""Ты — AI рекрутер. Оцени совместимость студента и вакансии.

ПРОФИЛЬ СТУДЕНТА:
Имя: {payload.student_name}
Навыки: {', '.join(payload.student_skills)}
Технологии: {', '.join(payload.student_technologies)}
Опыт: {payload.student_experience or 'Не указан'}

ВАКАНСИЯ:
Должность: {payload.vacancy_title}
Компания: {payload.vacancy_company}
Описание: {payload.vacancy_description[:1000]}
Требуемые навыки: {', '.join(payload.vacancy_required_skills)}
Требуемые технологии: {', '.join(payload.vacancy_required_technologies)}
Лет опыта: {payload.vacancy_experience_years}

Верни ТОЛЬКО валидный JSON (без пояснений):
{{
  "match_percent": 75,
  "strong_skills": ["Python", "FastAPI"],
  "missing_skills": ["Docker", "Kubernetes"],
  "explanation": "Краткое объяснение результата на русском языке (2-3 предложения)"
}}

match_percent — целое число от 0 до 100."""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_analyze_match, prompt)

    def _sync_analyze_match(self, prompt: str) -> Dict[str, Any]:
        """Синхронный вызов Gemini API (выполняется в executor)."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
            )
            raw = response.text.strip()
            cleaned = re.sub(r"```(?:json)?", "", raw).strip()
            parsed = json.loads(cleaned)
            
            return {
                "match_percent": int(parsed.get("match_percent", 0)),
                "strong_skills": parsed.get("strong_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "explanation": parsed.get("explanation", ""),
            }
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini вернул невалидный JSON при анализе матчинга",
            )
        except Exception as e:
            error_msg = str(e)
            # Проверка на ошибку квоты — используем Groq вместо этого
            if "429" in error_msg or "quota" in error_msg.lower():
                # Fallback на Groq (синхронный вызов, но это нормально для executor)
                import asyncio
                try:
                    from app.services.groq_service import groq_service
                    # Нужно вызвать async метод синхронно
                    loop = asyncio.new_event_loop()
                    result = loop.run_until_complete(
                        self._groq_analyze_with_delay(groq_service)
                    )
                    loop.close()
                    return result
                except Exception as groq_error:
                    # Если и Groq не работает, возвращаем ошибку о квоте
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Gemini API: превышена квота бесплатного tier. "
                               f"Fallback на Groq также не сработал: {str(groq_error)[:100]}"
                    )
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка Gemini API: {error_msg[:200]}",
            )
    
    async def _groq_analyze_with_delay(self, groq_service) -> Dict[str, Any]:
        """Вспомогательный метод для вызова Groq (импортируем, чтобы избежать циклической зависимости)."""
        # Эта функция не используется из-за сложности с циклическими импортами
        # TODO: переделать архитектуру сервисов
        raise NotImplementedError("Используйте встроенный анализ Groq через отдельный endpoint")

    async def generate_recommendations(
        self,
        student_profile: Dict[str, Any],
        top_vacancies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Генерирует персонализированные карьерные рекомендации для студента.
        
        Args:
            student_profile: Данные профиля студента
            top_vacancies: Список актуальных вакансий для контекста
            
        Returns:
            Словарь с recommendations и summary
        """
        vacancies_summary = "\n".join([
            f"- {v.get('title', '')} в {v.get('company', '')}: {', '.join(v.get('required_technologies', [])[:5])}"
            for v in top_vacancies[:5]
        ])

        prompt = f"""Ты — AI карьерный консультант. Составь персонализированные рекомендации.

ПРОФИЛЬ СТУДЕНТА:
Специальность: {student_profile.get('specialty', '')}
Навыки: {', '.join(student_profile.get('skills', []))}
Технологии: {', '.join(student_profile.get('technologies', []))}
Карьерные интересы: {', '.join(student_profile.get('career_interests', []))}

АКТУАЛЬНЫЕ ВАКАНСИИ НА РЫНКЕ:
{vacancies_summary}

Верни ТОЛЬКО валидный JSON:
{{
  "summary": "Общая оценка карьерного потенциала (2-3 предложения)",
  "recommendations": [
    {{
      "priority": "high",
      "category": "skill",
      "title": "Изучить Docker и контейнеризацию",
      "description": "Описание почему это важно",
      "action_items": ["Пройти курс на Stepik", "Создать проект с Docker"]
    }}
  ]
}}

priority: high, medium или low.
category: skill, project, course или networking.
Дай 4-6 конкретных рекомендаций на русском языке."""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_recommendations, prompt)

    def _sync_recommendations(self, prompt: str) -> Dict[str, Any]:
        """Синхронный вызов для генерации рекомендаций."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
            )
            raw = response.text.strip()
            cleaned = re.sub(r"```(?:json)?", "", raw).strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini вернул невалидный JSON при генерации рекомендаций",
            )
        except Exception as e:
            error_msg = str(e)
            # Проверка на ошибку квоты
            if "429" in error_msg or "quota" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Gemini API: превышена квота бесплатного tier. "
                           "Активируйте платный аккаунт на https://ai.google.dev/",
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка Gemini API: {error_msg[:200]}",
            )


# Синглтон сервиса
gemini_service = GeminiService()
