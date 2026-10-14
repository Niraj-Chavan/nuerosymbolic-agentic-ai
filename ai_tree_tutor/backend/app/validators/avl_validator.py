"""
AVL Tree Symbolic Validation Engine
=====================================
Deterministic mathematical validator for all AVL tree invariants.
This is the source of truth for detecting structural violations.

Checks performed:
  1. BST Property     — left subtree keys < node key < right subtree keys
  2. Balance Factor   — |BF| <= 1 for every node, and BF = height(L) - height(R)
  3. Height Correctness — node.height = 1 + max(height(left), height(right))
  4. Rotation Validity — after a rotation, BST ordering is preserved and
                         heights are recomputed correctly (checked implicitly
                         via balance + height checks on the resulting tree)
  5. Structural Validity — no cycles, consistent parent-child links,
                           every non-leaf node has properly structured children

Output format (always):
  {
    "valid": bool,
    "violations": [
      {
        "rule_id": str,
        "rule_name": str,
        "type": str,
        "severity": str,           # "critical" | "high" | "medium"
        "affected_nodes": [int],
        "expected": Any,
        "actual": Any,
        "message": str,
        "educational_hint": str,
        "concept_tag": str,
      },
      ...
    ],
    "affected_nodes": [int],       # deduplicated list of all nodes in any violation
    "concepts_involved": [str],    # deduplicated list of concept tags
  }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Rule definitions
# ============================================================

@dataclass(frozen=True)
class AVLRule:
    """Defines a single AVL validation rule."""
    rule_id: str
    rule_name: str
    type: str
    severity: str
    concept_tag: str
    educational_hint: str


RULES = {
    "BST": AVLRule(
        rule_id="AVL-001",
        rule_name="BST_Ordering",
        type="bst_violation",
        severity="critical",
        concept_tag="binary_search_property",
        educational_hint=(
            "The Binary Search Tree property requires that for every node, "
            "all keys in the left subtree are strictly less than the node's key, "
            "and all keys in the right subtree are strictly greater. "
            "This is a fundamental prerequisite — if violated, search will not work."
        ),
    ),
    "BALANCE_RANGE": AVLRule(
        rule_id="AVL-002",
        rule_name="Balance_Factor_Range",
        type="balance_factor_exceeded",
        severity="high",
        concept_tag="balance_factor_invariant",
        educational_hint=(
            "The AVL invariant requires that for every node, "
            "|height(left) - height(right)| <= 1. "
            "If the balance factor is outside [-1, 0, 1], a rotation is needed. "
            "Students often confuse balance factor with subtree size or depth."
        ),
    ),
    "BALANCE_CALC": AVLRule(
        rule_id="AVL-003",
        rule_name="Balance_Factor_Calculation",
        type="balance_factor_mismatch",
        severity="medium",
        concept_tag="balance_factor_computation",
        educational_hint=(
            "Balance factor is computed as: BF = height(left_subtree) - height(right_subtree). "
            "A mismatch means the stored BF does not match the actual heights of the children. "
            "This suggests the student did not recompute BF after a structural change."
        ),
    ),
    "HEIGHT": AVLRule(
        rule_id="AVL-004",
        rule_name="Height_Correctness",
        type="incorrect_height",
        severity="high",
        concept_tag="height_definition",
        educational_hint=(
            "The height of a node is: 1 + max(height(left), height(right)). "
            "After any insertion, deletion, or rotation, heights must be updated "
            "on the path from the changed node back to the root. "
            "An incorrect height indicates the student forgot to update heights during rebalancing."
        ),
    ),
    "STRUCTURE": AVLRule(
        rule_id="AVL-005",
        rule_name="Structural_Validity",
        type="structural_violation",
        severity="critical",
        concept_tag="tree_structure",
        educational_hint=(
            "A valid binary tree must have no cycles, and every child reference "
            "must point to a properly structured node (with key, height, balance_factor). "
            "A structural violation means the tree is malformed — possibly due to "
            "incorrect pointer manipulation during a rotation."
        ),
    ),
}


# ============================================================
# Public API
# ============================================================

def validate_avl(tree_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate all AVL tree invariants on an exported tree dict.

    Args:
        tree_data: Nested dict from tree.export_nested().
                   Each node has: key, height, balance_factor, left, right.

    Returns:
        Dict with keys: valid, violations, affected_nodes, concepts_involved.
    """
    violations: List[Dict[str, Any]] = []

    if tree_data is None:
        return _make_result(violations)

    # Phase 1: Structural validity (detect malformed nodes)
    _check_structure(tree_data, violations)

    # Phase 2: BST ordering
    _check_bst(tree_data, float("-inf"), float("inf"), violations)

    # Phase 3: Height consistency (bottom-up, returns computed height)
    _check_height(tree_data, violations)

    # Phase 4: Balance factor range (|BF| <= 1)
    _check_balance_range(tree_data, violations)

    # Phase 5: Balance factor correctness (stored BF vs computed BF)
    _check_balance_calc(tree_data, violations)

    return _make_result(violations)


