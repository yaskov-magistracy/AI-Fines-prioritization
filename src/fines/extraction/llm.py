import json

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from fines.extraction.base import ExtractedCase, PdfPayload
from fines.extraction.patterns import parse_money

PROMPT = """Ты извлекаешь данные из документа об исполнительном производстве.
Верни СТРОГО JSON без пояснений со схемой:
{"debtor_name": str|null, "case_number": str|null, "debt_amount": str|null,
 "make": str|null, "model": str|null, "year": int|null, "vin": str|null,
 "plate": str|null, "mileage_km": int|null}
Текст документа:
---
{text}
---"""


class LLMExtractor:
    """Извлечение через LLM с structured output.

    Заглушка: нужен эндпоинт, совместимый с OpenAI chat/completions.
    Настраивается через LLM_BASE_URL / LLM_API_KEY / LLM_MODEL.
    """

    name = "llm"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0) -> None:
        if not (base_url and api_key and model):
            raise ValueError("LLM-бэкенд требует LLM_BASE_URL, LLM_API_KEY и LLM_MODEL")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def extract(self, payload: PdfPayload) -> ExtractedCase:
        raw = self._call(payload.text[:30_000])
        return self._to_case(raw)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _call(self, text: str) -> dict[str, object]:
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": PROMPT.replace("{text}", text)}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed: dict[str, object] = json.loads(content)
        return parsed

    def _to_case(self, raw: dict[str, object]) -> ExtractedCase:
        def s(key: str) -> str | None:
            value = raw.get(key)
            return str(value).strip() or None if value else None

        def i(key: str) -> int | None:
            value = raw.get(key)
            if not isinstance(value, int | float | str):
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        debt_raw = s("debt_amount")
        return ExtractedCase(
            debtor_name=s("debtor_name"),
            case_number=s("case_number"),
            debt_amount=parse_money(debt_raw) if debt_raw else None,
            make=s("make"),
            model=s("model"),
            year=i("year"),
            vin=s("vin"),
            plate=s("plate"),
            mileage_km=i("mileage_km"),
            confidence=0.8,
            fields_meta={"source": "llm"},
        )
