from decimal import Decimal

from fines.extraction.base import ExtractedCase, PdfPayload
from fines.extraction.rule_based import RuleBasedExtractor

TEXT = """Постановление о взыскании
Дело № 12345/2024
Должник: Иванов Иван Иванович
Сумма долга: 450 000 руб.
Марка, модель: Toyota Camry
VIN: JTDBE32K123456789
Год выпуска: 2015
Пробег: 180000 км
Гос. номер: А123ВС777
"""


def _extract(text: str = TEXT) -> ExtractedCase:
    return RuleBasedExtractor().extract(PdfPayload(filename="t.pdf", pages=[text]))


def test_extracts_core_fields() -> None:
    case = _extract()
    assert case.debtor_name == "Иванов Иван Иванович"
    assert case.case_number == "12345/2024"
    assert case.debt_amount == Decimal("450000")
    assert case.make == "Toyota"
    assert case.model == "Camry"
    assert case.vin == "JTDBE32K123456789"
    assert case.year == 2015
    assert case.mileage_km == 180000
    assert case.plate == "А123ВС777"
    assert case.confidence >= 0.9


def test_empty_text_yields_empty_case() -> None:
    case = _extract("")
    assert case.vin is None
    assert case.debt_amount is None
    assert case.confidence == 0.0


def test_missing_vin_does_not_break_extraction() -> None:
    case = _extract(TEXT.replace("VIN: JTDBE32K123456789\n", ""))
    assert case.vin is None
    assert case.make == "Toyota"
    assert case.debt_amount == Decimal("450000")
