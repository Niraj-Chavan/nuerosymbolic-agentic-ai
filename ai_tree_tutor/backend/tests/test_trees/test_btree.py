"""
B-Tree & B+ Tree Tests
======================
Tests insertion, deletion, invariants, and exports of B-Tree and B+ Tree.
"""

from __future__ import annotations
import pytest

from app.trees.btree import BTree
from app.trees.bplus_tree import BPlusTree
from app.validators.btree_validator import validate_btree, validate_bplus


class TestBTree:
    def test_insert_order3(self):
        tree = BTree(order=3)
        assert tree.export() is None

        # Insert 10, 20, 5 -> should NOT split since max_keys = order = 3
        tree.insert(10)
        tree.insert(20)
        tree.insert(5)
        exported = tree.export()
        assert exported["keys"] == [5, 10, 20]
        assert exported["leaf"] is True

        # Insert 15 -> should trigger split since keys = [5, 10, 15, 20] has size 4 > 3
        tree.insert(15)
        exported = tree.export()
        assert exported["keys"] == [15]
        assert exported["leaf"] is False
        assert len(exported["children"]) == 2
        assert exported["children"][0]["keys"] == [5, 10]
        assert exported["children"][1]["keys"] == [20]

        # Invariant checks
        val = validate_btree(exported, order=3)
        assert val["valid"] is True

    def test_delete_order3(self):
        tree = BTree(order=3)
        for val in [10, 20, 5, 15, 25]:
            tree.insert(val)

        # Structure should be root: [15] -> children: [5, 10], [20, 25]
        exported = tree.export()
        assert exported["keys"] == [15]
        assert len(exported["children"]) == 2
        assert exported["children"][0]["keys"] == [5, 10]
        assert exported["children"][1]["keys"] == [20, 25]

        # Delete 10 -> child 0 becomes [5], length 1.
        # Since min_keys = order // 2 = 1, length 1 is valid (no borrow/merge).
        tree.delete(10)
        exported = tree.export()
        assert exported["children"][0]["keys"] == [5]

        # Delete 5 -> child 0 becomes [], length 0.
        # This is < min_keys (1), so it borrows from right child [20, 25].
        # 15 moves to left, 20 moves to root.
        tree.delete(5)
        exported = tree.export()
        assert exported["keys"] == [20]
        assert exported["children"][0]["keys"] == [15]
        assert exported["children"][1]["keys"] == [25]

        # Invariant checks
        val = validate_btree(exported, order=3)
        assert val["valid"] is True


class TestBPlusTree:
    def test_bplus_insert_order3(self):
        tree = BPlusTree(order=3)
        assert tree.export() is None

        # Insert 10, 20, 5 -> should NOT split since max_keys = order = 3
        tree.insert(10)
        tree.insert(20)
        tree.insert(5)
        exported = tree.export()
        assert exported["keys"] == [5, 10, 20]
        assert exported["leaf"] is True

        # Insert 15 -> should split since keys length is 4 > 3
        tree.insert(15)
        exported = tree.export()
        assert exported["keys"] == [15]
        assert exported["leaf"] is False
        assert len(exported["children"]) == 2
        assert exported["children"][0]["keys"] == [5, 10]
        assert exported["children"][1]["keys"] == [15, 20]

        # Invariant checks
        val = validate_bplus(exported, order=3)
        assert val["valid"] is True
