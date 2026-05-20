"""
Base Agent — Abstract Interface
=================================
All agents implement this single contract.
Enables the OperationPipeline to treat every agent uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.context.agent_context import AgentContext


class BaseAgent(ABC):
    """Every agent in the system implements this protocol."""

    @abstractmethod
    async def process(self, ctx: AgentContext) -> AgentContext:
        """Process the shared context and return it (mutated in place)."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"<{self.name}>"
