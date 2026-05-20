"""
B-Tree / B+ Tree / Heap / Segment Tree Symbolic Validator
=========================================================
Deterministic validation of invariants for B-Tree, B+ Tree,
Binary Heap, and Segment Tree.
"""

from typing import Any, Dict, List, Optional


# ============================================================ B-Tree
def validate_btree(tree_data: Optional[Dict[str, Any]], order: int = 3) -> Dict[str, Any]:
    """Validate B-Tree invariants."""
    violations: List[Dict[str, Any]] = []
    if tree_data is None:
        return {"valid": True, "violations": []}
    _validate_btree_node(tree_data, violations, is_root=True, order=order)
    return {"valid": len(violations) == 0, "violations": violations}


def _validate_btree_node(node: Dict[str, Any], violations: List[Dict], is_root: bool, order: int) -> int:
    keys = node.get("keys", [])
    children = node.get("children", [])
    is_leaf = node.get("leaf", True)

    max_keys = order
    min_keys = order // 2 if not is_root else 1

    if len(keys) > max_keys:
        violations.append({
            "type": "too_many_keys", "keys": keys, "max": max_keys,
            "message": f"Node has {len(keys)} keys, max is {max_keys}.",
        })

    for i in range(len(keys) - 1):
        if keys[i] >= keys[i + 1]:
            violations.append({
                "type": "keys_not_sorted", "keys": keys,
                "message": f"Keys not sorted: {keys}.",
            })
            break

    if not is_leaf and len(children) != len(keys) + 1:
        violations.append({
            "type": "wrong_child_count",
            "message": f"Node with {len(keys)} keys has {len(children)} children (expected {len(keys) + 1}).",
        })

    depths = []
    for child in children:
        d = _validate_btree_node(child, violations, False, order)
        depths.append(d)
    if depths and len(set(depths)) > 1:
        violations.append({
            "type": "unequal_leaf_depth", "depths": depths,
            "message": f"Children at unequal depths: {depths}.",
        })
    return (depths[0] + 1) if depths else 0


# ============================================================ B+ Tree
def validate_bplus(tree_data: Optional[Dict[str, Any]], order: int = 4) -> Dict[str, Any]:
    """Validate B+ Tree invariants."""
    violations: List[Dict[str, Any]] = []
    if tree_data is None:
        return {"valid": True, "violations": []}
    _validate_bplus_node(tree_data, order, violations, is_root=True)
    return {"valid": len(violations) == 0, "violations": violations}


def _validate_bplus_node(node: Dict, order: int, violations: List[Dict], is_root: bool = False) -> int:
    keys = node.get("keys", [])
    children = node.get("children", [])
    leaf = node.get("leaf", True)
    max_keys = order

    if len(keys) > max_keys:
        violations.append({
            "type": "too_many_keys", "keys": keys,
            "message": f"Node has {len(keys)} keys, max is {max_keys}.",
        })

    for i in range(len(keys) - 1):
        if keys[i] >= keys[i + 1]:
            violations.append({
                "type": "keys_not_sorted", "keys": keys,
                "message": f"Keys not sorted: {keys}.",
            })
            break

    if not leaf:
        if len(children) != len(keys) + 1:
            violations.append({
                "type": "wrong_child_count",
                "message": f"Node with {len(keys)} keys needs {len(keys) + 1} children, has {len(children)}.",
            })
        depths = []
        for child in children:
            d = _validate_bplus_node(child, order, violations)
            depths.append(d)
        if depths and len(set(depths)) > 1:
            violations.append({
                "type": "unequal_leaf_depth", "depths": depths,
                "message": f"Children at unequal depths: {depths}.",
            })
        return (depths[0] + 1) if depths else 0
    return 0


# ============================================================ Binary Heap
def validate_heap(heap_array: List[int], heap_type: str = "min") -> Dict[str, Any]:
    """Validate binary heap property on a flat array."""
    violations: List[Dict[str, Any]] = []
    for i in range(len(heap_array)):
        left = 2 * i + 1
        right = 2 * i + 2
        for child in (left, right):
            if child < len(heap_array):
                ok = heap_array[i] <= heap_array[child] if heap_type == "min" else heap_array[i] >= heap_array[child]
                if not ok:
                    violations.append({
                        "type": "heap_property_violated",
                        "parent_index": i, "child_index": child,
                        "parent_value": heap_array[i], "child_value": heap_array[child],
                        "message": (
                            f"{'Min' if heap_type == 'min' else 'Max'}-heap violated: "
                            f"parent {heap_array[i]}@{i} vs child {heap_array[child]}@{child}."
                        ),
                    })
    return {"valid": len(violations) == 0, "violations": violations}


# ============================================================ Segment Tree
def validate_segment_tree(data: List[int], seg_tree: List[int], n: int) -> Dict[str, Any]:
    """Validate segment tree against source data."""
    violations: List[Dict[str, Any]] = []
    if n == 0:
        return {"valid": True, "violations": []}
    _validate_seg_node(1, 0, n - 1, data, seg_tree, violations)
    return {"valid": len(violations) == 0, "violations": violations}


def _validate_seg_node(node: int, start: int, end: int, data: List[int], seg: List[int], violations: List[Dict]) -> int:
    if node >= len(seg):
        return 0
    if start == end:
        if seg[node] != data[start]:
            violations.append({
                "type": "leaf_mismatch", "index": start,
                "expected": data[start], "actual": seg[node],
                "message": f"Leaf at index {start}: expected {data[start]}, got {seg[node]}.",
            })
        return seg[node]

    mid = (start + end) // 2
    left_sum = _validate_seg_node(2 * node, start, mid, data, seg, violations)
    right_sum = _validate_seg_node(2 * node + 1, mid + 1, end, data, seg, violations)
    expected = left_sum + right_sum
    if seg[node] != expected:
        violations.append({
            "type": "invalid_range_sum", "range": [start, end],
            "expected": expected, "actual": seg[node],
            "message": f"Node {node} range [{start},{end}]: expected {expected}, got {seg[node]}.",
        })
    return seg[node]
