from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.visit import Visit


class URL(Base):
    __tablename__ = "urls"

    __table_args__ = (
        UniqueConstraint(
            "short_code",
            name="uq_urls_short_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    original_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    short_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        unique=True,
    )

    visit_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    visits: Mapped[list["Visit"]] = relationship(
        back_populates="url",
        cascade="all, delete-orphan",
    )
