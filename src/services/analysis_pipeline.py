import asyncio
import logging

from src.agent.openai import OpenAIClient
from src.db.models.request import Request
from src.services.article_db_service import save_analysis_result, save_scraped_articles
from src.services.article_search_service import run_article_search

logger = logging.getLogger(__name__)


async def run_analysis_pipeline(request_obj: Request) -> None:
    """Полный пайплайн: скрапинг -> сохранение статей -> AI-анализ -> сохранение результата.

    Запускается как фоновая задача (asyncio.create_task). Все ошибки ловятся
    и записываются в request_obj.status / error_detail.
    """
    try:
        # 1. Скрапинг
        date_from = int(request_obj.date_from) if request_obj.date_from else None
        date_to = int(request_obj.date_to) if request_obj.date_to else None

        articles = await asyncio.to_thread(
            run_article_search,
            theme=request_obj.theme,
            date_from=date_from,
            date_to=date_to,
            open_access=request_obj.open_access,
        )

        # 2. Подсчёт и сохранение total_amount
        total = sum(len(v) for v in articles.values()) if articles else 0
        request_obj.total_amount = total
        await request_obj.save()
        logger.info("Request(%d): скрапинг завершён, total_amount=%d", request_obj.pk, total)

        if not articles or total == 0:
            request_obj.status = "success"
            await request_obj.save()
            logger.info("Request(%d): 0 статей, завершаем", request_obj.pk)
            return

        # 3. Сохраняем статьи в Article (дедупликация по link)
        articles_map = await save_scraped_articles(articles)

        # 4. AI-анализ
        context = {
            "field_knowledge": request_obj.field_knowledge,
            "target_context": request_obj.target_context,
            "target_theme": request_obj.target_theme,
            "language": request_obj.language,
        }

        logger.info("Request(%d): запуск AI-анализа", request_obj.pk)
        client = OpenAIClient()
        ai_result, usage, model_name = await asyncio.to_thread(
            client.filter_article, articles, context,
        )

        # 5. Сохраняем результат анализа
        await save_analysis_result(ai_result, articles_map, usage, model_name, request_obj)

        # 6. Успех
        request_obj.status = "success"
        await request_obj.save()
        logger.info("Request(%d): анализ завершён успешно", request_obj.pk)

    except Exception as exc:
        logger.exception("Request(%d): ошибка в пайплайне", request_obj.pk)
        request_obj.status = "error"
        request_obj.error_detail = str(exc)
        await request_obj.save()
