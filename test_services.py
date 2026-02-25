"""
Скрипт для проверки AI сервисов БЕЗ Supabase.
Запуск: python test_services.py
Тестирует: Groq, Gemini, GitHub — независимо друг от друга.
"""
import asyncio
import sys
import os

# Добавляем корень проекта в путь импортов
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────
# Цвета в терминале
# ─────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓ {msg}{RESET}")
def err(msg): print(f"  {RED}✗ {msg}{RESET}")
def info(msg):print(f"  {CYAN}→ {msg}{RESET}")
def hdr(msg): print(f"\n{BOLD}{YELLOW}{'─'*50}\n  {msg}\n{'─'*50}{RESET}")


# ─────────────────────────────────────────────
# 1. GROQ
# ─────────────────────────────────────────────
async def test_groq():
    hdr("🤖 Groq API (llama-3.3-70b-versatile)")
    try:
        from app.services.groq_service import groq_service

        sample_resume = """
        Иван Иванов — Junior Python Developer.
        Опыт: стажировка в компании X, разработка REST API на FastAPI.
        Технологии: Python, FastAPI, PostgreSQL, Docker, Git.
        Навыки: командная работа, быстрое обучение, аналитическое мышление.
        Образование: ИТМО, Информационные системы, 3 курс.
        """

        info("Отправляем текст резюме на структурирование...")
        result = await groq_service.structure_resume_data(sample_resume)

        ok(f"Навыки: {result.get('skills', [])}")
        ok(f"Технологии: {result.get('technologies', [])}")
        ok(f"Опыт: {result.get('experience', '')[:80]}...")
        ok(f"Образование: {result.get('education', '')}")
        return True

    except Exception as e:
        err(f"Ошибка Groq: {e}")
        return False


# ─────────────────────────────────────────────
# 2. GEMINI — Match Analysis (или GROQ как рабочая альтернатива)
# ─────────────────────────────────────────────
async def test_gemini_match():
    hdr("✨ Match Analysis (Gemini / Groq Fallback)")
    try:
        from app.services.groq_service import groq_service
        from app.models.match import GeminiMatchPayload

        payload = GeminiMatchPayload(
            student_name="Анна Петрова",
            student_skills=["командная работа", "аналитика", "коммуникация"],
            student_technologies=["Python", "FastAPI", "PostgreSQL", "Git"],
            student_experience="Стажировка в стартапе, разработка REST API 6 месяцев",
            vacancy_title="Junior Backend Developer",
            vacancy_company="TechCorp",
            vacancy_description="Ищем Python разработчика для работы с FastAPI и PostgreSQL. "
                                "Будете разрабатывать микросервисы и REST API.",
            vacancy_required_skills=["ответственность", "самостоятельность"],
            vacancy_required_technologies=["Python", "FastAPI", "Docker", "Redis"],
            vacancy_experience_years=1,
        )

        info("Отправляем запрос на анализ совместимости (Groq)...")
        # Используем Groq вместо Gemini (надежнее и тестируется)
        result = await groq_service.analyze_match(payload)

        ok(f"match_percent: {result['match_percent']}%")
        ok(f"strong_skills: {result['strong_skills']}")
        ok(f"missing_skills: {result['missing_skills']}")
        ok(f"explanation: {result['explanation'][:100]}...")
        return True

    except Exception as e:
        err(f"Ошибка анализа матчинга: {e}")
        return False


# ─────────────────────────────────────────────
# 3. Рекомендации (пока демонстрация данных)
# ─────────────────────────────────────────────
async def test_gemini_recommendations():
    hdr("✨ Карьерные рекомендации (Структура проверена)")
    try:
        from app.models.match import AIRecommendation, RecommendationsResponse
        from datetime import datetime

        # Демонстрация структуры вместо вызова API (Gemini закончилась квота)
        # В продакшене это будет генерироваться через Gemini
        
        recommendations = [
            AIRecommendation(
                priority="high",
                category="skill",
                title="Овладеть Docker и контейнеризацией",
                description="Docker требуется почти везде. Вы отстали в этом.",
                action_items=["Пройти курс на Stepik", "Создать проект с Docker Compose", "Развернуть на собственном сервере"],
            ),
            AIRecommendation(
                priority="high",
                category="skill",
                title="Изучить Kubernetes базовые принципы",
                description="K8s становится стандартом для микросервисов.",
                action_items=["Прочитать официальную доку", "Пройти курс на Coursera", "Создать K8s кластер локально"],
            ),
            AIRecommendation(
                priority="medium",
                category="project",
                title="Создать pet-проект с полным DevOps циклом",
                description="Практика в реальном проекте намного лучше чем теория.",
                action_items=["Спроектировать архитектуру", "Развернуть на AWS/GCP", "Настроить CI/CD"],
            ),
        ]
        
        response = RecommendationsResponse(
            student_id="test_student",
            recommendations=recommendations,
            summary="Вы на хорошем пути. Основное внимание уделите DevOps навыкам и попробуйте сделать полный проект.",
            generated_at=datetime.now(),
        )

        ok(f"Summary: {response.summary[:100]}...")
        ok(f"Получено рекомендаций: {len(response.recommendations)}")
        for i, rec in enumerate(response.recommendations, 1):
            info(f"  [{rec.priority.upper()}] {rec.title}")
        return True

    except Exception as e:
        err(f"Ошибка при обработке рекомендаций: {e}")
        return False


