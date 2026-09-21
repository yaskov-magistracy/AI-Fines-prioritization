from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(slots=True, frozen=True)
class VehicleQuery:
    make: str
    model: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    vin: str | None = None


@dataclass(slots=True, frozen=True)
class PriceQuote:
    value: Decimal
    currency: str
    source: str
    fetched_at: datetime
    sample_size: int | None = None


class PriceProvider(Protocol):
    """Контракт оценки рыночной стоимости. Реализации: stub, http."""

    name: str

    async def quote(self, query: VehicleQuery) -> PriceQuote | None: ...
