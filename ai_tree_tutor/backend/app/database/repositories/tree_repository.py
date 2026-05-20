"""
Tree Repository — Session/TreeState persistence
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TreeStateModel


class TreeRepository:
    """Repository for tree state persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, session_id: str, tree_type: str) -> Optional[Dict[str, Any]]:
        stmt = (
            select(TreeStateModel)
            .where(
                TreeStateModel.session_id == session_id,
                TreeStateModel.tree_type == tree_type,
            )
            .order_by(TreeStateModel.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return {"tree_data": row.tree_data, "log": row.operation_log, "version": row.version}
        return None

    async def save(self, session_id: str, tree_type: str, tree_data: dict, log: list) -> int:
        stmt = (
            select(func.coalesce(func.max(TreeStateModel.version), 0))
            .where(
                TreeStateModel.session_id == session_id,
                TreeStateModel.tree_type == tree_type,
            )
        )
        result = await self.session.execute(stmt)
        max_version = result.scalar() or 0

        record = TreeStateModel(
            session_id=session_id,
            tree_type=tree_type,
            tree_data=tree_data,
            operation_log=log,
            version=max_version + 1,
        )
        self.session.add(record)
        await self.session.flush()
        return record.version
