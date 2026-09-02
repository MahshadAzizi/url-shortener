from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_url_service, get_visit_service
from app.schemas.url import ShortenRequest, ShortenResponse, StatsResponse
from app.services.url_service import URLService
from app.services.visit_service import VisitService

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
        url_service: Annotated[
            URLService,
            Depends(get_url_service),
        ]
) -> StatsResponse:
    visit_count = await url_service.get_url_with_stats(
        short_code,
    )

    if visit_count is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found",
        )

    return StatsResponse(
        short_code=short_code,
        visits=visit_count,
    )
