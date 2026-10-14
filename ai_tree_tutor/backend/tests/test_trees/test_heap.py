"""
Binary Heap Tests
==================
Tests insertion, deletion, invariants, and exports of BinaryHeap (min and max).
"""

from __future__ import annotations
import pytest

from app.trees.heap import BinaryHeap


class TestBinaryHeap:
    def test_min_heap_operations(self):
        heap = BinaryHeap(heap_type="min")
        assert heap.export() is None

        # Insert elements
        heap.insert(10)
        heap.insert(5)
        heap.insert(15)
        heap.insert(3)

        # Min heap root should be smallest (3)
        exported = heap.export()
        assert exported["key"] == 3
        assert heap.heap[0] == 3

        # Validate invariants
        validation = heap.validate()
        assert validation["valid"] is True

        # Extract root (delete key = None)
        res = heap.delete()
        assert res["key"] == 3
        assert heap.heap[0] == 5

        # Check invariants again
        validation = heap.validate()
        assert validation["valid"] is True

    def test_max_heap_operations(self):
        heap = BinaryHeap(heap_type="max")
        assert heap.export() is None

        # Insert elements
        heap.insert(10)
        heap.insert(20)
        heap.insert(5)
        heap.insert(25)

        # Max heap root should be largest (25)
        exported = heap.export()
        assert exported["key"] == 25
        assert heap.heap[0] == 25

        # Validate invariants
        validation = heap.validate()
        assert validation["valid"] is True

        # Extract root (delete key = None)
        res = heap.delete()
        assert res["key"] == 25
        assert heap.heap[0] == 20

        # Check invariants again
        validation = heap.validate()
        assert validation["valid"] is True
