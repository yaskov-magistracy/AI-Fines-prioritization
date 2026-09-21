from decimal import Decimal

import pytest

from fines.extraction import patterns


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("450 000", Decimal("450000")),
        ("1 234 567,89", Decimal("1234567.89")),
        ("1.234.567,00", Decimal("1234567.00")),
        ("250000.50", Decimal("250000.50")),
        ("0", None),
        ("abc", None),
    ],
)
def test_parse_money(raw: str, expected: Decimal | None) -> None:
    assert patterns.parse_money(raw) == expected


@pytest.mark.parametrize(
    ("vin", "valid"),
    [
        ("JTDBE32K123456789", True),
        ("12345678901234567", False),  # только цифры — это не VIN
        ("ABCDEFGHJKLMNPRST", False),  # только буквы
        ("JTDBE32K12345678I", False),  # запрещённая буква I
    ],
)
def test_is_valid_vin(vin: str, valid: bool) -> None:
    assert patterns.is_valid_vin(vin) is valid


def test_plate_regex() -> None:
    match = patterns.PLATE_RE.search("гос. номер А123ВС777")
    assert match is not None
    assert match.group(1).upper() == "А123ВС777"


def test_debt_label_wins_over_other_amounts() -> None:
    text = "Госпошлина 5 000 руб. Сумма долга: 450 000 руб."
    match = patterns.DEBT_LABEL_RE.search(text)
    assert match is not None
    assert patterns.parse_money(match.group(1)) == Decimal("450000")
