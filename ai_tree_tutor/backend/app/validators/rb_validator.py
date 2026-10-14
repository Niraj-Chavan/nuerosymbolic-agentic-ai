"""
Red-Black Tree Symbolic Validation Engine
==========================================
Deterministic mathematical validator for all Red-Black tree invariants.
This is the source of truth for detecting structural violations.

Checks performed:
  1. Root Property       — the root node must be BLACK
  2. Red Property        — no two consecutive RED nodes (a RED node cannot have a RED child)
  3. Black-Depth Property — every path from root to a leaf (null) has the same number of BLACK nodes
  4. BST Property        — left subtree keys < node key < right subtree keys

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

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Rule definitions
# ============================================================

@dataclass(frozen=True)
class RBRule:
    """Defines a single Red-Black validation rule."""
    rule_id: str
    rule_name: str
    type: str
    severity: str
    concept_tag: str
    educational_hint: str


RULES = {
    "ROOT": RBRule(
        rule_id="RB-001",
        rule_name="Root_Property",
        type="root_not_black",
        severity="critical",
        concept_tag="rb_root_property",
        educational_hint=(
            "Property 2 of Red-Black trees: the root must always be BLACK. "
            "This is a base invariant — if the root is RED, the tree is immediately invalid. "
            "After every insert and delete fix-up, the root is recolored to BLACK as the final step. "
            "A red root typically means the student forgot the final 'root.color = BLACK' step."
        ),
    ),
    "RED": RBRule(
        rule_id="RB-002",
        rule_name="Red_Property",
        type="consecutive_red_nodes",
        severity="high",
        concept_tag="rb_red_red_property",
        educational_hint=(
            "Property 4 of Red-Black trees: if a node is RED, both its children must be BLACK. "
            "Two consecutive RED nodes on any path violate this property. "
            "This is the most common violation students make after insertion — they insert a RED node "
            "whose parent is also RED and forget to run the fix-up (recolor/rotate) procedure."
        ),
    ),
    "BLACK_DEPTH": RBRule(
        rule_id="RB-003",
        rule_name="Black_Depth_Property",
        type="unequal_black_height",
        severity="critical",
        concept_tag="rb_black_height",
        educational_hint=(
            "Property 5 of Red-Black trees: every path from the root to a leaf (null) "
            "must contain the same number of BLACK nodes. This 'uniform black-height' "
            "is what guarantees the tree stays balanced (height <= 2*log2(n+1)). "
            "A mismatch means a BLACK node was removed or added on some path without "
            "compensating on all paths — this happens during deletion fix-up errors."
        ),
    ),
    "BST": RBRule(
        rule_id="RB-004",
        rule_name="BST_Ordering",
        type="bst_violation",
        severity="critical",
        concept_tag="binary_search_property",
        educational_hint=(
            "Red-Black trees are Binary Search Trees with additional coloring constraints. "
            "The BST property (left < node < right) must still hold. "
            "Rotations during fix-up preserve BST ordering — if this is violated, "
            "the rotation was performed incorrectly (wrong pointers were reassigned)."
        ),
    ),
}


# ============================================================
# Public API
# ============================================================

def validate_rb(tree_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate all Red-Black tree invariants on an exported tree dict.

    Args:
        tree_data: Nested dict from tree.export_nested().
                   Each node has: key, color, left, right.
                   NIL/null children are represented as None or absent.

    Returns:
        Dict with keys: valid, violations, affected_nodes, concepts_involved.
    """
    violations: List[Dict[str, Any]] = []

    if tree_data is None:
        return _make_result(violations)

    # Phase 1: BST ordering
    _check_bst(tree_data, float("-inf"), float("inf"), violations)

    # Phase 2: Root must be BLACK
    _check_root(tree_data, violations)

    # Phase 3: No consecutive RED nodes
    _check_red_property(tree_data, violations)

    # Phase 4: Equal black-height on all root-to-null paths
    _check_black_depth(tree_data, violations)

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

    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "type": rule.type,
        "severity": rule.severity,
        "affected_nodes": affected_nodes,
        "expected": expected,
        "actual": actual,
        "message": extra_message if extra_message else rule.educational_hint,
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
# Phase 1: BST ordering
# ============================================================

