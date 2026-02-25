"""
Groq сервис — быстрое структурирование данных резюме через LLM.
Использует llama-3.3-70b-versatile для извлечения навыков из текста.
"""
import json
import re
from groq import AsyncGroq
from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.config import get_settings

settings = get_settings()


class GroqService:
    """Клиент Groq API для быстрой обработки текста резюме."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_match(self, payload: "GeminiMatchPayload") -> Dict[str, Any]:
        """
        Анализирует совместимость студента и вакансии (дешевле чем Gemini).
        Используется как fallback если Gemini недоступен.
        
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
Описание: {payload.vacancy_description[:800]}
Требуемые навыки: {', '.join(payload.vacancy_required_skills)}
Требуемые технологии: {', '.join(payload.vacancy_required_technologies)}
Опыт требуется: {payload.vacancy_experience_years} лет

Верни ТОЛЬКО валидный JSON (без пояснений):
{{
  "match_percent": 75,
  "strong_skills": ["Python", "FastAPI"],
  "missing_skills": ["Docker", "Kubernetes"],
  "explanation": "Объяснение на русском (2-3 предложения)"
}}

match_percent — целое число от 0 до 100."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты рекрутер. Всегда возвращай только валидный JSON без дополнительного текста.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=512,
            )
            
            raw_response = response.choices[0].message.content.strip()
            cleaned = re.sub(r"```(?:json)?", "", raw_response).strip()
            parsed = json.loads(cleaned)
            
            return {
                "match_percent": int(parsed.get("match_percent", 0)),
                "strong_skills": parsed.get("strong_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "explanation": parsed.get("explanation", ""),
            }
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Groq вернул невалидный JSON при анализе матчинга: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка Groq API (анализ матчинга): {str(e)}",
            )

    async def structure_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """
        Структурирует текст резюме в JSON с ключевыми полями.
        Groq используется здесь благодаря muy высокой скорости ответа.
        
        Args:
            resume_text: Сырой текст из PDF резюме
            
        Returns:
            Словарь с полями: skills, technologies, experience, education
        """
        prompt = f"""Ты — парсер резюме. Проанализируй текст резюме и верни ТОЛЬКО валидный JSON.

Текст резюме:
---
{resume_text[:4000]}
---

Верни JSON строго в таком формате (без пояснений, только JSON):
{{
  "skills": ["навык1", "навык2"],
  "technologies": ["технология1", "технология2"],
  "experience": "Краткое описание опыта работы",
  "education": "Учебное заведение и специальность",
  "languages": ["Русский", "Английский"]
}}

В "skills" включи: коммуникация, работа в команде, аналитика и т.п.
В "technologies" включи: языки программирования, фреймворки, инструменты.
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты парсер резюме. Всегда возвращай только валидный JSON без дополнительного текста.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Низкая температура для точности
                max_tokens=1024,
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Очищаем ответ от возможных markdown-блоков
            cleaned = re.sub(r"```(?:json)?", "", raw_response).strip()
            
            parsed = json.loads(cleaned)
            
            # Гарантируем наличие всех ключей
            return {
                "skills": parsed.get("skills", []),
                "technologies": parsed.get("technologies", []),
                "experience": parsed.get("experience", ""),
                "education": parsed.get("education", ""),
                "languages": parsed.get("languages", []),
            }
            
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Groq вернул невалидный JSON: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка Groq API: {str(e)}",
            )

    async def generate_skill_tags(self, text: str) -> List[str]:
        """
        Быстро извлекает список технологий из произвольного текста.
        Используется при дополнительной обработке.
        """
        prompt = f"""Из текста ниже извлеки все технические навыки, технологии и инструменты.
Верни только JSON массив строк, например: ["Python", "FastAPI", "Docker"]

Текст: {text[:2000]}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512,
            )
            raw = response.choices[0].message.content.strip()
            cleaned = re.sub(r"```(?:json)?", "", raw).strip()
            return json.loads(cleaned)
        except Exception:
            return []


# Синглтон сервиса
groq_service = GroqService()
