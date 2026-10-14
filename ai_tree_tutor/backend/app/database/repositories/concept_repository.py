"""
Concept Repository — Concept mastery persistence and analytics
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ConceptMastery, MisconceptionLog


class ConceptRepository:
    """Repository for concept mastery persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_concept_mastery(
        self,
        user_id: str,
        session_id: str,
        concept_id: str,
        performance: float,
        is_correct: bool = True,
    ) -> ConceptMastery:
        stmt = (
            select(ConceptMastery)
            .where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_id == concept_id,
            )
            .order_by(desc(ConceptMastery.last_updated))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.attempts += 1
            if not is_correct:
                existing.mistakes += 1
            # exponential moving average
            alpha = 0.3
            existing.mastery_level = (1 - alpha) * existing.mastery_level + alpha * performance
            existing.last_updated = datetime.now(timezone.utc)
            record = existing
        else:
            record = ConceptMastery(
                user_id=user_id,
                session_id=session_id,
                concept_id=concept_id,
                mastery_level=performance,
                attempts=1,
                mistakes=0 if is_correct else 1,
            )
            self.session.add(record)

        await self.session.flush()
        return record

    async def get_weak_concepts(
        self,
        user_id: str,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(ConceptMastery)
            .where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.mastery_level < threshold,
            )
            .order_by(ConceptMastery.mastery_level.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "concept_id": r.concept_id,
                "mastery_level": r.mastery_level,
                "attempts": r.attempts,
                "mistakes": r.mistakes,
            }
            for r in rows
        ]

    async def get_concept_graph_for_user(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(ConceptMastery)
            .where(ConceptMastery.user_id == user_id)
            .order_by(ConceptMastery.concept_id)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "concept_id": r.concept_id,
                "mastery_level": r.mastery_level,
                "attempts": r.attempts,
                "mistakes": r.mistakes,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            }
            for r in rows
        ]

    async def track_misconception(
        self,
        user_id: str,
        operation_id: str,
        misconception_type: str,
        explanation: Optional[str] = None,
        fixed: bool = False,
    ) -> MisconceptionLog:
        record = MisconceptionLog(
            user_id=user_id,
            operation_id=operation_id,
            misconception_type=misconception_type,
            explanation=explanation,
            fixed=fixed,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_misconception_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(MisconceptionLog)
            .where(MisconceptionLog.user_id == user_id)
            .order_by(desc(MisconceptionLog.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "misconception_type": r.misconception_type,
                "explanation": r.explanation,
                "fixed": r.fixed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
