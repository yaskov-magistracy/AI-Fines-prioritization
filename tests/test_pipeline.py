from sqlalchemy.ext.asyncio import AsyncSession

from fines.config import Settings
from fines.models import DocumentStatus
from fines.pipeline import IngestPipeline
from tests.factories import make_pdf


async def test_ingest_parses_and_prices(session: AsyncSession, settings: Settings) -> None:
    document = await IngestPipeline(session, settings).ingest("case.pdf", make_pdf())
    await session.flush()

    assert document.status is DocumentStatus.PRICED
    assert document.page_count == 1
    case = document.case
    assert case is not None
    assert case.vin == "JTDBE32K123456789"
    assert case.market_value is not None
    assert case.debt_to_value_ratio is not None


async def test_ingest_is_idempotent_by_hash(session: AsyncSession, settings: Settings) -> None:
    pipeline = IngestPipeline(session, settings)
    data = make_pdf()
    first = await pipeline.ingest("a.pdf", data)
    await session.flush()
    second = await pipeline.ingest("b.pdf", data)

    assert first.id == second.id


async def test_unparsable_pdf_is_marked_failed(session: AsyncSession, settings: Settings) -> None:
    document = await IngestPipeline(session, settings).ingest("broken.pdf", b"not a pdf")
    assert document.status is DocumentStatus.FAILED
    assert document.error
