from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_url_service
from app.services.url_service import URLService

router = APIRouter()


@router.get(
    "/{short_code}",
    name="redirect_url",
)
async def redirect_url(
        short_code: str,
        request: Request,
        background_tasks: BackgroundTasks,
        service: Annotated[
            URLService,
            Depends(get_url_service),
        ],
) -> RedirectResponse:
    url = await service.get_url_by_short_code(short_code)

    if url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    ip_address = request.client.host if request.client else None

    background_tasks.add_task(
        service.record_visit,
        url.id,
        ip_address,
    )

    return RedirectResponse(
        url=url.original_url,
        status_code=307,
    )
