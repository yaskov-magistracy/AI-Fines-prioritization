from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fines import db as db_module
from fines.config import Settings, get_settings
from fines.main import create_app
from fines.models import Base


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="ci",
        database_url="sqlite+aiosqlite:///:memory:",
        storage_dir=tmp_path / "storage",
        extractor_backend="rule_based",
        price_provider="stub",
    )


@pytest_asyncio.fixture
async def sessionmaker(settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as s:
        yield s


@pytest.fixture
def app_client_factory(
    settings: Settings, sessionmaker: async_sessionmaker[AsyncSession]
) -> Iterator[AsyncClient]:
    """Клиент FastAPI поверх in-memory БД, без реального lifespan."""
    db_module._sessionmaker = sessionmaker
    app = create_app()
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_settings] = lambda: settings
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()
    db_module._sessionmaker = None


@pytest_asyncio.fixture
async def client(app_client_factory: AsyncClient) -> AsyncIterator[AsyncClient]:
    async with app_client_factory as c:
        yield c


from contextlib import asynccontextmanager  # noqa: E402


@asynccontextmanager
async def _noop_lifespan(app: object) -> AsyncIterator[None]:
    yield
