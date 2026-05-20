"""
Tree Execution Agent
=====================
Manages tree instances and executes operations.
Implements the BaseAgent protocol for pipeline compatibility.
"""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.context.agent_context import AgentContext
from app.core import tree_factory


def _make_key(tree_type: str, session_id: str = "default", **kwargs) -> str:
    """Cache key includes options so different parameters create distinct trees."""
    parts = [session_id, tree_type]
    if kwargs.get("order"):
        parts.append(f"o{kwargs['order']}")
    if kwargs.get("heap_type"):
        parts.append(f"h{kwargs['heap_type']}")
    return "_".join(parts)


class TreeExecutionAgent(BaseAgent):
    """Agent that manages tree instances and executes operations."""

    def __init__(self):
        self.trees: Dict[str, Any] = {}

    async def process(self, ctx: AgentContext) -> AgentContext:
        tree = self.get_or_create(ctx.tree_type, ctx.session_id, **ctx.options)
        ctx.tree_instance = tree

        if ctx.operation == "insert":
            result = tree.insert(ctx.key)
        elif ctx.operation == "delete":
            result = tree.delete(ctx.key)
        elif ctx.operation == "search":
            result = tree.search(ctx.key)
        else:
            raise ValueError(f"Unknown operation: {ctx.operation}")

        ctx.tree_export = tree.export()
        ctx.operation_log = result.get("log", [])
        ctx.found = result.get("found")
        ctx.search_path = result.get("path", [])
        ctx.metadata["tree_export"] = ctx.tree_export
        return ctx

    def get_or_create(self, tree_type: str, session_id: str = "default", **kwargs) -> Any:
        key = _make_key(tree_type, session_id, **kwargs)
        if key not in self.trees:
            self.trees[key] = tree_factory.create(tree_type, **kwargs)
        return self.trees[key]

    def reset(self, tree_type: str, session_id: str = "default", **kwargs) -> Dict[str, Any]:
        key = _make_key(tree_type, session_id, **kwargs)
        self.trees[key] = tree_factory.create(tree_type, **kwargs)
        return {"status": "reset", "tree_type": tree_type}

    def get_tree_export(self, tree_type: str, session_id: str = "default", **kwargs) -> Dict[str, Any]:
        key = _make_key(tree_type, session_id, **kwargs)
        if key in self.trees:
            return {"tree": self.trees[key].export()}
        prefix = f"{session_id}_{tree_type}"
        for k in self.trees:
            if k == prefix or k.startswith(prefix + "_"):
                return {"tree": self.trees[k].export()}
        return {"tree": None}
