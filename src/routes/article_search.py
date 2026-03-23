from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["articles"])


class ArticleSearchRequest(BaseModel):
    abstract_description: str = ""
    description: str = ""
    language: str = ""
    title: str = ""
    theme: str = ""
    date_from: Optional[int] = Field(None, alias="dateFrom")
    date_to: Optional[int] = Field(None, alias="dateTo")
    is_access: bool = Field(False, alias="isAccess")

    model_config = {"populate_by_name": True}


@router.post("/article-search")
async def article_search(body: ArticleSearchRequest):
    return {
        "received": body.model_dump(by_alias=True),
    }
