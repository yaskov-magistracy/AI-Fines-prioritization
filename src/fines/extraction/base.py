from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol


@dataclass(slots=True)
class PdfPayload:
    """Сырое содержимое PDF: текст постранично и байты картинок."""

    filename: str
    pages: list[str]
    images: list[tuple[int, bytes]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.pages)


@dataclass(slots=True)
class ExtractedCase:
    """Результат разбора одного документа. Все поля опциональны — PDF бывают кривые."""

    debtor_name: str | None = None
    case_number: str | None = None
    debt_amount: Decimal | None = None
    debt_currency: str = "RUB"

    make: str | None = None
    model: str | None = None
    year: int | None = None
    vin: str | None = None
    plate: str | None = None
    mileage_km: int | None = None

    confidence: float = 0.0
    fields_meta: dict[str, Any] = field(default_factory=dict)


class Extractor(Protocol):
    """Контракт бэкенда извлечения. Реализации: rule_based, llm."""

    name: str

    def extract(self, payload: PdfPayload) -> ExtractedCase: ...
