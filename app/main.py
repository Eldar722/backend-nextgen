"""
Точка входа FastAPI приложения.
Подключает все роутеры, настраивает CORS и middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import students, employers, ai, analytics

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    print(f"🚀 {settings.app_name} v{settings.app_version} запускается...")
    yield
    print("🛑 Приложение останавливается...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-сервис карьерного матчинга студентов и работодателей",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — разрешаем фронтенду обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры с общим префиксом /api/v1
app.include_router(students.router, prefix="/api/v1", tags=["Students"])
app.include_router(employers.router, prefix="/api/v1", tags=["Employers"])
app.include_router(ai.router, prefix="/api/v1", tags=["AI"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])


@app.get("/", tags=["Health"])
async def root():
    """Проверка работоспособности сервера."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Детальная проверка состояния сервиса."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }
