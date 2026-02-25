# NextGen Career Matching — Backend API

AI-сервис карьерного матчинга студентов и работодателей на основе FastAPI + Supabase + Google Gemini + Groq.

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Создать .env файл
cp .env.example .env
# Заполнить переменные в .env

# 3. Применить SQL схему в Supabase (см. ниже)

# 4. Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Документация API: http://localhost:8000/docs

---

## SQL Схема Supabase

Выполните следующие SQL запросы в **Supabase SQL Editor**:

```sql
-- Таблица профилей студентов
CREATE TABLE student_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    university TEXT NOT NULL,
    specialty TEXT NOT NULL,
    skills TEXT[] DEFAULT '{}',
    technologies TEXT[] DEFAULT '{}',
    experience_text TEXT,
    github_url TEXT,
    resume_url TEXT,
    career_interests TEXT[] DEFAULT '{}',
    profile_completion INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Таблица вакансий работодателей
CREATE TABLE vacancies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    description TEXT NOT NULL,
    required_skills TEXT[] DEFAULT '{}',
    required_technologies TEXT[] DEFAULT '{}',
    experience_years INT DEFAULT 0,
    soft_skills TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица кешированных результатов матчинга
CREATE TABLE matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    vacancy_id UUID NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    match_percent INT NOT NULL CHECK (match_percent >= 0 AND match_percent <= 100),
    strong_skills TEXT[] DEFAULT '{}',
    missing_skills TEXT[] DEFAULT '{}',
    explanation TEXT,
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, vacancy_id)
);

-- Таблица истории навыков студентов
CREATE TABLE skill_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    skills TEXT[] DEFAULT '{}',
    snapshot_date TIMESTAMPTZ DEFAULT NOW()
);

-- Автообновление updated_at при изменениях
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_student_profiles_updated_at
    BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_vacancies_updated_at
    BEFORE UPDATE ON vacancies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Индексы для производительности
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_vacancies_employer_id ON vacancies(employer_id);
CREATE INDEX idx_vacancies_is_active ON vacancies(is_active);
CREATE INDEX idx_matches_student_id ON matches(student_id);
CREATE INDEX idx_matches_vacancy_id ON matches(vacancy_id);
CREATE INDEX idx_matches_cached_at ON matches(cached_at);
CREATE INDEX idx_skill_history_student_id ON skill_history(student_id);
```

### Supabase Storage

Создайте bucket с именем `resumes` в **Storage → New bucket**:
- **Name**: `resumes`
- **Public**: ✅ (включить для публичных URL резюме)

### Настройка JWT

В **Settings → API** скопируйте `JWT Secret` в переменную `JWT_SECRET`.

Роли пользователей задаются через **Supabase Auth → Users** или при регистрации через `user_metadata`:

```json
{
  "role": "student"
}
```

Доступные роли: `student`, `employer`, `university`.

---

## Архитектура

```
app/
├── main.py                  # FastAPI точка входа
├── config.py                # Настройки из .env
├── db/
│   └── supabase_client.py   # Supabase клиент
├── middleware/
│   └── auth.py              # JWT аутентификация + role-based доступ
├── models/
│   ├── student.py           # Pydantic модели студентов
│   ├── vacancy.py           # Pydantic модели вакансий
│   └── match.py             # Pydantic модели матчинга
├── services/
│   ├── pdf_service.py       # Парсинг PDF резюме
│   ├── github_service.py    # Анализ GitHub профилей
│   ├── groq_service.py      # Groq API (структурирование данных)
│   ├── gemini_service.py    # Gemini API (матчинг + рекомендации)
│   └── matching_service.py  # Бизнес-логика матчинга + кеш
└── routers/
    ├── students.py          # /api/v1/students/*
    ├── employers.py         # /api/v1/employers/*
    ├── ai.py                # /api/v1/ai/*
    └── analytics.py        # /api/v1/analytics/*
```

## Эндпоинты

| Метод | URL | Роль | Описание |
|-------|-----|------|----------|
| POST | `/api/v1/students/profile` | student | Создать/обновить профиль |
| GET | `/api/v1/students/profile` | student | Получить свой профиль |
| POST | `/api/v1/students/upload-resume` | student | Загрузить PDF резюме |
| POST | `/api/v1/students/connect-github` | student | Привязать GitHub |
| GET | `/api/v1/students/matches` | student | Топ подходящих вакансий |
| GET | `/api/v1/students/recommendations` | student | AI карьерные советы |
| POST | `/api/v1/employers/vacancies` | employer | Создать вакансию |
| GET | `/api/v1/employers/vacancies` | employer | Мои вакансии |
| PUT | `/api/v1/employers/vacancies/{id}` | employer | Обновить вакансию |
| GET | `/api/v1/employers/vacancies/{id}/candidates` | employer | Топ кандидатов |
| POST | `/api/v1/ai/analyze-skills` | any | Извлечь навыки из текста |
| GET | `/api/v1/ai/recommendations` | student | AI рекомендации |
| GET | `/api/v1/analytics/top-skills` | any | Топ востребованных навыков |
| GET | `/api/v1/analytics/readiness` | any | Готовность студентов |
| GET | `/api/v1/analytics/trends` | any | Тренды рынка труда |
