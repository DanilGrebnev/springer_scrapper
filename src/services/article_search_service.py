import logging
from typing import Optional
from src.scrapper.springer.scrapping import ScrappingService

logger = logging.getLogger(__name__)


def run_article_search(
    theme: str,
    date_from: Optional[int],
    date_to: Optional[int],
    open_access: bool,
) -> dict:
    search_params = {
        "query": theme,
        "page": "",
        "dateFrom": str(date_from) if date_from is not None else "",
        "dateTo": str(date_to) if date_to is not None else "",
        "sortBy": "relevance",
        "openAccess": "true" if open_access else "false",
    }

    logger.info("=== [1/3] Параметры запроса к скраперу ===")
    for key, value in search_params.items():
        logger.info("  %-12s: %s", key, value)

    logger.info("=== [2/3] Запуск ScrappingService ===")
    service = ScrappingService(search_params)
    result = service.start() or {}

    total_articles = sum(len(v) for v in result.values())
    logger.info("=== [3/3] Скрапинг завершён: страниц=%d, статей=%d ===", len(result), total_articles)

    return result
