"""
Supabase клиент — единственная точка подключения к базе данных.
Использует service_role ключ для обхода RLS при серверных операциях.
"""
from supabase import create_client, Client
from app.config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_supabase() -> Client:
    """
    Возвращает кешированный Supabase клиент.
    service_role ключ даёт полный доступ в обход Row Level Security.
    """
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
