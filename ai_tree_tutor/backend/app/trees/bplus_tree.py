"""
B+ Tree Implementation
=======================
Variant of B-Tree where all data records are stored at the leaf level
and leaf nodes are linked for efficient range queries.
"""

from __future__ import annotations
from typing import Any, Optional, List, Dict


class BPlusLeaf:
    """Leaf node of a B+ Tree."""

    def __init__(self):
        self.keys: List[int] = []
        self.next: Optional["BPlusLeaf"] = None  # linked list pointer


class BPlusInternal:
    """Internal node of a B+ Tree."""

    def __init__(self):
        self.keys: List[int] = []
        self.children: List[Any] = []  # BPlusInternal | BPlusLeaf


class BPlusTree:
    """B+ Tree of given order."""

    def __init__(self, order: int = 4):
        self.order = order
        self.root: Any = BPlusLeaf()
        self.operation_log: List[Dict[str, Any]] = []

    def _is_leaf(self, node) -> bool:
        return isinstance(node, BPlusLeaf)

    # ---------------------------------------------------------------- insert
    def insert(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        if self.search(key).get("found", False):
            self.operation_log.append({"action": "error", "message": f"Key {key} already exists"})
            return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}
        result = self._insert(self.root, key)
        if result is not None:
            new_root = BPlusInternal()
            new_root.keys = [result[0]]
            new_root.children = [self.root, result[1]]
            self.root = new_root
            self.operation_log.append({"action": "new_root", "key": result[0]})
        self.operation_log.append({"action": "insert", "key": key})
        return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}

    def _insert(self, node, key: int):
        if self._is_leaf(node):
            self._insert_into_leaf(node, key)
            if len(node.keys) > self.order:
                return self._split_leaf(node)
            return None
        else:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            result = self._insert(node.children[i], key)
            if result is not None:
                node.keys.insert(i, result[0])
                node.children.insert(i + 1, result[1])
                if len(node.keys) > self.order:
                    return self._split_internal(node)
            return None

    def _insert_into_leaf(self, leaf: BPlusLeaf, key: int) -> None:
        i = 0
        while i < len(leaf.keys) and key > leaf.keys[i]:
            i += 1
        leaf.keys.insert(i, key)

    def _split_leaf(self, leaf: BPlusLeaf):
        mid = len(leaf.keys) // 2
        new_leaf = BPlusLeaf()
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.next = leaf.next
        leaf.keys = leaf.keys[:mid]
        leaf.next = new_leaf
        self.operation_log.append({"action": "split_leaf", "promoted": new_leaf.keys[0]})
        return (new_leaf.keys[0], new_leaf)

    def _split_internal(self, node: BPlusInternal):
        mid = len(node.keys) // 2
        promoted = node.keys[mid]
        new_internal = BPlusInternal()
        new_internal.keys = node.keys[mid + 1:]
        new_internal.children = node.children[mid + 1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        self.operation_log.append({"action": "split_internal", "promoted": promoted})
        return (promoted, new_internal)

    # ---------------------------------------------------------------- delete
    def delete(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        self._delete(self.root, key)
        if not self._is_leaf(self.root) and len(self.root.keys) == 0:
            self.root = self.root.children[0] if self.root.children else BPlusLeaf()
        self.operation_log.append({"action": "delete", "key": key})
        return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

    def _delete(self, node, key: int) -> bool:
        if self._is_leaf(node):
            if key in node.keys:
                node.keys.remove(key)
                return True
            self.operation_log.append({"action": "not_found", "key": key})
            return False

        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1

        deleted = self._delete(node.children[i], key)
        if not deleted:
            return False

        min_keys = self.order // 2
        child = node.children[i]
        child_key_count = len(child.keys)

        if child_key_count < min_keys:
            # Try borrow from left sibling
            if i > 0 and len(node.children[i - 1].keys) > min_keys:
                self._borrow_left(node, i)
            # Try borrow from right sibling
            elif i < len(node.children) - 1 and len(node.children[i + 1].keys) > min_keys:
                self._borrow_right(node, i)
            # Merge
            else:
                if i > 0:
                    self._merge_nodes(node, i - 1)
                elif i < len(node.children) - 1:
                    self._merge_nodes(node, i)

        # Update internal key if needed
        if i < len(node.keys) and not self._is_leaf(node.children[i + 1]):
            pass  # simplified
        elif i < len(node.keys) and self._is_leaf(node.children[i + 1]):
            if node.children[i + 1].keys:
                node.keys[i] = node.children[i + 1].keys[0]

        return True

    def _borrow_left(self, parent, i):
        child = parent.children[i]
        left_sibling = parent.children[i - 1]
        if self._is_leaf(child):
            borrowed = left_sibling.keys.pop()
            child.keys.insert(0, borrowed)
            parent.keys[i - 1] = child.keys[0]
        else:
            child.keys.insert(0, parent.keys[i - 1])
            parent.keys[i - 1] = left_sibling.keys.pop()
            if left_sibling.children:
                child.children.insert(0, left_sibling.children.pop())

    def _borrow_right(self, parent, i):
        child = parent.children[i]
        right_sibling = parent.children[i + 1]
        if self._is_leaf(child):
            borrowed = right_sibling.keys.pop(0)
            child.keys.append(borrowed)
            parent.keys[i] = right_sibling.keys[0] if right_sibling.keys else borrowed
        else:
            child.keys.append(parent.keys[i])
            parent.keys[i] = right_sibling.keys.pop(0)
            if right_sibling.children:
                child.children.append(right_sibling.children.pop(0))

    def _merge_nodes(self, parent, i):
        left = parent.children[i]
        right = parent.children[i + 1]
        if self._is_leaf(left):
            left.keys.extend(right.keys)
            left.next = right.next
        else:
            left.keys.append(parent.keys[i])
            left.keys.extend(right.keys)
            left.children.extend(right.children)
        parent.keys.pop(i)
        parent.children.pop(i + 1)
        self.operation_log.append({"action": "merge", "index": i})

    # ---------------------------------------------------------------- search
    def search(self, key: int) -> Dict[str, Any]:
        path = []
        found = self._search(self.root, key, path)
        return {"operation": "search", "key": key, "found": found, "path": path, "tree": self.export()}

    def _search(self, node, key: int, path: List) -> bool:
        path.append({"keys": list(node.keys), "leaf": self._is_leaf(node)})
        if self._is_leaf(node):
            return key in node.keys
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._search(node.children[i], key, path)

    # ---------------------------------------------------------------- export
    def export(self) -> Optional[Dict[str, Any]]:
        if self._is_leaf(self.root) and not self.root.keys:
            return None
        return self._export_node(self.root)

    def _export_node(self, node) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "keys": list(node.keys),
            "leaf": self._is_leaf(node),
        }
        if not self._is_leaf(node):
            result["children"] = [self._export_node(c) for c in node.children]
        else:
            result["children"] = []
            result["has_next"] = node.next is not None
        return result

    # ------------------------------------------------------------- validation
    def validate(self) -> Dict[str, Any]:
        violations = []
        self._validate_node(self.root, violations, is_root=True)
        # Check leaf linkage
        self._validate_leaf_linkage(violations)
        return {"valid": len(violations) == 0, "violations": violations, "tree": self.export()}

    def _validate_node(self, node, violations: List[Dict], is_root: bool = False) -> int:
        max_keys = self.order
        min_keys = self.order // 2 if not is_root else 1

        if not (is_root and self._is_leaf(node) and len(node.keys) == 0):
            if len(node.keys) > max_keys:
                violations.append({
                    "type": "too_many_keys",
                    "keys": list(node.keys),
                    "max": max_keys,
                    "message": f"Node has {len(node.keys)} keys, max is {max_keys}.",
                })

        for i in range(len(node.keys) - 1):
            if node.keys[i] >= node.keys[i + 1]:
                violations.append({
                    "type": "keys_not_sorted",
                    "keys": list(node.keys),
                    "message": f"Keys are not sorted: {node.keys}.",
                })
                break

        if self._is_leaf(node):
            return 0

        if len(node.children) != len(node.keys) + 1:
            violations.append({
                "type": "wrong_child_count",
                "keys": list(node.keys),
                "children_count": len(node.children),
                "message": f"Internal node with {len(node.keys)} keys should have {len(node.keys) + 1} children.",
            })

        depths = []
        for child in node.children:
            d = self._validate_node(child, violations)
            depths.append(d)

        if depths and len(set(depths)) > 1:
            violations.append({
                "type": "unequal_leaf_depth",
                "depths": depths,
                "message": f"Leaves at unequal depths: {depths}.",
            })

        return (depths[0] + 1) if depths else 0

    def _validate_leaf_linkage(self, violations: List[Dict]) -> None:
        leaves = []
        self._collect_leaves(self.root, leaves)
        for i in range(len(leaves) - 1):
            if leaves[i].next is not leaves[i + 1]:
                violations.append({
                    "type": "broken_leaf_linkage",
                    "index": i,
                    "message": f"Leaf {i} (keys={leaves[i].keys}) does not link to leaf {i + 1}.",
                })

    def _collect_leaves(self, node, leaves: List) -> None:
        if self._is_leaf(node):
            leaves.append(node)
            return
        for child in node.children:
            self._collect_leaves(child, leaves)
