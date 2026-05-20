"""
Database Connection — SQLAlchemy Async Setup
=============================================
Manages PostgreSQL/SQLite connection lifecycle.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_connect_kwargs: dict = {"echo": settings.debug}
# pool_size/max_overflow are only valid for PostgreSQL (asyncpg)
if settings.database_url.startswith("postgresql"):
    _connect_kwargs["pool_size"] = 10
    _connect_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.database_url,
    **_connect_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. For dev/quickstart. Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()
