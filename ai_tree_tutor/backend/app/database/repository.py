"""
Abstract Repository — Generic CRUD interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Generic repository pattern for database access."""

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        ...

    @abstractmethod
    async def list(self, **filters) -> List[T]:
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        ...

    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        ...

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        ...
