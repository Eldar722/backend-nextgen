"""
Middleware аутентификации — проверяет JWT токены Supabase.
Извлекает user_id и роль пользователя из каждого запроса.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
from app.config import get_settings

settings = get_settings()

# Схема Bearer токена для FastAPI Security
security = HTTPBearer()


class CurrentUser:
    """Представляет аутентифицированного пользователя из JWT токена."""

    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


def decode_supabase_jwt(token: str) -> dict:
    """
    Декодирует и верифицирует JWT токен Supabase.
    Supabase использует HS256 алгоритм с JWT_SECRET.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase не всегда включает aud
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалидный токен авторизации: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Dependency для защищённых эндпоинтов.
    Проверяет токен и возвращает данные текущего пользователя.
    """
    token = credentials.credentials
    payload = decode_supabase_jwt(token)

    user_id: Optional[str] = payload.get("sub")
    email: Optional[str] = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит идентификатор пользователя",
        )

    # Роль хранится в метаданных пользователя Supabase
    user_metadata = payload.get("user_metadata", {})
    app_metadata = payload.get("app_metadata", {})
    role = user_metadata.get("role") or app_metadata.get("role") or "student"

    return CurrentUser(user_id=user_id, email=email or "", role=role)


async def require_student(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency — разрешает доступ только студентам."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только для студентов",
        )
    return current_user


async def require_employer(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency — разрешает доступ только работодателям."""
    if current_user.role != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только для работодателей",
        )
    return current_user


async def require_university(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency — разрешает доступ только университетам."""
    if current_user.role not in ("university", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только для университетов",
        )
    return current_user
