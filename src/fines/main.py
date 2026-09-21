from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fines import __version__
from fines.api.routes import cases, documents, health
from fines.config import get_settings
from fines.db import dispose_engine, init_engine
from fines.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_engine(settings)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Fines Prioritization",
        version=__version__,
        description="Парсинг исполнительных производств из PDF и приоритизация по стоимости ТС",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(cases.router)
    return app


app = create_app()
