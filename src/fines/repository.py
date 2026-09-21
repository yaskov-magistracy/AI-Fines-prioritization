import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fines.models import DebtCase, Document
from fines.schemas import CaseFilters, SortOrder


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.case), selectinload(Document.photos))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_hash(self, content_hash: str) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.content_hash == content_hash)
            .options(selectinload(Document.case))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def search(self, filters: CaseFilters) -> tuple[int, Sequence[DebtCase]]:
        stmt = select(DebtCase).join(Document, Document.id == DebtCase.document_id)
        stmt = self._apply_filters(stmt, filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        column = getattr(DebtCase, filters.sort_by.value, None)
        if column is None:
            column = Document.created_at
        ordering = column.asc() if filters.order is SortOrder.ASC else column.desc()

        stmt = stmt.order_by(ordering.nullslast()).limit(filters.limit).offset(filters.offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        return total, rows

    def _apply_filters(
        self, stmt: Select[tuple[DebtCase]], f: CaseFilters
    ) -> Select[tuple[DebtCase]]:
        if f.q:
            pattern = f"%{f.q.strip()}%"
            stmt = stmt.where(
                or_(
                    DebtCase.debtor_name.ilike(pattern),
                    DebtCase.vin.ilike(pattern),
                    DebtCase.case_number.ilike(pattern),
                    DebtCase.make.ilike(pattern),
                    DebtCase.model.ilike(pattern),
                    DebtCase.plate.ilike(pattern),
                )
            )
        if f.make:
            stmt = stmt.where(DebtCase.make.ilike(f.make))
        if f.model:
            stmt = stmt.where(DebtCase.model.ilike(f"%{f.model}%"))
        if f.vin:
            stmt = stmt.where(DebtCase.vin == f.vin.upper())
        if f.year_min is not None:
            stmt = stmt.where(DebtCase.year >= f.year_min)
        if f.year_max is not None:
            stmt = stmt.where(DebtCase.year <= f.year_max)
        if f.debt_min is not None:
            stmt = stmt.where(DebtCase.debt_amount >= f.debt_min)
        if f.debt_max is not None:
            stmt = stmt.where(DebtCase.debt_amount <= f.debt_max)
        if f.value_min is not None:
            stmt = stmt.where(DebtCase.market_value >= f.value_min)
        if f.value_max is not None:
            stmt = stmt.where(DebtCase.market_value <= f.value_max)
        if f.ratio_max is not None:
            stmt = stmt.where(DebtCase.debt_to_value_ratio <= f.ratio_max)
        if f.status is not None:
            stmt = stmt.where(Document.status == f.status)
        return stmt
