"""
Segment Tree Implementation
============================
A binary tree used for answering range queries and performing range updates
efficiently (in O(log n) time).
"""

from __future__ import annotations
from typing import Any, List, Dict, Optional


class SegmentTree:
    """Segment Tree for range sum queries and point updates."""

    def __init__(self, data: List[int] = None):
        self.data: List[int] = data or []
        self.n = len(self.data)
        self.tree: List[int] = [0] * (4 * max(self.n, 1))
        self.operation_log: List[Dict[str, Any]] = []
        if self.data:
            self._build(1, 0, self.n - 1)

    def _build(self, node: int, start: int, end: int) -> None:
        if start == end:
            self.tree[node] = self.data[start]
        else:
            mid = (start + end) // 2
            self._build(2 * node, start, mid)
            self._build(2 * node + 1, mid + 1, end)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    # ---------------------------------------------------------------- insert (update)
    def insert(self, key: int) -> Dict[str, Any]:
        """Append a value and rebuild."""
        self.operation_log = []
        self.data.append(key)
        self.n = len(self.data)
        self.tree = [0] * (4 * self.n)
        self._build(1, 0, self.n - 1)
        self.operation_log.append({"action": "insert", "key": key, "position": self.n - 1})
        return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}

    def update(self, index: int, value: int) -> Dict[str, Any]:
        """Point update: set data[index] = value."""
        self.operation_log = []
        if index < 0 or index >= self.n:
            return {"operation": "update", "error": "Index out of range"}
        self.data[index] = value
        self._update(1, 0, self.n - 1, index, value)
        self.operation_log.append({"action": "update", "index": index, "value": value})
        return {"operation": "update", "index": index, "value": value, "tree": self.export(), "log": self.operation_log}

    def _update(self, node: int, start: int, end: int, idx: int, val: int) -> None:
        if start == end:
            self.tree[node] = val
        else:
            mid = (start + end) // 2
            if idx <= mid:
                self._update(2 * node, start, mid, idx, val)
            else:
                self._update(2 * node + 1, mid + 1, end, idx, val)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    # ---------------------------------------------------------------- delete
    def delete(self, key: int) -> Dict[str, Any]:
        """Remove first occurrence of key and rebuild."""
        self.operation_log = []
        if key not in self.data:
            self.operation_log.append({"action": "not_found", "key": key})
            return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}
        idx = self.data.index(key)
        self.data.pop(idx)
        self.n = len(self.data)
        self.tree = [0] * (4 * max(self.n, 1))
        if self.data:
            self._build(1, 0, self.n - 1)
        self.operation_log.append({"action": "delete", "key": key, "index": idx})
        return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

    # ---------------------------------------------------------------- search (range query)
    def search(self, key: int) -> Dict[str, Any]:
        """Search for a value in the data array."""
        found = key in self.data
        path = []
        if found:
            path = [i for i, v in enumerate(self.data) if v == key]
        return {"operation": "search", "key": key, "found": found, "path": path, "tree": self.export()}

    def range_query(self, left: int, right: int) -> Dict[str, Any]:
        """Range sum query over [left, right]."""
        if left < 0 or right >= self.n or left > right:
            return {"operation": "range_query", "error": "Invalid range"}
        result = self._query(1, 0, self.n - 1, left, right)
        return {"operation": "range_query", "left": left, "right": right, "result": result, "tree": self.export()}

    def _query(self, node: int, start: int, end: int, l: int, r: int) -> int:
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        mid = (start + end) // 2
        return self._query(2 * node, start, mid, l, r) + self._query(2 * node + 1, mid + 1, end, l, r)

    # ---------------------------------------------------------------- export
    def export(self) -> Optional[Dict[str, Any]]:
        if self.n == 0:
            return None
        return self._export_node(1, 0, self.n - 1)

    def _export_node(self, node: int, start: int, end: int) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "key": f"{start}:{end}",
            "node_index": node,
            "range": [start, end],
            "value": self.tree[node],
            "children": [],
        }
        if start < end:
            mid = (start + end) // 2
            result["left"] = self._export_node(2 * node, start, mid)
            result["right"] = self._export_node(2 * node + 1, mid + 1, end)
            result["children"] = [result["left"], result["right"]]
        else:
            result["left"] = None
            result["right"] = None
        return result

    # ------------------------------------------------------------- validation
    def validate(self) -> Dict[str, Any]:
        violations = []
        if self.n > 0:
            self._validate_node(1, 0, self.n - 1, violations)
        return {"valid": len(violations) == 0, "violations": violations, "tree": self.export()}

    def _validate_node(self, node: int, start: int, end: int, violations: List[Dict]) -> int:
        if start == end:
            if self.tree[node] != self.data[start]:
                violations.append({
                    "type": "leaf_mismatch",
                    "node_index": node,
                    "expected": self.data[start],
                    "actual": self.tree[node],
                    "message": f"Leaf node {node} at index {start}: expected {self.data[start]}, got {self.tree[node]}.",
                })
            return self.tree[node]
        mid = (start + end) // 2
        left_sum = self._validate_node(2 * node, start, mid, violations)
        right_sum = self._validate_node(2 * node + 1, mid + 1, end, violations)
        expected = left_sum + right_sum
        if self.tree[node] != expected:
            violations.append({
                "type": "invalid_range_sum",
                "node_index": node,
                "range": [start, end],
                "expected": expected,
                "actual": self.tree[node],
                "message": f"Node {node} range [{start},{end}]: expected sum {expected}, got {self.tree[node]}.",
            })
        return self.tree[node]
