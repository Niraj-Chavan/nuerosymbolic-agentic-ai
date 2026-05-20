"""
Binary Heap Implementation
===========================
A complete binary tree that satisfies the min-heap property
(parent ≤ children). Can be toggled to max-heap.
"""

from __future__ import annotations
from typing import Any, List, Dict, Optional


class BinaryHeap:
    """Array-based Binary Heap (min-heap by default)."""

    def __init__(self, heap_type: str = "min"):
        self.heap: List[int] = []
        self.heap_type = heap_type  # "min" or "max"
        self.operation_log: List[Dict[str, Any]] = []

    def _compare(self, a: int, b: int) -> bool:
        """Return True if a should be higher in the heap than b."""
        if self.heap_type == "min":
            return a < b
        return a > b

    def _swap(self, i: int, j: int) -> None:
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.operation_log.append({
            "action": "swap",
            "positions": [i, j],
            "values": [self.heap[i], self.heap[j]],
        })

    # ---------------------------------------------------------------- insert
    def insert(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        self.heap.append(key)
        self.operation_log.append({"action": "insert", "key": key, "position": len(self.heap) - 1})
        self._sift_up(len(self.heap) - 1)
        return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self._compare(self.heap[idx], self.heap[parent]):
                self._swap(idx, parent)
                idx = parent
            else:
                break

    # ---------------------------------------------------------------- delete (extract root)
    def delete(self, key: int = None) -> Dict[str, Any]:
        """Remove a specific key, or extract root if key is None."""
        self.operation_log = []
        if not self.heap:
            return {"operation": "delete", "key": key, "error": "Heap is empty", "tree": self.export(), "log": self.operation_log}

        if key is None:
            idx = 0
            key = self.heap[0]
        else:
            try:
                idx = self.heap.index(key)
            except ValueError:
                self.operation_log.append({"action": "not_found", "key": key})
                return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

        self.operation_log.append({"action": "delete", "key": key, "position": idx})
        last = len(self.heap) - 1
        self._swap(idx, last)
        self.heap.pop()

        if idx < len(self.heap):
            self._sift_down(idx)
            self._sift_up(idx)

        return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

    def _sift_down(self, idx: int) -> None:
        size = len(self.heap)
        while True:
            target = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            if left < size and self._compare(self.heap[left], self.heap[target]):
                target = left
            if right < size and self._compare(self.heap[right], self.heap[target]):
                target = right
            if target == idx:
                break
            self._swap(idx, target)
            idx = target

    # ---------------------------------------------------------------- search
    def search(self, key: int) -> Dict[str, Any]:
        found = key in self.heap
        path = []
        if found:
            idx = self.heap.index(key)
            while idx > 0:
                path.append(self.heap[idx])
                idx = (idx - 1) // 2
            if self.heap:
                path.append(self.heap[0])
            path.reverse()
        return {"operation": "search", "key": key, "found": found, "path": path, "tree": self.export()}

    # ---------------------------------------------------------------- export
    def export(self) -> Optional[Dict[str, Any]]:
        if not self.heap:
            return None
        return self._export_node(0)

    def _export_node(self, idx: int) -> Optional[Dict[str, Any]]:
        if idx >= len(self.heap):
            return None
        left = self._export_node(2 * idx + 1)
        right = self._export_node(2 * idx + 2)
        return {
            "key": self.heap[idx],
            "value": self.heap[idx],
            "index": idx,
            "left": left,
            "right": right,
            "children": [child for child in (left, right) if child is not None],
        }

    # ------------------------------------------------------------- validation
    def validate(self) -> Dict[str, Any]:
        violations = []
        for i in range(len(self.heap)):
            left = 2 * i + 1
            right = 2 * i + 2
            if left < len(self.heap) and not self._compare(self.heap[i], self.heap[left]) and self.heap[i] != self.heap[left]:
                violations.append({
                    "type": "heap_property_violated",
                    "parent_index": i,
                    "child_index": left,
                    "parent_value": self.heap[i],
                    "child_value": self.heap[left],
                    "message": f"{'Min' if self.heap_type == 'min' else 'Max'}-heap violated: parent {self.heap[i]} at index {i} vs child {self.heap[left]} at index {left}.",
                })
            if right < len(self.heap) and not self._compare(self.heap[i], self.heap[right]) and self.heap[i] != self.heap[right]:
                violations.append({
                    "type": "heap_property_violated",
                    "parent_index": i,
                    "child_index": right,
                    "parent_value": self.heap[i],
                    "child_value": self.heap[right],
                    "message": f"{'Min' if self.heap_type == 'min' else 'Max'}-heap violated: parent {self.heap[i]} at index {i} vs child {self.heap[right]} at index {right}.",
                })
        return {"valid": len(violations) == 0, "violations": violations, "tree": self.export()}