def _check_bst(
    node: Dict[str, Any],
    lo: float,
    hi: float,
    violations: List[Dict[str, Any]],
) -> None:
    """
    Verify BST ordering: lo < node.key < hi.
    Recursively narrow bounds for subtrees.
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
                f"It must be in the range ({lo}, {hi}), but it is not. "
                f"This typically means a rotation was performed with incorrect pointer reassignment."
            ),
        ))

    if node.get("left"):
        _check_bst(node["left"], lo, min(key, hi), violations)
    if node.get("right"):
        _check_bst(node["right"], max(key, lo), hi, violations)


# ============================================================
# Phase 2: Root property
# ============================================================

def _check_root(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> None:
    """Check that the root node is BLACK."""
    if node.get("color") != "BLACK":
        violations.append(_make_violation(
            "ROOT",
            affected_nodes=[node["key"]],
            expected="BLACK",
            actual=node.get("color", "unknown"),
            extra_message=(
                f"Root node {node['key']} is {node.get('color', 'unknown')}, "
                f"but the root must always be BLACK (Property 2). "
                f"Every insert/delete fix-up should end by setting root.color = BLACK."
            ),
        ))


# ============================================================
# Phase 3: Red property (no consecutive RED nodes)
# ============================================================

def _check_red_property(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> None:
    """
    Check that no RED node has a RED child.
    This is Property 4 of Red-Black trees.
    """
    if node.get("color") == "RED":
        for child_key in ("left", "right"):
            child = node.get(child_key)
            if child is not None and child.get("color") == "RED":
                violations.append(_make_violation(
                    "RED",
                    affected_nodes=[node["key"], child["key"]],
                    expected="BLACK child",
                    actual=f"RED child ({child['key']})",
                    extra_message=(
                        f"Red node {node['key']} has a red child {child['key']} "
                        f"({child_key} child). "
                        f"Two consecutive red nodes violate Property 4. "
                        f"This usually means the insert fix-up (recolor or rotation) was not applied, "
                        f"or the wrong case was chosen during the fix-up procedure."
                    ),
                ))

    if node.get("left"):
        _check_red_property(node["left"], violations)
    if node.get("right"):
        _check_red_property(node["right"], violations)


# ============================================================
# Phase 4: Black-depth property (uniform black-height)
# ============================================================

def _check_black_depth(
    node: Dict[str, Any],
    violations: List[Dict[str, Any]],
) -> None:
    """
    Check that all paths from this node to any leaf (null) have the same
    number of BLACK nodes.

    Collects the black-height of every root-to-null path and checks uniformity.
    """
    path_heights: Dict[int, List[Tuple[int, List[int]]]] = {}
    _collect_path_black_heights(node, 0, [], path_heights)

    if not path_heights:
        return

    # Get the set of unique black heights
    unique_heights = sorted(path_heights.keys())

    if len(unique_heights) > 1:
        # Collect all affected nodes from all paths
        all_path_nodes: Set[int] = set()
        for bh, paths in path_heights.items():
            for _, path_nodes in paths:
                all_path_nodes.update(path_nodes)

        # Build detailed message
        path_details = ", ".join(
            f"bh={bh} ({len(paths)} path{'s' if len(paths) != 1 else ''})"
            for bh, paths in sorted(path_heights.items())
        )

        violations.append(_make_violation(
            "BLACK_DEPTH",
            affected_nodes=sorted(all_path_nodes),
            expected=f"uniform black-height (all paths same)",
            actual=unique_heights,
            extra_message=(
                f"Paths from root to leaves have different black heights: {path_details}. "
                f"Every path must contain the same number of BLACK nodes (Property 5). "
                f"This means the tree's height guarantee (O(log n)) is broken. "
                f"This typically occurs when a BLACK node is deleted and the fix-up "
                f"procedure does not correctly restore black-height on all affected paths."
            ),
        ))


def _collect_path_black_heights(
    node: Optional[Dict[str, Any]],
    count: int,
    path_nodes: List[int],
    heights: Dict[int, List[Tuple[int, List[int]]]],
) -> None:
    """
    Traverse all paths from the current node to null leaves.
    Accumulate the black count and the list of nodes on each path.
    Group paths by their black-height.
    """
    if node is None:
        # Reached a leaf (null) — record the black count for this path
        current_nodes = list(path_nodes)
        if count not in heights:
            heights[count] = []
        heights[count].append((count, current_nodes))
        return

    # Track this node in the path
    key = node.get("key")
    if key is not None:
        path_nodes.append(key)

    # Increment black count if this node is BLACK
    new_count = count + (1 if node.get("color") == "BLACK" else 0)

    # Recurse
    _collect_path_black_heights(node.get("left"), new_count, path_nodes, heights)
    _collect_path_black_heights(node.get("right"), new_count, path_nodes, heights)

    # Backtrack
    if key is not None:
        path_nodes.pop()
