from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class ShortenRequest(BaseModel):
    original_url: AnyHttpUrl = Field(max_length=2048)


class ShortenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: AnyHttpUrl
    original_url: AnyHttpUrl
    created_at: datetime


class StatsResponse(BaseModel):
    short_code: str
    visits: int
