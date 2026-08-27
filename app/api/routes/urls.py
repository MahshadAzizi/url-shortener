from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_url_service
from app.schemas.url import ShortenRequest, ShortenResponse, StatsResponse
from app.services.url_service import URLService

router = APIRouter()


@router.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def shorten_url(
        payload: ShortenRequest,
        request: Request,
        service: Annotated[
            URLService,
            Depends(get_url_service),
        ],
) -> ShortenResponse:
    url = await service.create_short_url(
        str(payload.original_url),
    )

    short_url = str(
        request.url_for(
            "redirect_url",
            short_code=url.short_code,
        )
    )

    return ShortenResponse(
        short_code=url.short_code,
        short_url=short_url,
        original_url=url.original_url,
        created_at=url.created_at,
    )


@router.get(
    "/stats/{short_code}",
    response_model=StatsResponse,
)
async def get_stats(
        short_code: str,
        service: Annotated[
            URLService,
            Depends(get_url_service),
        ],
) -> StatsResponse:
    url = await service.get_url_by_short_code(short_code)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )

    visits = await service.get_visit_count(url.id)

    return StatsResponse(
        short_code=url.short_code,
        visits=visits,
    )
