"""
Quiz Repository — Quiz result persistence and analytics
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import QuizResult


class QuizRepository:
    """Repository for quiz result persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_quiz_result(
        self,
        user_id: str,
        session_id: str,
        quiz_id: str,
        score: Optional[int] = None,
        total: Optional[int] = None,
        answers_json: Optional[dict] = None,
    ) -> QuizResult:
        record = QuizResult(
            user_id=user_id,
            session_id=session_id,
            quiz_id=quiz_id,
            score=score,
            total=total,
            answers_json=answers_json or {},
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_user_quiz_history(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(QuizResult)
            .where(QuizResult.user_id == user_id)
            .order_by(desc(QuizResult.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "quiz_id": r.quiz_id,
                "score": r.score,
                "total": r.total,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in rows
        ]

    async def get_quiz_analytics(self, user_id: str) -> Dict[str, Any]:
        total_stmt = (
            select(func.count(QuizResult.id))
            .where(QuizResult.user_id == user_id)
        )
        total_result = await self.session.execute(total_stmt)
        total_quizzes = total_result.scalar() or 0

        score_stmt = (
            select(
                func.coalesce(func.sum(QuizResult.score), 0),
                func.coalesce(func.sum(QuizResult.total), 0),
            )
            .where(QuizResult.user_id == user_id)
        )
        score_result = await self.session.execute(score_stmt)
        row = score_result.one()
        total_score = row[0] or 0
        total_possible = row[1] or 0

        avg_pct = (total_score / total_possible * 100) if total_possible > 0 else 0.0

        recent_stmt = (
            select(QuizResult)
            .where(QuizResult.user_id == user_id)
            .order_by(desc(QuizResult.timestamp))
            .limit(5)
        )
        recent_result = await self.session.execute(recent_stmt)
        recent = recent_result.scalars().all()

        return {
            "total_quizzes": total_quizzes,
            "total_score": total_score,
            "total_possible": total_possible,
            "average_percentage": round(avg_pct, 1),
            "recent_results": [
                {
                    "quiz_id": r.quiz_id,
                    "score": r.score,
                    "total": r.total,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
                for r in recent
            ],
        }
