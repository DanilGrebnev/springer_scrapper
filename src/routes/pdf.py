import io
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.auth.deps import get_current_user_id
from src.db.models.request import Request
from src.services.pdf_service import render_request_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pdf"])


@router.get(
    "/pdf",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "PDF-отчёт по запросу (принудительное скачивание).",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        },
        404: {"description": "Запроса с таким id не существует или он принадлежит другому пользователю."},
        409: {"description": "Запрос ещё не завершён — PDF-отчёт недоступен."},
    },
)
async def export_request_pdf(
    id: int,
    user_id: int = Depends(get_current_user_id),
):
    request_obj = await Request.filter(id=id, author_id=user_id).first()
    if request_obj is None:
        raise HTTPException(404, "Request not found")

    if request_obj.status != "success":
        raise HTTPException(
            409,
            f"Request is not ready for export (status={request_obj.status})",
        )

    try:
        pdf_bytes = await render_request_pdf(request_obj)
    except Exception:
        logger.exception("Не удалось сформировать PDF для Request(%d)", request_obj.pk)
        raise HTTPException(500, "Failed to render PDF")

    filename = f"search-{request_obj.pk}.pdf"
    # RFC 5987 + классический filename — так работает и в старых, и в современных браузерах.
    content_disposition = (
        f'attachment; filename="{filename}"; '
        f"filename*=UTF-8''{quote(filename)}"
    )

    headers = {
        "Content-Disposition": content_disposition,
        "Content-Length": str(len(pdf_bytes)),
        "Content-Type": "application/pdf",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    }

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=headers,
    )
