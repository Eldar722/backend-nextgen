# NextGen Career Matching — Backend API

> AI-сервис карьерного матчинга студентов и работодателей.  
> **Stack:** FastAPI · Supabase · Google Gemini 1.5 Flash · Groq llama-3.3-70b · PyGithub · pdfplumber

---

## Быстрый старт

```bash
# 1. Клонировать и перейти в папку
cd backend

# 2. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env
cp .env.example .env
# Заполнить все переменные (см. секцию ниже)

# 5. Применить SQL схему в Supabase (один раз)
# Скопировать SQL из секции ниже → Supabase SQL Editor → Run

# 6. Запустить
uvicorn app.main:app --reload --port 8000
```

**Документация:** http://localhost:8000/docs  
**Health check:** http://localhost:8000/health → `{"status":"healthy","version":"1.0.0"}`

---

## Переменные окружения (`.env`)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
GITHUB_TOKEN=your-github-personal-access-token
JWT_SECRET=your-supabase-jwt-secret
```

| Переменная | Где взять |
|---|---|
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → `service_role` key |
| `GEMINI_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens |
| `JWT_SECRET` | Supabase → Settings → API → JWT Secret |

---

## Структура проекта

```
backend/
├── app/
│   ├── main.py                  # FastAPI приложение, CORS, роутеры
│   ├── config.py                # Настройки из .env (pydantic-settings)
│   ├── db/
│   │   └── supabase_client.py   # Supabase клиент (service_role)
│   ├── middleware/
│   │   └── auth.py              # JWT верификация + role-based зависимости
│   ├── models/
│   │   ├── student.py           # Pydantic: профиль студента, GitHub, резюме
│   │   ├── vacancy.py           # Pydantic: создание/обновление вакансий
│   │   └── match.py             # Pydantic: матчинг, рекомендации, Gemini payload
│   ├── services/
│   │   ├── pdf_service.py       # pdfplumber — извлечение текста из PDF
│   │   ├── github_service.py    # PyGithub — анализ репозиториев
│   │   ├── groq_service.py      # Groq llama-3.3-70b — структурирование резюме
│   │   ├── gemini_service.py    # Gemini 1.5 Flash — матчинг и рекомендации
│   │   └── matching_service.py  # Бизнес-логика: кеш 24ч, вызов Gemini, upsert
│   └── routers/
│       ├── students.py          # /api/v1/students/*
│       ├── employers.py         # /api/v1/employers/*
│       ├── ai.py                # /api/v1/ai/*
│       └── analytics.py        # /api/v1/analytics/*
├── test_services.py             # Тест AI сервисов без Supabase
├── test_pdf_parsing.py          # Тест парсинга PDF резюме
├── .env.example                 # Шаблон переменных окружения
├── .gitignore
└── requirements.txt
```

---

## API Эндпоинты

### Students `/api/v1/students/` 🔒 role: student

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/profile` | Создать / обновить профиль |
| `GET` | `/profile` | Получить свой профиль |
| `POST` | `/upload-resume` | Загрузить PDF резюме (multipart/form-data) |
| `POST` | `/connect-github` | Привязать GitHub → добавить технологии |
| `GET` | `/matches` | Топ вакансий по AI матчингу |
| `GET` | `/recommendations` | Персональные карьерные советы от Gemini |

### Employers `/api/v1/employers/` 🔒 role: employer

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/vacancies` | Создать вакансию |
| `GET` | `/vacancies` | Список своих вакансий |
| `PUT` | `/vacancies/{id}` | Обновить вакансию |
| `GET` | `/vacancies/{id}/candidates` | Топ кандидатов (AI матчинг) |

### AI `/api/v1/ai/` 🔒 role: any

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/analyze-skills` | Извлечь навыки из произвольного текста (Groq) |
| `GET` | `/recommendations` | AI карьерные рекомендации (Gemini) |

### Analytics `/api/v1/analytics/` 🔒 role: any

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/top-skills` | Топ востребованных навыков/технологий на рынке |
| `GET` | `/readiness` | Распределение готовности студентов к трудоустройству |
| `GET` | `/trends` | Gap-анализ: спрос работодателей vs предложение студентов |

### Health (без авторизации)

| Метод | URL | Ответ |
|---|---|---|
| `GET` | `/` | `{"status":"ok","service":"...","version":"1.0.0"}` |
| `GET` | `/health` | `{"status":"healthy","version":"1.0.0"}` |

---

## AI Pipeline

```
POST /upload-resume
  └─ pdfplumber → извлечь текст
      └─ Groq (llama-3.3-70b) → структурировать в JSON {skills, technologies}
          └─ Merge с профилем → upsert в Supabase

POST /connect-github
  └─ PyGithub → репозитории + языки программирования
      └─ Добавить технологии к профилю студента

GET /matches
  └─ Для каждой активной вакансии:
      ├─ Найти кеш в matches (< 24ч) → вернуть сразу
      └─ Нет кеша → Gemini 1.5 Flash анализирует пару студент↔вакансия
              └─ upsert результата в matches → вернуть
```

---

## Авторизация

Используется **Supabase Auth**. Фронт логинится, получает JWT токен и передаёт его во все запросы:

```
Authorization: Bearer <supabase_jwt_token>
```

Роль задаётся при регистрации через `user_metadata.role`:

```js
await supabase.auth.signUp({
  email, password,
  options: { data: { role: 'student' } }  // 'student' | 'employer' | 'university'
})
```

---

## SQL Схема Supabase

Выполнить в **Supabase → SQL Editor**:

```sql
-- Профили студентов
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

-- Вакансии работодателей
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

-- Кеш результатов AI матчинга (TTL 24ч)
CREATE TABLE matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    vacancy_id UUID NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    match_percent INT NOT NULL CHECK (match_percent BETWEEN 0 AND 100),
    strong_skills TEXT[] DEFAULT '{}',
    missing_skills TEXT[] DEFAULT '{}',
    explanation TEXT,
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, vacancy_id)
);

-- История навыков студентов (снапшоты при каждом обновлении профиля)
CREATE TABLE skill_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    skills TEXT[] DEFAULT '{}',
    snapshot_date TIMESTAMPTZ DEFAULT NOW()
);

-- Автообновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_student_profiles_updated_at
    BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_vacancies_updated_at
    BEFORE UPDATE ON vacancies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Индексы
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_vacancies_employer_id ON vacancies(employer_id);
CREATE INDEX idx_vacancies_is_active ON vacancies(is_active);
CREATE INDEX idx_matches_student_id ON matches(student_id);
CREATE INDEX idx_matches_vacancy_id ON matches(vacancy_id);
CREATE INDEX idx_matches_cached_at ON matches(cached_at);
CREATE INDEX idx_skill_history_student_id ON skill_history(student_id);
```

### Supabase Storage

Создать bucket **`resumes`** в Storage → New bucket:
- **Name:** `resumes`
- **Public:** ✅ включить

---

## Тестирование

```bash
# Проверить AI сервисы без Supabase (Groq, Gemini, GitHub)
python test_services.py

# Проверить парсинг PDF резюме
python test_pdf_parsing.py

# Swagger UI (все эндпоинты)
# http://localhost:8000/docs
```

---

## Деплой

```bash
# Продакшен (4 воркера)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

> ⚠️ В продакшене заменить `allow_origins=["*"]` на конкретный домен фронтенда в `app/main.py`
