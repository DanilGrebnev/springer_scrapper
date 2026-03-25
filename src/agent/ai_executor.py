import os
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None

# Все роуты, отправляющие запросы к ИИ, должны использовать этот же executor.
# Не создавайте отдельный пул в каждом роуте — суммарный параллелизм контролируется здесь.
_MAX_WORKERS = int(os.getenv("AI_MAX_WORKERS", "3"))


def get_ai_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="ai_worker")
        logger.info("AI executor создан (max_workers=%d)", _MAX_WORKERS)
    return _executor


def shutdown_ai_executor(wait: bool = True) -> None:
    global _executor
    if _executor is not None:
        logger.info("Останавливаю AI executor (wait=%s)…", wait)
        _executor.shutdown(wait=wait)
        _executor = None
        logger.info("AI executor остановлен")
