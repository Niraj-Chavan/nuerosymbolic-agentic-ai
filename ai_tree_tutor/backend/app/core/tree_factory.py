"""
Tree Factory — Registry Pattern
=================================
Decoupled tree instance management.
Removes the if/elif chain for step recorder dispatch and validator dispatch
by centralising tree type → constructor mappings.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.trees.avl import AVLTree
from app.trees.red_black import RedBlackTree
from app.trees.heap import BinaryHeap
from app.trees.segment_tree import SegmentTree
from app.trees.btree import BTree
from app.trees.bplus_tree import BPlusTree

# Tree constructor registry
TreeFactory = Callable[..., Any]

_REGISTRY: Dict[str, TreeFactory] = {
    "avl": lambda **kw: AVLTree(),
    "red_black": lambda **kw: RedBlackTree(),
    "heap": lambda **kw: BinaryHeap(heap_type=kw.get("heap_type", "min")),
    "segment_tree": lambda **kw: SegmentTree(data=kw.get("data", [])),
    "btree": lambda **kw: BTree(order=kw.get("order", 3)),
    "bplus_tree": lambda **kw: BPlusTree(order=kw.get("order", 4)),
}

SUPPORTED_TREES: List[str] = list(_REGISTRY.keys())
SUPPORTED_OPERATIONS: List[str] = ["insert", "delete", "search"]


def register(tree_type: str, factory: TreeFactory) -> None:
    """Register a new tree type at runtime."""
    _REGISTRY[tree_type] = factory


def create(tree_type: str, **kwargs) -> Any:
    """Create a new tree instance by type."""
    factory = _REGISTRY.get(tree_type)
    if factory is None:
        raise ValueError(f"Unknown tree type: {tree_type}. Supported: {list(_REGISTRY)}")
    return factory(**kwargs)


def is_supported(tree_type: str) -> bool:
    return tree_type in _REGISTRY


def supported_trees() -> List[str]:
    return list(SUPPORTED_TREES)


def supported_operations() -> List[str]:
    return list(SUPPORTED_OPERATIONS)
