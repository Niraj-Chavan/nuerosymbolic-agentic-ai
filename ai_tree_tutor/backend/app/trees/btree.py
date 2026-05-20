"""
B-Tree Implementation
=====================
A self-balancing tree data structure that maintains sorted data and allows
searches, insertions, and deletions in logarithmic time.
Generalization of a BST where a node can have more than two children.
"""

from __future__ import annotations
from typing import Any, Optional, List, Dict, Tuple


class BTreeNode:
    """A node in the B-Tree."""

    def __init__(self, leaf: bool = True):
        self.keys: List[int] = []
        self.children: List["BTreeNode"] = []
        self.leaf: bool = leaf


class BTree:
    """B-Tree of given order."""

    def __init__(self, order: int = 3):
        self.order = order
        self.t = order  # Keep self.t for backward compatibility / fallback
        self.root = BTreeNode(leaf=True)
        self.operation_log: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------- insert
    def insert(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        if self.search(key).get("found", False):
            self.operation_log.append({"action": "error", "message": f"Key {key} already exists"})
            return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}
        
        res = self._insert(self.root, key)
        if res is not None:
            promoted_key, new_node = res
            new_root = BTreeNode(leaf=False)
            new_root.keys = [promoted_key]
            new_root.children = [self.root, new_node]
            self.root = new_root
            self.operation_log.append({"action": "root_split"})
        
        self.operation_log.append({"action": "insert", "key": key})
        return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}

    def _insert(self, node: BTreeNode, key: int) -> Optional[Tuple[int, BTreeNode]]:
        if node.leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            node.keys.insert(i, key)
            if len(node.keys) > self.order:
                return self._split(node)
            return None
        else:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            res = self._insert(node.children[i], key)
            if res is not None:
                promoted_key, new_child = res
                node.keys.insert(i, promoted_key)
                node.children.insert(i + 1, new_child)
                if len(node.keys) > self.order:
                    return self._split(node)
            return None

    def _split(self, node: BTreeNode) -> Tuple[int, BTreeNode]:
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]
        new_node = BTreeNode(leaf=node.leaf)
        new_node.keys = node.keys[mid + 1:]
        node.keys = node.keys[:mid]
        if not node.leaf:
            new_node.children = node.children[mid + 1:]
            node.children = node.children[:mid + 1]
        self.operation_log.append({
            "action": "split",
            "promoted_key": promoted_key,
        })
        return promoted_key, new_node

    # ---------------------------------------------------------------- delete
    def delete(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        if not self.search(key).get("found", False):
            self.operation_log.append({"action": "error", "message": f"Key {key} does not exist"})
            return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

        deleted = self._delete(self.root, key)
        if len(self.root.keys) == 0 and not self.root.leaf:
            if self.root.children:
                self.root = self.root.children[0]
            else:
                self.root = BTreeNode(leaf=True)
        self.operation_log.append({"action": "delete", "key": key})
        return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

    def _delete(self, node: BTreeNode, key: int) -> bool:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if node.leaf:
            if i < len(node.keys) and node.keys[i] == key:
                node.keys.pop(i)
                return True
            return False

        if i < len(node.keys) and node.keys[i] == key:
            pred = self._get_predecessor(node.children[i])
            node.keys[i] = pred
            deleted = self._delete(node.children[i], pred)
            if not deleted:
                return False
        else:
            deleted = self._delete(node.children[i], key)
            if not deleted:
                return False

        min_keys = self.order // 2
        child = node.children[i]
        if len(child.keys) < min_keys:
            if i > 0 and len(node.children[i - 1].keys) > min_keys:
                self._borrow_left(node, i)
            elif i < len(node.children) - 1 and len(node.children[i + 1].keys) > min_keys:
                self._borrow_right(node, i)
            else:
                if i > 0:
                    self._merge_nodes(node, i - 1)
                else:
                    self._merge_nodes(node, i)
        return True

    def _get_predecessor(self, node: BTreeNode) -> int:
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]

    def _borrow_left(self, parent: BTreeNode, i: int) -> None:
        child = parent.children[i]
        left_sibling = parent.children[i - 1]
        child.keys.insert(0, parent.keys[i - 1])
        parent.keys[i - 1] = left_sibling.keys.pop()
        if not child.leaf:
            child.children.insert(0, left_sibling.children.pop())
        self.operation_log.append({"action": "borrow_left", "index": i})

    def _borrow_right(self, parent: BTreeNode, i: int) -> None:
        child = parent.children[i]
        right_sibling = parent.children[i + 1]
        child.keys.append(parent.keys[i])
        parent.keys[i] = right_sibling.keys.pop(0)
        if not child.leaf:
            child.children.append(right_sibling.children.pop(0))
        self.operation_log.append({"action": "borrow_right", "index": i})

    def _merge_nodes(self, parent: BTreeNode, i: int) -> None:
        left = parent.children[i]
        right = parent.children[i + 1]
        left.keys.append(parent.keys[i])
        left.keys.extend(right.keys)
        if not left.leaf:
            left.children.extend(right.children)
        parent.keys.pop(i)
        parent.children.pop(i + 1)
        self.operation_log.append({"action": "merge", "index": i})

    # ---------------------------------------------------------------- search
    def search(self, key: int) -> Dict[str, Any]:
        path = []
        found = self._search(self.root, key, path)
        return {"operation": "search", "key": key, "found": found, "path": path, "tree": self.export()}

    def _search(self, node: Optional[BTreeNode], key: int, path: List) -> bool:
        if node is None:
            return False
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        path.append({"keys": list(node.keys), "index": i})
        if i < len(node.keys) and node.keys[i] == key:
            return True
        if node.leaf:
            return False
        return self._search(node.children[i], key, path)

    # ---------------------------------------------------------------- export
    def export(self) -> Optional[Dict[str, Any]]:
        if not self.root.keys:
            return None
        return self._export_node(self.root)

    def _export_node(self, node: BTreeNode) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "keys": list(node.keys),
            "leaf": node.leaf,
            "children": [],
        }
        for child in node.children:
            result["children"].append(self._export_node(child))
        return result

    # ------------------------------------------------------------- validation
    def validate(self) -> Dict[str, Any]:
        violations = []
        self._validate_node(self.root, violations, is_root=True)
        return {"valid": len(violations) == 0, "violations": violations, "tree": self.export()}

    def _validate_node(self, node: BTreeNode, violations: List[Dict], is_root: bool = False) -> int:
        order = self.order
        max_keys = order
        min_keys = order // 2 if not is_root else 1

        if len(node.keys) > max_keys:
            violations.append({
                "type": "too_many_keys",
                "keys": list(node.keys),
                "max": max_keys,
                "message": f"Node has {len(node.keys)} keys, max allowed is {max_keys}.",
            })

        if not is_root and len(node.keys) < min_keys and not (is_root and len(node.keys) == 0):
            violations.append({
                "type": "too_few_keys",
                "keys": list(node.keys),
                "min": min_keys,
                "message": f"Non-root node has {len(node.keys)} keys, minimum is {min_keys}.",
            })

        # Keys must be sorted
        for i in range(len(node.keys) - 1):
            if node.keys[i] >= node.keys[i + 1]:
                violations.append({
                    "type": "keys_not_sorted",
                    "keys": list(node.keys),
                    "message": f"Keys {node.keys} are not in sorted order.",
                })
                break

        if not node.leaf:
            if len(node.children) != len(node.keys) + 1:
                violations.append({
                    "type": "wrong_child_count",
                    "keys": list(node.keys),
                    "children_count": len(node.children),
                    "expected": len(node.keys) + 1,
                    "message": f"Node with {len(node.keys)} keys should have {len(node.keys) + 1} children, has {len(node.children)}.",
                })

        depths = []
        for child in node.children:
            d = self._validate_node(child, violations)
            depths.append(d)

        if depths and len(set(depths)) > 1:
            violations.append({
                "type": "unequal_leaf_depth",
                "depths": depths,
                "message": f"Children have unequal depths: {depths}. All leaves must be at the same level.",
            })

        return (depths[0] + 1) if depths else 0
