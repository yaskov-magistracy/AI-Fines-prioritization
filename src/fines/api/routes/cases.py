from typing import Annotated

from fastapi import APIRouter, Depends

from fines.api.deps import SessionDep
from fines.repository import CaseRepository
from fines.schemas import CaseFilters, CaseOut, CasePage

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=CasePage)
async def search_cases(
    session: SessionDep,
    filters: Annotated[CaseFilters, Depends()],
) -> CasePage:
    total, rows = await CaseRepository(session).search(filters)
    return CasePage(
        total=total,
        limit=filters.limit,
        offset=filters.offset,
        items=[CaseOut.model_validate(row) for row in rows],
    )
