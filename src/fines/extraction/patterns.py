import re
from decimal import Decimal, InvalidOperation

# VIN: 17 символов, без I, O, Q
VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")

# Российский номер: А123ВС777
PLATE_RE = re.compile(r"\b([АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3})\b", re.IGNORECASE)

YEAR_RE = re.compile(r"\b(19[8-9]\d|20[0-4]\d)\b")

# Год выпуска по метке надёжнее: в тексте полно других четырёхзначных чисел
YEAR_LABEL_RE = re.compile(
    r"(?:год\s+выпуска|г\.?\s*в\.|выпуска)\D{0,10}?(19[8-9]\d|20[0-4]\d)\b",
    re.IGNORECASE,
)

CASE_NUMBER_RE = re.compile(r"\b(\d{1,7}/\d{2,4}(?:/\d{1,6}-\w{2,4})?)\b")

MILEAGE_RE = re.compile(r"(\d[\d\s.,]{2,9})\s*(?:км|km)\b", re.IGNORECASE)

# "1 234 567,89 руб." / "1234567.89 RUB" / "сумма долга: 250000"
MONEY_RE = re.compile(
    r"(\d[\d\s ]{0,15}(?:[.,]\d{1,2})?)\s*(?:руб|рублей|р\.|₽|RUB)",
    re.IGNORECASE,
)

DEBT_LABEL_RE = re.compile(
    r"(?:сумма\s+долга|задолженност[ьи]|остаток\s+долга|взыскать|долг)\D{0,40}?"
    r"(\d[\d\s ]{0,15}(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)

DEBTOR_LABEL_RE = re.compile(
    r"(?:[Дд]олжник|[Оо]тветчик|ФИО\s+должника)\s*[:\-—]?\s*"
    r"([А-ЯЁ][а-яё\-]+\s+[А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+)?)",
)

MAKE_MODEL_LABEL_RE = re.compile(
    r"(?:марка(?:\s*,?\s*модель)?|транспортн\w+\s+средств\w+|автомобиль|ТС)\s*[:\-—]?\s*"
    r"([A-Za-zА-Яа-яЁё][\w\-.]*(?:[ \t]+[\w\-./]+){0,3})",
    re.IGNORECASE,
)

# Минимальный справочник марок. Пополняется по мере встреч в реальных PDF.
KNOWN_MAKES: tuple[str, ...] = (
    "LADA",
    "ВАЗ",
    "Toyota",
    "Kia",
    "Hyundai",
    "Nissan",
    "Volkswagen",
    "Skoda",
    "Renault",
    "Ford",
    "Chevrolet",
    "Mazda",
    "Mitsubishi",
    "BMW",
    "Mercedes-Benz",
    "Audi",
    "Opel",
    "Honda",
    "Subaru",
    "Suzuki",
    "Lexus",
    "Volvo",
    "Peugeot",
    "Citroen",
    "Chery",
    "Haval",
    "Geely",
    "Changan",
    "Exeed",
    "УАЗ",
    "ГАЗ",
    "Datsun",
    "Daewoo",
    "SsangYong",
    "Infiniti",
    "Land Rover",
    "Jeep",
    "Porsche",
)


def parse_money(raw: str) -> Decimal | None:
    """'1 234 567,89' -> Decimal('1234567.89'). Возвращает None на мусоре."""
    cleaned = raw.replace(" ", "").replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "") if cleaned.rfind(",") > cleaned.rfind(".") else cleaned
    cleaned = cleaned.replace(",", ".")
    if cleaned.count(".") > 1:
        head, _, tail = cleaned.rpartition(".")
        cleaned = head.replace(".", "") + "." + tail
    try:
        value = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    return value if value > 0 else None


def parse_int(raw: str) -> int | None:
    cleaned = re.sub(r"[^\d]", "", raw)
    return int(cleaned) if cleaned else None


def is_valid_vin(vin: str) -> bool:
    """VIN должен содержать и буквы, и цифры — иначе это номер документа."""
    return (
        bool(VIN_RE.fullmatch(vin))
        and any(c.isalpha() for c in vin)
        and any(c.isdigit() for c in vin)
    )