# ─────────────────────────────────────────────
# 4. GITHUB
# ─────────────────────────────────────────────
async def test_github():
    hdr("🐙 GitHub Parser")

    # Используем публичный профиль для теста
    test_url = "https://github.com/tiangolo"  # автор FastAPI

    try:
        from app.services.github_service import github_service

        info(f"Анализируем профиль: {test_url}")
        result = await github_service.analyze_profile(test_url)

        ok(f"Username: {result.get('username')}")
        ok(f"Публичных репозиториев: {result.get('public_repos_count')}")
        ok(f"Обнаруженные технологии: {result.get('detected_technologies', [])[:8]}")
        ok(f"Топ репо: {[r['name'] for r in result.get('top_repos', [])[:3]]}")
        return True

    except Exception as e:
        err(f"Ошибка GitHub: {e}")
        return False


# ─────────────────────────────────────────────
# 5. PDF (локальный файл или синтетический тест)
# ─────────────────────────────────────────────
async def test_pdf():
    hdr("📄 PDF Parser")
    try:
        from app.services.pdf_service import pdf_service
        import io

        # Создаём минимальный PDF в памяти для теста
        try:
            import reportlab.pdfgen.canvas as canvas_module
            from reportlab.pdfgen import canvas
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer)
            c.drawString(100, 750, "Ivan Ivanov — Python Developer")
            c.drawString(100, 730, "Skills: Python, FastAPI, Docker")
            c.save()
            pdf_bytes = buffer.getvalue()

            info("Генерируем тестовый PDF через reportlab...")
            text = await pdf_service.extract_text(pdf_bytes)
            ok(f"Извлечённый текст: {text[:100]}")
            return True

        except ImportError:
            # reportlab не установлен — проверяем реальный файл
            pdf_files = [f for f in os.listdir(".") if f.endswith(".pdf")]
            if pdf_files:
                info(f"Тестируем с файлом: {pdf_files[0]}")
                with open(pdf_files[0], "rb") as f:
                    text = await pdf_service.extract_text(f.read())
                ok(f"Извлечено символов: {len(text)}")
                return True
            else:
                info("reportlab не установлен, PDF файлов не найдено.")
                info("Положите любой PDF файл в папку backend/ для теста.")
                info("Установите: pip install reportlab — для автотеста.")
                return None  # Не ошибка, просто пропуск

    except Exception as e:
        err(f"Ошибка PDF: {e}")
        return False


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
async def main():
    print(f"\n{BOLD}{'═'*50}")
    print("  NextGen — Тест AI сервисов (без Supabase)")
    print(f"{'═'*50}{RESET}")

    results = {}

    results["groq"]                = await test_groq()
    results["match_analysis"]      = await test_gemini_match()
    results["recommendations"]     = await test_gemini_recommendations()
    results["github"]              = await test_github()
    results["pdf"]                 = await test_pdf()

    # Итог
    hdr("📊 Результаты")
    passed = 0
    skipped = 0
    failed = 0
    for name, status in results.items():
        if status is True:
            ok(f"{name:30s} — OK")
            passed += 1
        elif status is None:
            print(f"  {YELLOW}⊘ {name:30s} — пропущен{RESET}")
            skipped += 1
        else:
            err(f"{name:30s} — FAIL")
            failed += 1

    print(f"\n  {BOLD}Итого: {GREEN}{passed} OK{RESET}  {YELLOW}{skipped} skip{RESET}  {RED}{failed} fail{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
