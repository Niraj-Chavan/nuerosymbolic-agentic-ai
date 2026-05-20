"""
initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-20 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_sessions
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "session_start",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("session_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_", sa.JSON(), nullable=True),
    )

    # concept_mastery
    op.create_table(
        "concept_mastery",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("concept_id", sa.String(255), nullable=False, index=True),
        sa.Column("mastery_level", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mistakes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["user_sessions.id"],
            name="fk_concept_mastery_session",
        ),
    )
    op.create_index(
        "ix_concept_mastery_user_concept",
        "concept_mastery",
        ["user_id", "concept_id"],
        unique=False,
    )

    # quiz_results
    op.create_table(
        "quiz_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("quiz_id", sa.String(255), nullable=False, index=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("answers_json", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["user_sessions.id"],
            name="fk_quiz_results_session",
        ),
    )

    # operation_history
    op.create_table(
        "operation_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("tree_type", sa.String(50), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["user_sessions.id"],
            name="fk_operation_history_session",
        ),
    )

    # misconception_log
    op.create_table(
        "misconception_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("operation_id", sa.String(36), nullable=False, unique=True),
        sa.Column("misconception_type", sa.String(255), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("fixed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["operation_history.id"],
            name="fk_misconception_log_operation",
        ),
    )

    # tree_states (legacy)
    op.create_table(
        "tree_states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("tree_type", sa.String(), nullable=False),
        sa.Column("tree_data", sa.JSON(), nullable=False),
        sa.Column("operation_log", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("misconception_log")
    op.drop_table("operation_history")
    op.drop_table("quiz_results")
    op.drop_index("ix_concept_mastery_user_concept", table_name="concept_mastery")
    op.drop_table("concept_mastery")
    op.drop_table("user_sessions")
    op.drop_table("tree_states")
