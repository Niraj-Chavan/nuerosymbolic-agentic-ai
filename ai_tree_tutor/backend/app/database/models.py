"""
SQLAlchemy ORM Models
======================
Declarative models for PostgreSQL persistence.
All tables use UUID primary keys and UTC timestamps.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# =========================================================================
# 1. user_sessions
# =========================================================================

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata_", JSON, default=dict)

    # relationships
    operation_history: Mapped[List["OperationHistory"]] = relationship(
        back_populates="session",
        foreign_keys="OperationHistory.session_id",
        cascade="all, delete-orphan",
    )
    quiz_results: Mapped[List["QuizResult"]] = relationship(
        back_populates="session",
        foreign_keys="QuizResult.session_id",
        cascade="all, delete-orphan",
    )
    concept_mastery: Mapped[List["ConceptMastery"]] = relationship(
        back_populates="session",
        foreign_keys="ConceptMastery.session_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UserSession id={self.id} user_id={self.user_id}>"


# =========================================================================
# 2. concept_mastery
# =========================================================================

class ConceptMastery(Base):
    __tablename__ = "concept_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_sessions.id"), nullable=False
    )
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mistakes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    session: Mapped["UserSession"] = relationship(
        back_populates="concept_mastery",
        foreign_keys=[session_id],
    )

    def __repr__(self) -> str:
        return f"<ConceptMastery user={self.user_id} concept={self.concept_id} mastery={self.mastery_level}>"


# =========================================================================
# 3. quiz_results
# =========================================================================

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_sessions.id"), nullable=False
    )
    quiz_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    answers_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    session: Mapped["UserSession"] = relationship(
        back_populates="quiz_results",
        foreign_keys=[session_id],
    )

    def __repr__(self) -> str:
        return f"<QuizResult id={self.id} user={self.user_id} score={self.score}/{self.total}>"


# =========================================================================
# 4. operation_history
# =========================================================================

class OperationHistory(Base):
    __tablename__ = "operation_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_sessions.id"), nullable=False
    )
    tree_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    result: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    session: Mapped["UserSession"] = relationship(
        back_populates="operation_history",
        foreign_keys=[session_id],
    )
    misconception: Mapped[Optional["MisconceptionLog"]] = relationship(
        back_populates="operation",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<OperationHistory id={self.id} op={self.operation} on={self.tree_type}>"


# =========================================================================
# 5. misconception_log
# =========================================================================

class MisconceptionLog(Base):
    __tablename__ = "misconception_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operation_history.id"), nullable=False, unique=True
    )
    misconception_type: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    operation: Mapped["OperationHistory"] = relationship(
        back_populates="misconception",
        foreign_keys=[operation_id],
    )

    def __repr__(self) -> str:
        return f"<MisconceptionLog id={self.id} type={self.misconception_type} fixed={self.fixed}>"


# =========================================================================
# Legacy: TreeStateModel (kept for tree_repository compatibility)
# =========================================================================

class TreeStateModel(Base):
    __tablename__ = "tree_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    tree_type: Mapped[str] = mapped_column(String, nullable=False)
    tree_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    operation_log: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )
