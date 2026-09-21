import re
from decimal import Decimal

from rapidfuzz import fuzz, process

from fines.extraction import patterns
from fines.extraction.base import ExtractedCase, PdfPayload


class RuleBasedExtractor:
    """Регулярки + справочник марок. Детерминирован, работает без сети."""

    name = "rule_based"

    def extract(self, payload: PdfPayload) -> ExtractedCase:
        text = _normalize(payload.text)
        case = ExtractedCase()
        meta: dict[str, str] = {}

        if m := patterns.DEBTOR_LABEL_RE.search(text):
            case.debtor_name = m.group(1).strip()
            meta["debtor_name"] = "label"

        if m := patterns.CASE_NUMBER_RE.search(text):
            case.case_number = m.group(1)
            meta["case_number"] = "regex"

        case.debt_amount, debt_src = self._debt(text)
        if debt_src:
            meta["debt_amount"] = debt_src

        for m in patterns.VIN_RE.finditer(text):
            if patterns.is_valid_vin(m.group(1)):
                case.vin = m.group(1)
                meta["vin"] = "regex"
                break

        if m := patterns.PLATE_RE.search(text):
            case.plate = m.group(1).upper()
            meta["plate"] = "regex"

        case.make, case.model, make_src = self._make_model(text)
        if make_src:
            meta["make"] = make_src

        if m := patterns.YEAR_LABEL_RE.search(text):
            case.year = int(m.group(1))
            meta["year"] = "label"
        elif m := patterns.YEAR_RE.search(text):
            case.year = int(m.group(1))
            meta["year"] = "regex"

        if m := patterns.MILEAGE_RE.search(text):
            case.mileage_km = patterns.parse_int(m.group(1))
            meta["mileage_km"] = "regex"

        case.fields_meta = dict(meta)
        case.confidence = _confidence(case)
        return case

    def _debt(self, text: str) -> tuple[Decimal | None, str | None]:
        if (m := patterns.DEBT_LABEL_RE.search(text)) and (
            value := patterns.parse_money(m.group(1))
        ):
            return value, "label"
        amounts = [
            v for m in patterns.MONEY_RE.finditer(text) if (v := patterns.parse_money(m.group(1)))
        ]
        if amounts:
            return max(amounts), "max_money"
        return None, None

    def _make_model(self, text: str) -> tuple[str | None, str | None, str | None]:
        if m := patterns.MAKE_MODEL_LABEL_RE.search(text):
            make, model = _split_make_model(m.group(1).strip())
            if make:
                return make, model, "label"

        # Фоллбэк: ищем любую известную марку в тексте
        for token_line in text.splitlines():
            match = process.extractOne(
                token_line, patterns.KNOWN_MAKES, scorer=fuzz.partial_ratio, score_cutoff=92
            )
            if match:
                make = match[0]
                model = _model_after(token_line, make)
                return make, model, "dictionary"
        return None, None, None


def _split_make_model(raw: str) -> tuple[str | None, str | None]:
    parts = raw.split()
    if not parts:
        return None, None
    match = process.extractOne(parts[0], patterns.KNOWN_MAKES, scorer=fuzz.ratio, score_cutoff=80)
    make = match[0] if match else parts[0]
    model = " ".join(parts[1:]) or None
    return make, model


def _model_after(line: str, make: str) -> str | None:
    idx = line.lower().find(make.lower())
    if idx < 0:
        return None
    tail = line[idx + len(make) :].strip(" ,:-—")
    tail = re.split(r"[,;]|\s{2,}", tail)[0].strip()
    return tail[:128] or None


def _normalize(text: str) -> str:
    text = text.replace("­", "").replace("﻿", "")
    return re.sub(r"[ \t]+", " ", text)


def _confidence(case: ExtractedCase) -> float:
    weights = {"vin": 0.3, "make": 0.2, "debt_amount": 0.3, "year": 0.1, "debtor_name": 0.1}
    return round(sum(w for f, w in weights.items() if getattr(case, f) is not None), 2)
