"""
AVL Tree Tests
===============
Tests insertion, deletion, rotations, balance invariants,
step recording, and serialization.
"""

from __future__ import annotations

import pytest

from app.trees.avl import AVLTree, RotationCase


# =========================================================================
# Insertion
# =========================================================================

class TestAVLInsert:
    def test_insert_empty_tree(self):
        tree = AVLTree()
        result = tree.insert(10)
        assert tree.root is not None
        assert tree.root.key == 10
        assert tree.root.height == 1
        assert result["operation"] == "insert"
        assert result["key"] == 10

    def test_insert_smaller_goes_left(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(5)
        assert tree.root.left is not None
        assert tree.root.left.key == 5

    def test_insert_larger_goes_right(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(15)
        assert tree.root.right is not None
        assert tree.root.right.key == 15

    def test_insert_no_duplicates(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(10)
        assert tree.size() == 1

    def test_insert_triggers_left_rotation(self):
        """Insert 30, 20, 10 → RR case → left rotation at 30."""
        tree = AVLTree()
        tree.insert(30)
        tree.insert(20)
        tree.insert(10)
        # After RR rotation, 20 becomes root
        assert tree.root.key == 20
        assert tree.root.left.key == 10
        assert tree.root.right.key == 30
        assert abs(tree._balance_factor(tree.root)) <= 1

    def test_insert_triggers_right_rotation(self):
        """Insert 10, 20, 30 → RR case → left rotation at 10."""
        tree = AVLTree()
        tree.insert(10)
        tree.insert(20)
        tree.insert(30)
        assert tree.root.key == 20
        assert tree.root.left.key == 10
        assert tree.root.right.key == 30

    def test_insert_triggers_left_right_rotation(self):
        """Insert 30, 10, 20 → LR case → double rotation."""
        tree = AVLTree()
        tree.insert(30)
        tree.insert(10)
        tree.insert(20)
        assert tree.root.key == 20
        assert tree.root.left.key == 10
        assert tree.root.right.key == 30

    def test_insert_triggers_right_left_rotation(self):
        """Insert 10, 30, 20 → RL case → double rotation."""
        tree = AVLTree()
        tree.insert(10)
        tree.insert(30)
        tree.insert(20)
        assert tree.root.key == 20
        assert tree.root.left.key == 10
        assert tree.root.right.key == 30

    def test_complex_insert_sequence(self):
        """Insert [10, 20, 30, 40, 50, 25] and verify structure."""
        tree = AVLTree()
        for key in [10, 20, 30, 40, 50, 25]:
            tree.insert(key)
        # Root should be 30 after rebalancing
        assert tree.root.key == 30
        # Left subtree: 20 (with 10, 25)
        assert tree.root.left.key == 20
        assert tree.root.left.left.key == 10
        assert tree.root.left.right.key == 25
        # Right subtree: 40 (with None, 50)
        assert tree.root.right.key == 40
        assert tree.root.right.right.key == 50

    def test_balance_factor_maintained_after_inserts(self):
        tree = AVLTree()
        for key in [10, 20, 30, 40, 50, 25, 5, 3, 7, 15, 35, 45, 55]:
            tree.insert(key)
        result = tree.validate()
        assert result["valid"], f"Tree has violations: {result['violations']}"


# =========================================================================
# Deletion
# =========================================================================

class TestAVLDelete:
    def test_delete_leaf_node(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(20)
        tree.insert(5)
        result = tree.delete(5)
        assert result["operation"] == "delete"
        assert result["key"] == 5
        assert tree.root.left is None
        assert tree.size() == 2

    def test_delete_node_with_one_child(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(5)
        tree.insert(3)  # left child of 5
        result = tree.delete(5)
        assert result["operation"] == "delete"
        # 3 should replace 5
        assert tree.root.left.key == 3

    def test_delete_node_with_two_children(self):
        tree = AVLTree()
        tree.insert(20)
        tree.insert(10)
        tree.insert(30)
        tree.insert(5)
        tree.insert(15)
        result = tree.delete(10)
        assert result["operation"] == "delete"
        # 10 is replaced by in-order successor 15
        assert tree.root.left.key == 15

    def test_delete_root_with_two_children(self):
        tree = AVLTree()
        tree.insert(20)
        tree.insert(10)
        tree.insert(30)
        tree.delete(20)
        # Root becomes in-order successor: 30
        assert tree.root.key == 30

    def test_delete_nonexistent_key(self):
        tree = AVLTree()
        tree.insert(10)
        result = tree.delete(99)
        assert tree.size() == 1
        descriptions = [s.get("description", "") for s in result.get("log", [])]
        assert any("not found" in d.lower() for d in descriptions)

    def test_delete_preserves_balance(self):
        tree = AVLTree()
        for key in [10, 20, 30, 40, 50]:
            tree.insert(key)
        tree.delete(40)
        tree.delete(50)
        result = tree.validate()
        assert result["valid"], f"Tree has violations after delete: {result['violations']}"

    def test_delete_triggers_rebalance(self):
        """Delete from a tree that requires rebalancing after removal."""
        tree = AVLTree()
        for key in [30, 20, 40, 10, 25, 35, 50, 5]:
            tree.insert(key)
        tree.delete(5)
        tree.delete(10)
        result = tree.validate()
        assert result["valid"], f"Tree out of balance: {result['violations']}"


# =========================================================================
# Search
# =========================================================================

class TestAVLSearch:
    def test_search_existing_key(self, sample_avl_tree):
        result = sample_avl_tree.search(30)
        assert result["found"] is True
        assert 30 in result["path"]

    def test_search_nonexistent_key(self, sample_avl_tree):
        result = sample_avl_tree.search(999)
        assert result["found"] is False

    def test_search_empty_tree(self):
        tree = AVLTree()
        result = tree.search(10)
        assert result["found"] is False
        assert result["path"] == []

    def test_search_returns_path(self, sample_avl_tree):
        result = sample_avl_tree.search(25)
        assert result["found"] is True
        assert len(result["path"]) > 0
        # Path should go through root to 25
        assert result["path"][0] == 30


# =========================================================================
# Validation
# =========================================================================

class TestAVLValidation:
    def test_valid_tree_has_no_violations(self, sample_avl_tree):
        result = sample_avl_tree.validate()
        assert result["valid"] is True
        assert len(result["violations"]) == 0

    def test_validate_empty_tree(self):
        tree = AVLTree()
        result = tree.validate()
        assert result["valid"] is True

    def test_validate_detects_bst_violation(self):
        """Manually create a BST violation and check detection."""
        tree = AVLTree()
        tree.insert(10)
        tree.insert(20)
        # Manually corrupt: set left child with larger key
        tree.root.left = tree.root.__class__(key=15, height=1)
        result = tree.validate()
        assert result["valid"] is False
        types = [v["type"] for v in result["violations"]]
        assert "bst_violation" in types

    def test_validate_detects_balance_violation(self):
        tree = AVLTree()
        tree.insert(10)
        # Manually corrupt height to create false balance violation
        tree.insert(5)
        tree.root.right = tree.root.__class__(key=20, height=10)
        tree._update_height(tree.root)
        result = tree.validate()
        assert result["valid"] is False
        types = [v["type"] for v in result["violations"]]
        assert "balance_factor_exceeded" in types or "incorrect_height" in types


# =========================================================================
# Step Recording
# =========================================================================

class TestAVLStepRecording:
    def test_insert_records_steps(self):
        tree = AVLTree()
        result = tree.insert(10)
        assert "log" in result
        assert len(result["log"]) >= 2  # at least "begin" and "result"

    def test_insert_records_rotation_steps(self):
        tree = AVLTree()
        result = tree.insert(10)
        result = tree.insert(20)
        result = tree.insert(30)
        actions = [s["action"] for s in result["log"]]
        assert "rotation" in actions

    def test_delete_records_steps(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(20)
        result = tree.delete(10)
        assert "log" in result
        assert len(result["log"]) >= 2

    def test_search_records_path_steps(self):
        tree = AVLTree()
        [tree.insert(k) for k in [30, 20, 40, 10, 25]]
        result = tree.search(25)
        assert "steps" in result
        assert len(result["steps"]) > 0

    def test_animation_steps_are_built(self):
        tree = AVLTree()
        result = tree.insert(10)
        result = tree.insert(20)
        result = tree.insert(30)
        assert "animation_steps" in result
        assert len(result["animation_steps"]) > 0
        for step in result["animation_steps"]:
            assert "step_number" in step
            assert "description" in step


# =========================================================================
# Export / Serialization
# =========================================================================

class TestAVLExport:
    def test_export_empty_tree(self):
        tree = AVLTree()
        assert tree.export_nested() is None
        assert tree.export_level_order() == []
        adj = tree.export_adjacency()
        assert adj["nodes"] == {}
        assert adj["edges"] == []

    def test_export_nested_structure(self, sample_avl_tree):
        export = sample_avl_tree.export_nested()
        assert export is not None
        assert "key" in export
        assert "height" in export
        assert "balance_factor" in export
        assert "left" in export or "right" in export

    def test_export_level_order(self, sample_avl_tree):
        result = sample_avl_tree.export_level_order()
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) == sample_avl_tree.size()

    def test_export_adjacency(self, sample_avl_tree):
        adj = sample_avl_tree.export_adjacency()
        assert "nodes" in adj
        assert "edges" in adj
        assert len(adj["nodes"]) == sample_avl_tree.size()
        assert len(adj["edges"]) == sample_avl_tree.size() - 1

    def test_export_size_consistency(self, sample_avl_tree):
        nested = sample_avl_tree.export_nested()
        level = sample_avl_tree.export_level_order()
        adj = sample_avl_tree.export_adjacency()
        size = sample_avl_tree.size()
        assert size > 0
        assert len(level["nodes"]) == size
        assert len(adj["nodes"]) == size


# =========================================================================
# Rotation Cases
# =========================================================================

class TestAVLRotations:
    def test_left_rotation(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(20)
        tree.insert(30)
        assert tree.root.key == 20  # 10-20-30 → left rotation at 10

    def test_right_rotation(self):
        tree = AVLTree()
        tree.insert(30)
        tree.insert(20)
        tree.insert(10)
        assert tree.root.key == 20  # 30-20-10 → right rotation at 30

    def test_left_right_rotation(self):
        tree = AVLTree()
        tree.insert(30)
        tree.insert(10)
        tree.insert(20)
        assert tree.root.key == 20

    def test_right_left_rotation(self):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(30)
        tree.insert(20)
        assert tree.root.key == 20

    def test_rotation_enum_values(self):
        assert RotationCase.LL.value == "LL"
        assert RotationCase.RR.value == "RR"
        assert RotationCase.LR.value == "LR"
        assert RotationCase.RL.value == "RL"


# =========================================================================
# Edge Cases
# =========================================================================

class TestAVLEdgeCases:
    def test_large_number_of_inserts(self):
        tree = AVLTree()
        for i in range(1, 101):
            tree.insert(i)
        assert tree.size() == 100
        result = tree.validate()
        assert result["valid"], f"Tree out of balance after 100 inserts: {result['violations']}"
        # Height should be ~log2(100) ≈ 7-8,  allowed up to ~ 1.44*log2(100) ≈ 10
        assert tree._height(tree.root) <= 10, f"Tree too tall: {tree._height(tree.root)}"

    def test_reverse_order_inserts(self):
        tree = AVLTree()
        for i in range(100, 0, -1):
            tree.insert(i)
        result = tree.validate()
        assert result["valid"]

    def test_random_order_inserts(self):
        import random
        tree = AVLTree()
        keys = list(range(1, 51))
        random.shuffle(keys)
        for k in keys:
            tree.insert(k)
        result = tree.validate()
        assert result["valid"]

    def test_insert_then_delete_all(self):
        tree = AVLTree()
        for i in [10, 20, 30, 40, 50]:
            tree.insert(i)
        for i in [10, 20, 30, 40, 50]:
            tree.delete(i)
        assert tree.root is None
        assert tree.size() == 0

    def test_pretty_print_does_not_raise(self, sample_avl_tree):
        output = sample_avl_tree.pretty_print()
        assert isinstance(output, str)
        assert len(output) > 0
