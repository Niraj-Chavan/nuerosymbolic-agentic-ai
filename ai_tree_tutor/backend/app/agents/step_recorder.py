"""
Step Recorder — Registry Pattern
==================================
Replaces the massive if/elif chain in main.py with a registry.
Each tree type registers its step recording functions.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.core import tree_factory

# Registry: tree_type -> { operation -> recorder_function }
RecorderFn = Callable[..., Dict[str, Any]]
_recorders: Dict[str, Dict[str, RecorderFn]] = {}


def register(tree_type: str, operation: str, fn: RecorderFn) -> None:
    """Register a step recorder for a given tree type and operation."""
    if tree_type not in _recorders:
        _recorders[tree_type] = {}
    _recorders[tree_type][operation] = fn


def record(tree_type: str, operation: str, tree_instance: Any, key: int, **kwargs) -> Dict[str, Any]:
    """Dispatch to the correct recorder. Falls back to generic."""
    ops = _recorders.get(tree_type, {})
    fn = ops.get(operation)
    if fn:
        return fn(tree_instance, key, **kwargs)
    return record_generic_operation(tree_instance, operation, key)


def record_generic_operation(tree_instance: Any, operation: str, key: int) -> Dict[str, Any]:
    """Fallback generic step recorder."""
    result = {}
    if hasattr(tree_instance, operation):
        result = getattr(tree_instance, operation)(key)
    export = tree_instance.export() if hasattr(tree_instance, "export") else {}
    log = result.get("log", []) if isinstance(result, dict) else []
    steps = []
    for entry in log:
        steps.append({
            "tree": export,
            "description": entry.get("message", str(entry)),
            "step_type": entry.get("type", "info"),
            "highlighted_nodes": entry.get("affected_nodes", []),
            "why": entry.get("why", ""),
        })
    return {
        "tree": export,
        "log": log,
        "animation_steps": steps,
    }


class StepRecorderRegistry:
    """Facade for step recording across all tree types."""

    def record(self, tree_type: str, operation: str, tree_instance: Any, key: int, **kwargs) -> Dict[str, Any]:
        return record(tree_type, operation, tree_instance, key, **kwargs)

    @staticmethod
    def supported_types() -> list:
        return list(_recorders.keys())
