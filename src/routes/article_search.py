import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.article_search_service import run_article_search
from src.agent.openai import OpenAIClient

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
MOCK_FILE = RESULTS_DIR / "result_2026-03-24_02-49-27.json"
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["articles"])


class ArticleSearchRequest(BaseModel):
    field_knowledge: str = Field("", alias="fieldKnowledge")
    target_context: str = Field("", alias="targetContext")
    target_theme: str = Field("", alias="targetTheme")
    language: str = ""
    theme: str = ""
    date_from: Optional[int] = Field(None, alias="dateFrom")
    date_to: Optional[int] = Field(None, alias="dateTo")
    open_access: bool = Field(False, alias="openAccess")

    model_config = {"populate_by_name": True}


@router.post("/article-search")
def article_search(body: ArticleSearchRequest):
    # --- ВРЕМЕННАЯ ЗАГЛУШКА ДЛЯ ОТЛАДКИ ФРОНТА ---
    logger.info("Возврат захардкоженного результата из %s", MOCK_FILE)
    return json.loads(MOCK_FILE.read_text(encoding="utf-8"))
    # --- КОНЕЦ ЗАГЛУШКИ ---
    articles = run_article_search(
        theme=body.theme,
        date_from=body.date_from,
        date_to=body.date_to,
        open_access=body.open_access,
    )

    if not articles:
        return {
            "received": body.model_dump(by_alias=True),
            "articles": {},
            "ai_result": None,
        }

    context = {
        "field_knowledge": body.field_knowledge,
        "target_context": body.target_context,
        "target_theme": body.target_theme,
        "language": body.language,
    }

    logger.info("Запуск анализа статей через ИИ")
    client = OpenAIClient()
    ai_result = client.filter_article(articles, context)

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = f"result_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    filepath = RESULTS_DIR / filename
    filepath.write_text(json.dumps(ai_result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    logger.info("Результат сохранён в %s", filepath)

    return ai_result
