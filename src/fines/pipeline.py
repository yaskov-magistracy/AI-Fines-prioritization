import uuid
from decimal import Decimal
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from fines.config import Settings
from fines.extraction import get_extractor
from fines.extraction.pdf import file_hash, read_pdf
from fines.models import DebtCase, Document, DocumentStatus, Photo
from fines.pricing import VehicleQuery, get_price_provider
from fines.repository import CaseRepository
from fines.storage import LocalStorage

log = structlog.get_logger(__name__)


class IngestPipeline:
    """PDF -> текст+фото -> поля -> рыночная цена -> запись в БД."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._storage = LocalStorage(settings.storage_dir)
        self._extractor = get_extractor(settings)
        self._pricing = get_price_provider(settings)
        self._repo = CaseRepository(session)

    async def ingest(self, filename: str, data: bytes) -> Document:
        digest = file_hash(data)
        if existing := await self._repo.get_by_hash(digest):
            log.info("документ уже загружен", document_id=str(existing.id))
            return existing

        document = Document(
            id=uuid.uuid4(),
            filename=filename,
            content_hash=digest,
            storage_path=f"pdf/{digest}.pdf",
        )
        self._storage.save(document.storage_path, data)
        self._session.add(document)
        await self._session.flush()

        try:
            await self._process(document)
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error = f"{type(exc).__name__}: {exc}"
            log.warning("разбор не удался", document_id=str(document.id), error=document.error)

        return document

    async def _process(self, document: Document) -> None:
        path: Path = self._storage.path(document.storage_path)
        payload = read_pdf(path)
        document.page_count = len(payload.pages)
        document.raw_text = payload.text[:1_000_000]

        photos: list[Photo] = []
        for idx, (page_no, image_bytes) in enumerate(payload.images):
            rel = f"photos/{document.content_hash}/{page_no}_{idx}.bin"
            self._storage.save(rel, image_bytes)
            photos.append(Photo(document_id=document.id, page=page_no, storage_path=rel))
        self._session.add_all(photos)
        # Проставляем связи вручную: ленивая подгрузка в async-сессии падает
        attributes.set_committed_value(document, "photos", photos)

        extracted = self._extractor.extract(payload)
        case = DebtCase(
            document_id=document.id,
            debtor_name=extracted.debtor_name,
            case_number=extracted.case_number,
            debt_amount=extracted.debt_amount,
            debt_currency=extracted.debt_currency,
            make=extracted.make,
            model=extracted.model,
            year=extracted.year,
            vin=extracted.vin,
            plate=extracted.plate,
            mileage_km=extracted.mileage_km,
            extractor=self._extractor.name,
            confidence=extracted.confidence,
            fields_meta=extracted.fields_meta,
        )
        self._session.add(case)
        attributes.set_committed_value(document, "case", case)
        document.status = DocumentStatus.PARSED

        if await self._enrich_price(case):
            document.status = DocumentStatus.PRICED

    async def _enrich_price(self, case: DebtCase) -> bool:
        if not case.make:
            return False
        quote = await self._pricing.quote(
            VehicleQuery(
                make=case.make,
                model=case.model,
                year=case.year,
                mileage_km=case.mileage_km,
                vin=case.vin,
            )
        )
        if quote is None:
            return False

        case.market_value = quote.value
        case.market_value_source = quote.source
        case.market_value_at = quote.fetched_at
        if case.debt_amount is not None and quote.value > 0:
            case.debt_to_value_ratio = float(
                (Decimal(case.debt_amount) / quote.value).quantize(Decimal("0.0001"))
            )
        return True
