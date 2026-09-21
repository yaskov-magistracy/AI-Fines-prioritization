import hashlib
from datetime import UTC, datetime
from decimal import Decimal

from fines.pricing.base import PriceQuote, VehicleQuery

BASE_PRICES: dict[str, int] = {
    "LADA": 700_000,
    "ВАЗ": 350_000,
    "Toyota": 1_900_000,
    "Kia": 1_500_000,
    "Hyundai": 1_450_000,
    "BMW": 2_800_000,
    "Mercedes-Benz": 3_000_000,
    "Audi": 2_400_000,
    "Volkswagen": 1_600_000,
    "Renault": 1_100_000,
}
DEFAULT_BASE = 1_000_000


class StubPriceProvider:
    """Детерминированная оценка для локальной разработки и тестов.

    Никакой сети: цена = база по марке, скорректированная на возраст и пробег.
    """

    name = "stub"

    async def quote(self, query: VehicleQuery) -> PriceQuote | None:
        if not query.make:
            return None

        base = Decimal(BASE_PRICES.get(query.make, DEFAULT_BASE))
        now = datetime.now(UTC)

        if query.year:
            age = max(0, now.year - query.year)
            base *= Decimal("0.92") ** age

        if query.mileage_km:
            penalty = Decimal(min(query.mileage_km, 400_000)) / Decimal(1_000_000)
            base *= Decimal(1) - penalty

        # Детерминированный разброс ±5% по ключу автомобиля
        key = f"{query.make}|{query.model}|{query.year}|{query.vin}"
        jitter = int(hashlib.sha256(key.encode()).hexdigest()[:4], 16) % 1001  # 0..1000
        base *= Decimal(950 + jitter // 10) / Decimal(1000)

        value = max(Decimal("30000"), base).quantize(Decimal("1.00"))
        return PriceQuote(value=value, currency="RUB", source=self.name, fetched_at=now)
