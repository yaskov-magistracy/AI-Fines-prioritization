from decimal import Decimal

from fines.pricing.base import VehicleQuery
from fines.pricing.stub import StubPriceProvider


async def test_stub_is_deterministic() -> None:
    provider = StubPriceProvider()
    query = VehicleQuery(make="Toyota", model="Camry", year=2015, mileage_km=180_000)
    first = await provider.quote(query)
    second = await provider.quote(query)
    assert first is not None and second is not None
    assert first.value == second.value


async def test_older_car_is_cheaper() -> None:
    provider = StubPriceProvider()
    new = await provider.quote(VehicleQuery(make="Toyota", model="Camry", year=2023))
    old = await provider.quote(VehicleQuery(make="Toyota", model="Camry", year=2005))
    assert new is not None and old is not None
    assert old.value < new.value


async def test_no_make_no_quote() -> None:
    assert await StubPriceProvider().quote(VehicleQuery(make="")) is None


async def test_floor_price() -> None:
    quote = await StubPriceProvider().quote(VehicleQuery(make="ВАЗ", year=1990, mileage_km=400_000))
    assert quote is not None
    assert quote.value >= Decimal("30000")
