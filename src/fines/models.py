import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[object, object]] = {dict[str, Any]: JSON}


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    PRICED = "priced"
    FAILED = "failed"


class Document(Base):
    """Загруженный PDF: исходник + статус конвейера."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    storage_path: Mapped[str] = mapped_column(String(1024))
    page_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[DocumentStatus] = mapped_column(String(16), default=DocumentStatus.UPLOADED)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    raw_text: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    case: Mapped["DebtCase | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DebtCase(Base):
    """Извлечённая из PDF карточка: должник, долг, автомобиль, оценка."""

    __tablename__ = "debt_cases"
    __table_args__ = (
        Index("ix_debt_cases_make_model", "make", "model"),
        Index("ix_debt_cases_ratio", "debt_to_value_ratio"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), unique=True, index=True
    )

    debtor_name: Mapped[str | None] = mapped_column(String(512), default=None)
    case_number: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    debt_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=None, index=True)
    debt_currency: Mapped[str] = mapped_column(String(3), default="RUB")

    make: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    year: Mapped[int | None] = mapped_column(default=None, index=True)
    vin: Mapped[str | None] = mapped_column(String(17), default=None, index=True)
    plate: Mapped[str | None] = mapped_column(String(16), default=None)
    mileage_km: Mapped[int | None] = mapped_column(default=None)

    market_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=None, index=True)
    market_value_source: Mapped[str | None] = mapped_column(String(64), default=None)
    market_value_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    debt_to_value_ratio: Mapped[float | None] = mapped_column(Float, default=None)

    extractor: Mapped[str | None] = mapped_column(String(32), default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    fields_meta: Mapped[dict[str, Any]] = mapped_column(default=dict)

    document: Mapped[Document] = relationship(back_populates="case")


class Photo(Base):
    """Изображение, вытащенное со страницы PDF."""

    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int] = mapped_column(default=0)
    storage_path: Mapped[str] = mapped_column(String(1024))
    width: Mapped[int | None] = mapped_column(default=None)
    height: Mapped[int | None] = mapped_column(default=None)

    document: Mapped[Document] = relationship(back_populates="photos")
