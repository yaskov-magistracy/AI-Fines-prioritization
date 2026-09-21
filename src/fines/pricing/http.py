from datetime import UTC, datetime
from decimal import Decimal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from fines.pricing.base import PriceQuote, VehicleQuery


class HttpPriceProvider:
    """Оценка через внешний прайс-API.

    Заглушка под конкретного поставщика: ожидает JSON {"price": ..., "count": ...}.
    Эндпоинт и ключ берутся из PRICE_API_BASE_URL / PRICE_API_KEY.
    """

    name = "http"

    def __init__(self, base_url: str, api_key: str, timeout: float = 15.0) -> None:
        if not base_url:
            raise ValueError("HTTP-провайдер цен требует PRICE_API_BASE_URL")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def quote(self, query: VehicleQuery) -> PriceQuote | None:
        params = {
            k: v
            for k, v in {
                "make": query.make,
                "model": query.model,
                "year": query.year,
                "mileage": query.mileage_km,
            }.items()
            if v is not None
        }
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/price", params=params, headers=headers)
            if response.status_code == httpx.codes.NOT_FOUND:
                return None
            response.raise_for_status()
            body = response.json()

        price = body.get("price")
        if price is None:
            return None
        return PriceQuote(
            value=Decimal(str(price)),
            currency=body.get("currency", "RUB"),
            source=self.name,
            fetched_at=datetime.now(UTC),
            sample_size=body.get("count"),
        )
