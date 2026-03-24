import logging

from tortoise import Tortoise

from src.db.config import DATABASE_URL

logger = logging.getLogger(__name__)


async def check_db() -> None:
    """Проверяет доступность БД после инициализации Tortoise.

    Выполняет простой запрос SELECT 1. Если БД недоступна — выбрасывает
    исключение, что прерывает запуск приложения с понятным сообщением об ошибке.
    """
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        # Скрываем credentials из URL для безопасного логирования
        safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
        logger.info("Database connection OK: %s", safe_url)
    except Exception as exc:
        logger.error("Database check failed: %s", exc)
        raise
