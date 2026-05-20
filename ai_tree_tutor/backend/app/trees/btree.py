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
    """B-Tree of given order (minimum degree t)."""

    def __init__(self, t: int = 3):
        self.t = t  # minimum degree
        self.root = BTreeNode(leaf=True)
        self.operation_log: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------- insert
    def insert(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        root = self.root
        if len(root.keys) == 2 * self.t - 1:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
            self.operation_log.append({"action": "root_split"})
        self._insert_non_full(self.root, key)
        self.operation_log.append({"action": "insert", "key": key})
        return {"operation": "insert", "key": key, "tree": self.export(), "log": self.operation_log}

    def _split_child(self, parent: BTreeNode, i: int) -> None:
        t = self.t
        child = parent.children[i]
        new_node = BTreeNode(leaf=child.leaf)
        mid_key = child.keys[t - 1]

        parent.keys.insert(i, mid_key)
        parent.children.insert(i + 1, new_node)

        new_node.keys = child.keys[t:]
        child.keys = child.keys[:t - 1]

        if not child.leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]

        self.operation_log.append({
            "action": "split",
            "promoted_key": mid_key,
        })

    def _insert_non_full(self, node: BTreeNode, key: int) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(0)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key)

    # ---------------------------------------------------------------- delete
    def delete(self, key: int) -> Dict[str, Any]:
        self.operation_log = []
        self._delete(self.root, key)
        if len(self.root.keys) == 0 and not self.root.leaf:
            self.root = self.root.children[0]
        self.operation_log.append({"action": "delete", "key": key})
        return {"operation": "delete", "key": key, "tree": self.export(), "log": self.operation_log}

    def _delete(self, node: BTreeNode, key: int) -> None:
        t = self.t
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if node.leaf:
            if i < len(node.keys) and node.keys[i] == key:
                node.keys.pop(i)
            else:
                self.operation_log.append({"action": "not_found", "key": key})
            return

        if i < len(node.keys) and node.keys[i] == key:
            if len(node.children[i].keys) >= t:
                pred = self._get_predecessor(node.children[i])
                node.keys[i] = pred
                self._delete(node.children[i], pred)
            elif len(node.children[i + 1].keys) >= t:
                succ = self._get_successor(node.children[i + 1])
                node.keys[i] = succ
                self._delete(node.children[i + 1], succ)
            else:
                self._merge(node, i)
                self._delete(node.children[i], key)
        else:
            if i < len(node.children) and len(node.children[i].keys) < t:
                self._fill(node, i)
                if i > len(node.keys):
                    i -= 1
            if i < len(node.children):
                self._delete(node.children[i], key)

    def _get_predecessor(self, node: BTreeNode) -> int:
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]

    def _get_successor(self, node: BTreeNode) -> int:
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def _merge(self, node: BTreeNode, i: int) -> None:
        child = node.children[i]
        sibling = node.children[i + 1]
        child.keys.append(node.keys[i])
        child.keys.extend(sibling.keys)
        if not child.leaf:
            child.children.extend(sibling.children)
        node.keys.pop(i)
        node.children.pop(i + 1)
        self.operation_log.append({"action": "merge", "index": i})

    def _fill(self, node: BTreeNode, i: int) -> None:
        t = self.t
        if i > 0 and len(node.children[i - 1].keys) >= t:
            self._borrow_from_prev(node, i)
        elif i < len(node.children) - 1 and len(node.children[i + 1].keys) >= t:
            self._borrow_from_next(node, i)
        else:
            if i < len(node.children) - 1:
                self._merge(node, i)
            else:
                self._merge(node, i - 1)

    def _borrow_from_prev(self, node: BTreeNode, i: int) -> None:
        child = node.children[i]
        sibling = node.children[i - 1]
        child.keys.insert(0, node.keys[i - 1])
        node.keys[i - 1] = sibling.keys.pop()
        if not child.leaf:
            child.children.insert(0, sibling.children.pop())

    def _borrow_from_next(self, node: BTreeNode, i: int) -> None:
        child = node.children[i]
        sibling = node.children[i + 1]
        child.keys.append(node.keys[i])
        node.keys[i] = sibling.keys.pop(0)
        if not child.leaf:
            child.children.append(sibling.children.pop(0))

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
        t = self.t
        max_keys = 2 * t - 1
        min_keys = t - 1 if not is_root else 1

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
