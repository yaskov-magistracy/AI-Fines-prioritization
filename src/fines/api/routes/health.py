from fastapi import APIRouter
from sqlalchemy import text

from fines import __version__
from fines.api.deps import SessionDep
from fines.schemas import HealthOut

router = APIRouter(tags=["service"])


@router.get("/health", response_model=HealthOut)
async def health(session: SessionDep) -> HealthOut:
    try:
        await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:
        database = f"error: {type(exc).__name__}"
    return HealthOut(status="ok", version=__version__, database=database)
