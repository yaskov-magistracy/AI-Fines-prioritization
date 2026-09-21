import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from fines.models import DocumentStatus


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    debtor_name: str | None
    case_number: str | None
    debt_amount: Decimal | None
    debt_currency: str
    make: str | None
    model: str | None
    year: int | None
    vin: str | None
    plate: str | None
    mileage_km: int | None
    market_value: Decimal | None
    market_value_source: str | None
    market_value_at: datetime | None
    debt_to_value_ratio: float | None
    extractor: str | None
    confidence: float | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: DocumentStatus
    page_count: int
    error: str | None
    created_at: datetime
    case: CaseOut | None = None


class SortField(StrEnum):
    DEBT = "debt_amount"
    VALUE = "market_value"
    RATIO = "debt_to_value_ratio"
    YEAR = "year"
    CREATED = "created_at"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class CaseFilters(BaseModel):
    """Фильтры поиска по карточкам."""

    q: str | None = Field(default=None, description="Поиск по ФИО, VIN, номеру дела, марке")
    make: str | None = None
    model: str | None = None
    vin: str | None = None
    year_min: int | None = Field(default=None, ge=1980)
    year_max: int | None = Field(default=None, le=2100)
    debt_min: Decimal | None = Field(default=None, ge=0)
    debt_max: Decimal | None = Field(default=None, ge=0)
    value_min: Decimal | None = Field(default=None, ge=0)
    value_max: Decimal | None = Field(default=None, ge=0)
    ratio_max: float | None = Field(default=None, gt=0, description="долг / стоимость")
    status: DocumentStatus | None = None

    sort_by: SortField = SortField.RATIO
    order: SortOrder = SortOrder.ASC
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class CasePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CaseOut]


class HealthOut(BaseModel):
    status: str
    version: str
    database: str
