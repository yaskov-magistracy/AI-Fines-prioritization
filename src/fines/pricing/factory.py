from fines.config import Settings
from fines.pricing.base import PriceProvider
from fines.pricing.stub import StubPriceProvider


def get_price_provider(settings: Settings) -> PriceProvider:
    if settings.price_provider == "http":
        from fines.pricing.http import HttpPriceProvider

        return HttpPriceProvider(settings.price_api_base_url, settings.price_api_key)
    return StubPriceProvider()
