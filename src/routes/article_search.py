import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth.deps import get_current_user_id
from src.db.models.request import Request
from src.services.analysis_pipeline import run_analysis_pipeline
from src.services.article_db_service import build_result_from_db
from src.services.status_messages import (
    analyzing_message,
    collecting_message,
    error_message,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["articles"])


# --------------- Schemas ---------------

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


class CheckSearchRequest(BaseModel):
    request_id: int


class AmountArticles(BaseModel):
    high_match: int = 0
    medium_match: int = 0
    low_match: int = 0


class HistoryItem(BaseModel):
    id: int
    target_theme: str
    field_knowledge: str
    dateFrom: int | None = None
    dateTo: int | None = None
    amount_articles: AmountArticles


# --------------- Routes ---------------

@router.get("/history", response_model=list[HistoryItem])
async def history(user_id: int = Depends(get_current_user_id)):
    requests = (
        await Request.filter(author_id=user_id)
        .prefetch_related("results__articles")
        .order_by("-id")
    )

    items: list[HistoryItem] = []
    for req in requests:
        high = medium = low = 0
        for rr in await req.results.all():
            for match in await rr.articles.all():
                level = match.level_match
                if level == "high_match":
                    high += 1
                elif level == "medium_match":
                    medium += 1
                elif level == "low_match":
                    low += 1

        def _to_int(val: str) -> int | None:
            try:
                return int(val) if val else None
            except ValueError:
                return None

        items.append(HistoryItem(
            id=req.id,
            target_theme=req.target_theme,
            field_knowledge=req.field_knowledge,
            dateFrom=_to_int(req.date_from),
            dateTo=_to_int(req.date_to),
            amount_articles=AmountArticles(
                high_match=high,
                medium_match=medium,
                low_match=low,
            ),
        ))

    return items

@router.get("/history-detail")
async def history_detail(
    id: int,
    user_id: int = Depends(get_current_user_id),
):
    request_obj = await Request.filter(id=id, author_id=user_id).first()
    if request_obj is None:
        raise HTTPException(404, "Request not found")

    result = await build_result_from_db(request_obj)
    result["filters"] = {
        "field_knowledge": request_obj.field_knowledge,
        "target_theme": request_obj.target_theme,
        "target_context": request_obj.target_context,
        "language": request_obj.language,
        "theme": request_obj.theme,
        "dateFrom": int(request_obj.date_from) if request_obj.date_from else None,
        "dateTo": int(request_obj.date_to) if request_obj.date_to else None,
        "openAccess": request_obj.open_access,
    }
    return result


@router.post("/article-search")
async def article_search(
    body: ArticleSearchRequest,
    user_id: int = Depends(get_current_user_id),
):
    request_obj = await Request.create(
        author_id=user_id,
        status="process",
        field_knowledge=body.field_knowledge,
        target_theme=body.target_theme,
        target_context=body.target_context,
        language=body.language,
        theme=body.theme,
        date_from=str(body.date_from) if body.date_from is not None else "",
        date_to=str(body.date_to) if body.date_to is not None else "",
        open_access=body.open_access,
    )
    logger.info("Request(%d) создан для user_id=%d, запускаем pipeline", request_obj.pk, user_id)

    asyncio.create_task(run_analysis_pipeline(request_obj))

    return {"request_id": request_obj.pk, "status": "process"}


@router.post("/check-search")
async def check_search(
    body: CheckSearchRequest,
    user_id: int = Depends(get_current_user_id),
):
    request_obj = await Request.filter(id=body.request_id, author_id=user_id).first()
    if request_obj is None:
        raise HTTPException(404, "Request not found")

    if request_obj.status == "error":
        return {
            "status": "error",
            "message": error_message(),
            "result": None,
        }

    if request_obj.status == "process":
        if request_obj.total_amount == 0:
            return {
                "status": "process",
                "message": collecting_message(),
                "result": None,
            }
        return {
            "status": "process",
            "message": analyzing_message(request_obj.total_amount),
            "result": None,
        }

    # status == "success"
    result = await build_result_from_db(request_obj)
    return {
        "status": "success",
        "message": "",
        "result": result,
    }