# ============================================================
# Violation builders
# ============================================================

def _make_violation(
    rule_key: str,
    affected_nodes: List[int],
    expected: Any = None,
    actual: Any = None,
    extra_message: str = "",
) -> Dict[str, Any]:
    """Create a structured violation record from a rule definition."""
    rule = RULES[rule_key]
    base_msg = rule.educational_hint
    msg = extra_message if extra_message else base_msg

    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "type": rule.type,
        "severity": rule.severity,
        "affected_nodes": affected_nodes,
        "expected": expected,
        "actual": actual,
        "message": msg,
        "educational_hint": rule.educational_hint,
        "concept_tag": rule.concept_tag,
    }


def _make_result(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the final result with deduplicated affected_nodes and concepts."""
    affected: Set[int] = set()
    concepts: Set[str] = set()

    for v in violations:
        for n in v.get("affected_nodes", []):
            affected.add(n)
        if v.get("concept_tag"):
            concepts.add(v["concept_tag"])

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "affected_nodes": sorted(affected),
        "concepts_involved": sorted(concepts),
    }


# ============================================================
# Phase 1: Structural validity
# ============================================================

def _check_structure(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
    visited: Optional[Set[int]] = None,
) -> None:
    """
    Check that the tree structure is well-formed:
    - No cycles (track visited keys)
    - Every node has required fields: key, height, balance_factor
    - Children are either None or valid dicts
    """
    if visited is None:
        visited = set()

    key = node.get("key")
    if key is None:
        violations.append(_make_violation(
            "STRUCTURE",
            affected_nodes=[],
            expected="node with 'key' field",
            actual="node missing 'key'",
            extra_message="A node is missing the required 'key' field.",
        ))
        return

    if key in visited:
        violations.append(_make_violation(
            "STRUCTURE",
            affected_nodes=[key],
            expected="tree with no cycles",
            actual=f"cycle detected involving node {key}",
            extra_message=f"Node {key} appears multiple times — the tree has a cycle.",
        ))
        return

    visited.add(key)

    # Check required fields
    for field_name in ("height", "balance_factor"):
        if field_name not in node:
            violations.append(_make_violation(
                "STRUCTURE",
                affected_nodes=[key],
                expected=f"node with '{field_name}' field",
                actual=f"node missing '{field_name}'",
                extra_message=f"Node {key} is missing the '{field_name}' field.",
            ))

    # Recurse into children
    for child_key in ("left", "right"):
        child = node.get(child_key)
        if child is not None:
            if not isinstance(child, dict):
                violations.append(_make_violation(
                    "STRUCTURE",
                    affected_nodes=[key],
                    expected="dict node or None",
                    actual=f"{type(child).__name__}",
                    extra_message=f"Node {key}'s '{child_key}' child is not a valid node dict.",
                ))
            else:
                _check_structure(child, violations, visited)


# ============================================================
# Phase 2: BST ordering
# ============================================================

def _check_bst(
    node: Dict[str, Any],
    lo: float,
    hi: float,
    violations: List[Dict[str, Any]],
) -> None:
    """
    Verify BST ordering: lo < node.key < hi.
    Recursively narrow bounds for left (lo, key) and right (key, hi) subtrees.
    """
    key = node["key"]

    if key <= lo or key >= hi:
        violations.append(_make_violation(
            "BST",
            affected_nodes=[key],
            expected=f"in range ({lo}, {hi})",
            actual=key,
            extra_message=(
                f"Node {key} violates BST ordering. "
                f"All keys in the left subtree must be < {key}, "
                f"and all keys in the right subtree must be > {key}."
            ),
        ))

    # Recurse with tightened bounds
    if node.get("left"):
        _check_bst(node["left"], lo, min(key, hi), violations)
    if node.get("right"):
        _check_bst(node["right"], max(key, lo), hi, violations)


# ============================================================
# Phase 3: Height correctness (bottom-up)
# ============================================================

def _check_height(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> int:
    """
    Compute the expected height bottom-up and compare with stored height.
    Returns the computed height for the parent's calculation.
    """
    left_h = 0
    right_h = 0

    if node.get("left"):
        left_h = _check_height(node["left"], violations)
    if node.get("right"):
        right_h = _check_height(node["right"], violations)

    expected = 1 + max(left_h, right_h)
    actual = node.get("height", expected)

    if actual != expected:
        violations.append(_make_violation(
            "HEIGHT",
            affected_nodes=[node["key"]],
            expected=expected,
            actual=actual,
            extra_message=(
                f"Node {node['key']} has height {actual}, "
                f"but should be 1 + max({left_h}, {right_h}) = {expected}. "
                f"Height was not updated after a structural change."
            ),
        ))

    return expected


# ============================================================
# Phase 4: Balance factor range (|BF| <= 1)
# ============================================================

def _check_balance_range(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> None:
    """Check that every node's stored balance factor is in [-1, 0, 1]."""
    bf = node.get("balance_factor", 0)

    if abs(bf) > 1:
        violations.append(_make_violation(
            "BALANCE_RANGE",
            affected_nodes=[node["key"]],
            expected="balance factor in [-1, 0, 1]",
            actual=bf,
            extra_message=(
                f"Node {node['key']} has balance factor {bf} "
                f"(must be -1, 0, or 1). "
                f"A rotation is required to restore the AVL property."
            ),
        ))

    if node.get("left"):
        _check_balance_range(node["left"], violations)
    if node.get("right"):
        _check_balance_range(node["right"], violations)


# ============================================================
# Phase 5: Balance factor correctness (stored vs computed)
# ============================================================

def _check_balance_calc(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> None:
    """Check that the stored BF matches the actual BF computed from heights."""
    left_h = _computed_height(node.get("left"))
    right_h = _computed_height(node.get("right"))
    computed_bf = left_h - right_h
    stored_bf = node.get("balance_factor", computed_bf)

    if stored_bf != computed_bf:
        violations.append(_make_violation(
            "BALANCE_CALC",
            affected_nodes=[node["key"]],
            expected=computed_bf,
            actual=stored_bf,
            extra_message=(
                f"Node {node['key']} reports balance factor {stored_bf}, "
                f"but actual BF = height(left) - height(right) = {left_h} - {right_h} = {computed_bf}. "
                f"The stored BF is stale and does not reflect the current tree structure."
            ),
        ))

    if node.get("left"):
        _check_balance_calc(node["left"], violations)
    if node.get("right"):
        _check_balance_calc(node["right"], violations)


def _computed_height(node: Optional[Dict[str, Any]]) -> int:
    """Compute height of a node from its stored height field."""
    if node is None:
        return 0
    return node.get("height", 0)
