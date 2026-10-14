"""
Symbolic Validation Agent
==========================
Checks tree invariants using deterministic mathematical rules.
Implements BaseAgent protocol. Dispatches to registered validators.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple

from app.agents.base_agent import BaseAgent
from app.context.agent_context import AgentContext
from app.validators.avl_validator import validate_avl
from app.validators.rb_validator import validate_rb
from app.validators.btree_validator import (
    validate_btree,
    validate_bplus,
    validate_heap,
    validate_segment_tree,
)


class ValidationAgent(BaseAgent):
    """Validates tree invariants using internal + external symbolic checks."""

    def __init__(self):
        self._external_validators: Dict[str, Callable] = {
            "avl": lambda inst, export: validate_avl(export),
            "red_black": lambda inst, export: validate_rb(export),
            "btree": lambda inst, export: validate_btree(export, getattr(inst, "order", 3)),
            "bplus_tree": lambda inst, export: validate_bplus(export, getattr(inst, "order", 4)),
            "heap": lambda inst, export: validate_heap(
                getattr(inst, "heap", []),
                getattr(inst, "heap_type", "min"),
            ),
            "segment_tree": lambda inst, export: validate_segment_tree(
                getattr(inst, "data", []),
                getattr(inst, "tree", []),
                getattr(inst, "n", 0),
            ),
        }

    def register_validator(self, tree_type: str, validator_fn: Callable) -> None:
        """Register a new external validator at runtime."""
        self._external_validators[tree_type] = validator_fn

    async def process(self, ctx: AgentContext) -> AgentContext:
        tree = ctx.tree_instance
        internal = self._normalize(tree.validate().get("violations", []))
        external = self._normalize(
            self._run_external(ctx.tree_type, tree, tree.export()).get("violations", []),
        )
        merged = self._merge(internal, external)
        result = self._build(ctx.tree_type, merged, tree.export())
        ctx.violations = result["violations"]
        ctx.validation_valid = result["valid"]
        ctx.affected_nodes = result["affected_nodes"]
        return ctx

    def _run_external(self, tree_type: str, instance: Any, export: Any) -> Dict:
        validator = self._external_validators.get(tree_type)
        if validator:
            return validator(instance, export)
        return {"valid": True, "violations": [], "affected_nodes": [], "concepts_involved": []}

    def _normalize(self, violations: List[Dict]) -> List[Dict]:
        normalized = []
        for v in violations:
            nv = dict(v)
            if "affected_nodes" not in nv:
                nodes = []
                for field in ("node", "parent", "child"):
                    if field in nv and isinstance(nv[field], int):
                        nodes.append(nv[field])
                nv["affected_nodes"] = nodes
            nv.setdefault("rule_id", "")
            nv.setdefault("rule_name", nv.get("type", "unknown"))
            nv.setdefault("severity", "medium")
            nv.setdefault("educational_hint", nv.get("message", ""))
            nv.setdefault("concept_tag", "")
            nv.setdefault("expected", None)
            nv.setdefault("actual", None)
            normalized.append(nv)
        return normalized

    def _merge(self, internal: List[Dict], external: List[Dict]) -> List[Dict]:
        seen: Set[Tuple] = set()
        merged = []
        for v in external + internal:
            sig = (v.get("rule_id", ""), v.get("type", ""),
                   tuple(sorted(v.get("affected_nodes", []))))
            if sig not in seen:
                seen.add(sig)
                merged.append(v)
        return merged

    def _build(self, tree_type: str, violations: List[Dict], export: Any) -> Dict:
        affected: Set[int] = set()
        concepts: Set[str] = set()
        for v in violations:
            affected.update(v.get("affected_nodes", []))
            if v.get("concept_tag"):
                concepts.add(v["concept_tag"])
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "affected_nodes": sorted(affected),
            "concepts_involved": sorted(concepts),
            "tree_type": tree_type,
            "tree": export,
        }
