"""
Production-Level AVL Tree Implementation
=========================================
Self-balancing binary search tree where the balance factor
(height difference of left and right subtrees) of every node is at most 1.

Maintains O(log n) height guarantee through rotations after every
insertion and deletion.

Designed for the Neuro-Symbolic AI Tutoring System with:
- Step-by-step operation recording for frontend animation
- Visualization-friendly JSON serialization (level-order + adjacency list)
- Concept-tagged violations for symbolic validation integration
- Educational metadata on every state change
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RotationCase(Enum):
    """The four AVL rebalancing cases."""
    LL = "LL"       # Left-Left: single right rotation
    RR = "RR"       # Right-Right: single left rotation
    LR = "LR"       # Left-Right: left then right rotation
    RL = "RL"       # Right-Left: right then left rotation


class ViolationType(Enum):
    """AVL invariant violation types for symbolic validation."""
    BALANCE_EXCEEDED = "balance_factor_exceeded"
    HEIGHT_INCORRECT = "incorrect_height"
    BST_ORDERING = "bst_violation"


@dataclass
class AVLNode:
    """A node in the AVL tree."""
    key: int
    left: Optional["AVLNode"] = None
    right: Optional["AVLNode"] = None
    height: int = 1


@dataclass
class OperationStep:
    """A single recorded step during a tree operation."""
    action: str           # "compare", "insert", "update_height", "rotation", "result"
    node_keys: list[int]  # Affected node keys
    description: str      # Human-readable description
    why: str              # Educational explanation of WHY this step occurs
    concept_tag: str      # Maps to KnowledgeGraph concept node
    tree_state: Optional[dict] = None  # Snapshot at this point


@dataclass
class OperationResult:
    """Complete result of a tree operation."""
    operation: str
    key: int
    found: bool = True
    tree: Optional[dict] = None
    steps: list[OperationStep] = field(default_factory=list)
    violations: list[dict] = field(default_factory=list)
    summary: str = ""


class AVLTree:
    """
    AVL (Adelson-Velsky and Landis) Self-Balancing Binary Search Tree.

    Invariants:
    1. BST ordering: left subtree keys < node key < right subtree keys
    2. Balance: |height(left) - height(right)| <= 1 for every node
    3. Height: node.height = 1 + max(height(left), height(right))
    """

    def __init__(self):
        self.root: Optional[AVLNode] = None
        self._steps: list[OperationStep] = []
        self._capture_states: bool = False  # Enable tree snapshots per step

    # ================================================================
    # Helper methods
    # ================================================================

    @staticmethod
    def _height(node: Optional[AVLNode]) -> int:
        """Return the height of a node; 0 for None."""
        return node.height if node else 0

    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        """
        Balance factor = height(left subtree) - height(right subtree).

        Positive BF  => left-heavy
        Negative BF  => right-heavy
        |BF| > 1     => violation (requires rotation)
        """
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _update_height(self, node: AVLNode) -> None:
        """
        Recompute node height from children.
        Height is defined as the number of edges on the longest
        path from this node down to a leaf.
        """
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    # ================================================================
    # Rotation methods
    # ================================================================

    def _rotate_right(self, z: AVLNode, case: RotationCase = RotationCase.LL) -> AVLNode:
        r"""
        Right rotation (LL case)::

             z               y
            / \             / \
           y   T3   =>     x   z
          / \      <—        / \
         x   T2             T1  T2

        Applied when z is left-heavy (BF > 1) and y is left-heavy or balanced.
        The left child y becomes the new subtree root.
        """
        y = z.left
        t3 = y.right

        # Perform rotation
        y.right = z
        z.left = t3

        # Heights MUST be updated bottom-up: z first (now child), then y (now parent)
        self._update_height(z)
        self._update_height(y)

        self._steps.append(OperationStep(
            action="rotation",
            node_keys=[y.key, z.key],
            description=f"Right rotation at node {z.key} (case: {case.value})",
            why=(
                f"Node {z.key} is left-heavy (BF={self._balance_factor(z) if z != y else 'N/A'}). "
                f"A right rotation makes {y.key} the new root, reducing the height difference."
            ),
            concept_tag="avl_rotation_ll",
        ))
        return y

    def _rotate_left(self, z: AVLNode, case: RotationCase = RotationCase.RR) -> AVLNode:
        r"""
        Left rotation (RR case)::

           z                 y
          / \               / \
         T1  y      =>     z   x
            / \           / \
           T2  x         T1  T2

        Applied when z is right-heavy (BF < -1) and y is right-heavy or balanced.
        The right child y becomes the new subtree root.
        """
        y = z.right
        t2 = y.left

        # Perform rotation
        y.left = z
        z.right = t2

        # Update heights bottom-up
        self._update_height(z)
        self._update_height(y)

        self._steps.append(OperationStep(
            action="rotation",
            node_keys=[y.key, z.key],
            description=f"Left rotation at node {z.key} (case: {case.value})",
            why=(
                f"Node {z.key} is right-heavy (BF={self._balance_factor(z) if z != y else 'N/A'}). "
                f"A left rotation makes {y.key} the new root, reducing the height difference."
            ),
            concept_tag="avl_rotation_rr",
        ))
        return y

    # ================================================================
    # Rebalancing (determines which rotation case applies)
    # ================================================================

    def _rebalance(self, node: AVLNode, inserted_key: Optional[int] = None) -> AVLNode:
        """
        Check balance factor at node and apply the correct rotation case.

        This is called during both insert (using inserted_key to disambiguate
        LL vs LR, RR vs RL) and delete (using child's BF to disambiguate).
        """
        self._update_height(node)
        balance = self._balance_factor(node)

        # ---------- Left-heavy (BF > 1) ----------
        if balance > 1:
            if inserted_key is not None:
                # Insert path: use key comparison to determine case
                if inserted_key < node.left.key:
                    return self._rotate_right(node, RotationCase.LL)
                else:
                    # LR case: first left-rotate left child, then right-rotate node
                    self._steps.append(OperationStep(
                        action="rotation",
                        node_keys=[node.left.key, node.key],
                        description=f"LR case: preparing left child of {node.key} for double rotation",
                        why=(
                            f"The inserted key went into the RIGHT subtree of the LEFT child of {node.key}. "
                            f"This zig-zag pattern requires a left rotation on the left child first to "
                            f"convert it into a zig-zig (LL) pattern."
                        ),
                        concept_tag="avl_rotation_lr",
                    ))
                    node.left = self._rotate_left(node.left, RotationCase.LR)
                    return self._rotate_right(node, RotationCase.LR)
            else:
                # Delete path: use left child's BF to disambiguate
                left_bf = self._balance_factor(node.left)
                if left_bf >= 0:
                    return self._rotate_right(node, RotationCase.LL)
                else:
                    self._steps.append(OperationStep(
                        action="rotation",
                        node_keys=[node.left.key, node.key],
                        description=f"LR case (during delete): double rotation at {node.key}",
                        why=(
                            f"After deletion, node {node.key} is left-heavy, but its left child "
                            f"is right-heavy. A left rotation on the left child converts this to "
                            f"LL, then a right rotation on {node.key} completes the rebalance."
                        ),
                        concept_tag="avl_rotation_lr",
                    ))
                    node.left = self._rotate_left(node.left, RotationCase.LR)
                    return self._rotate_right(node, RotationCase.LR)

        # ---------- Right-heavy (BF < -1) ----------
        if balance < -1:
            if inserted_key is not None:
                # Insert path
                if inserted_key > node.right.key:
                    return self._rotate_left(node, RotationCase.RR)
                else:
                    # RL case: first right-rotate right child, then left-rotate node
                    self._steps.append(OperationStep(
                        action="rotation",
                        node_keys=[node.right.key, node.key],
                        description=f"RL case: preparing right child of {node.key} for double rotation",
                        why=(
                            f"The inserted key went into the LEFT subtree of the RIGHT child of {node.key}. "
                            f"This zig-zag pattern requires a right rotation on the right child first to "
                            f"convert it into a zig-zig (RR) pattern."
                        ),
                        concept_tag="avl_rotation_rl",
                    ))
                    node.right = self._rotate_right(node.right, RotationCase.RL)
                    return self._rotate_left(node, RotationCase.RL)
            else:
                # Delete path: use right child's BF to disambiguate
                right_bf = self._balance_factor(node.right)
                if right_bf <= 0:
                    return self._rotate_left(node, RotationCase.RR)
                else:
                    self._steps.append(OperationStep(
                        action="rotation",
                        node_keys=[node.right.key, node.key],
                        description=f"RL case (during delete): double rotation at {node.key}",
                        why=(
                            f"After deletion, node {node.key} is right-heavy, but its right child "
                            f"is left-heavy. A right rotation on the right child converts this to "
                            f"RR, then a left rotation on {node.key} completes the rebalance."
                        ),
                        concept_tag="avl_rotation_rl",
                    ))
                    node.right = self._rotate_right(node.right, RotationCase.RL)
                    return self._rotate_left(node, RotationCase.RL)

        return node

    # ================================================================
    # Insert
    # ================================================================

    def insert(self, key: int) -> dict[str, Any]:
        """
        Insert a key into the AVL tree.

        Algorithm:
        1. Standard BST insert (recursive, O(log n) path)
        2. Update heights on the way back up
        3. Check balance factors; rotate if |BF| > 1

        Returns a dict with operation metadata, tree export, and step log.
        """
        self._steps = []

        self._steps.append(OperationStep(
            action="insert",
            node_keys=[key],
            description=f"Begin AVL insert: key = {key}",
            why="Insertion follows BST ordering first, then fixes any balance violations.",
            concept_tag="avl_insert",
            tree_state=self._capture_snapshot(),
        ))

        self.root = self._insert(self.root, key)

        self._steps.append(OperationStep(
            action="result",
            node_keys=[],
            description=f"Insert of {key} complete. Tree height = {self._height(self.root)}.",
            why="All nodes on the insertion path have been checked and rebalanced.",
            concept_tag="avl_insert",
            tree_state=self._capture_snapshot(),
        ))

        return self._build_result("insert", key)

    def _insert(self, node: Optional[AVLNode], key: int) -> AVLNode:
        """
        Recursive AVL insert.

        On the way DOWN: traverse BST path.
        On the way UP:  update heights, check balance, rotate if needed.
        """
        if not node:
            self._steps.append(OperationStep(
                action="insert",
                node_keys=[key],
                description=f"Found empty position → create new node {key} (height=1)",
                why=f"Key {key} belongs here based on BST ordering from the traversal path.",
                concept_tag="avl_insert",
            ))
            return AVLNode(key=key)

        # BST comparison step
        self._steps.append(OperationStep(
            action="compare",
            node_keys=[key, node.key],
            description=f"Compare {key} with {node.key}",
            why=f"BST rule: {key} {'<' if key < node.key else '>'} {node.key}, so go {'LEFT' if key < node.key else 'RIGHT'}.",
            concept_tag="binary_search_property",
        ))

        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} already exists — no duplicate insertion",
                why="AVL trees maintain unique keys to preserve BST invariants.",
                concept_tag="avl_insert",
            ))
            return node

        # Rebalance on the way up
        return self._rebalance(node, inserted_key=key)

    # ================================================================
    # Delete
    # ================================================================

    def delete(self, key: int) -> dict[str, Any]:
        """
        Delete a key from the AVL tree.

        Algorithm:
        1. Standard BST delete (0, 1, or 2 children cases)
        2. Update heights on the way back up
        3. Check balance factors; rotate if |BF| > 1

        Returns a dict with operation metadata, tree export, and step log.
        """
        self._steps = []

        self._steps.append(OperationStep(
            action="insert",  # "delete" for action type
            node_keys=[key],
            description=f"Begin AVL delete: key = {key}",
            why="Deletion removes the node then rebalances the tree from the deletion point upward.",
            concept_tag="avl_delete",
            tree_state=self._capture_snapshot(),
        ))

        self.root = self._delete(self.root, key)

        self._steps.append(OperationStep(
            action="result",
            node_keys=[],
            description=f"Delete of {key} complete.",
            why="All nodes on the path from deletion point to root have been checked and rebalanced.",
            concept_tag="avl_delete",
            tree_state=self._capture_snapshot(),
        ))

        return self._build_result("delete", key)

    def _min_value_node(self, node: AVLNode) -> AVLNode:
        """Find the in-order successor (leftmost node in subtree)."""
        current = node
        while current.left:
            current = current.left
        return current

    def _delete(self, node: Optional[AVLNode], key: int) -> Optional[AVLNode]:
        """Recursive AVL delete."""
        if not node:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} not found in tree",
                why="Reached a null node — the key does not exist.",
                concept_tag="avl_delete",
            ))
            return node

        # Search for the key
        if key < node.key:
            self._steps.append(OperationStep(
                action="compare",
                node_keys=[key, node.key],
                description=f"{key} < {node.key} → search LEFT",
                why="BST ordering: keys smaller than node.key are in the left subtree.",
                concept_tag="binary_search_property",
            ))
            node.left = self._delete(node.left, key)
        elif key > node.key:
            self._steps.append(OperationStep(
                action="compare",
                node_keys=[key, node.key],
                description=f"{key} > {node.key} → search RIGHT",
                why="BST ordering: keys larger than node.key are in the right subtree.",
                concept_tag="binary_search_property",
            ))
            node.right = self._delete(node.right, key)
        else:
            # Found the node to delete
            self._steps.append(OperationStep(
                action="insert",  # deletion action
                node_keys=[key],
                description=f"Found node {key} — removing it",
                why="This is the deletion target. We handle three cases: 0, 1, or 2 children.",
                concept_tag="avl_delete",
            ))

            # Case 1: No left child (0 or 1 child)
            if not node.left:
                self._steps.append(OperationStep(
                    action="insert",
                    node_keys=[key],
                    description=f"Node {key} has no left child → replace with right subtree",
                    why="With 0 or 1 child, the non-null child (if any) simply takes this node's place.",
                    concept_tag="avl_delete",
                ))
                return node.right

            # Case 2: No right child
            if not node.right:
                self._steps.append(OperationStep(
                    action="insert",
                    node_keys=[key],
                    description=f"Node {key} has no right child → replace with left subtree",
                    why="With only a left child, that child takes this node's place.",
                    concept_tag="avl_delete",
                ))
                return node.left

            # Case 3: Two children — replace with in-order successor
            successor = self._min_value_node(node.right)
            self._steps.append(OperationStep(
                action="insert",
                node_keys=[key, successor.key],
                description=f"Node {key} has 2 children → replace with in-order successor {successor.key}",
                why=(
                    f"The in-order successor ({successor.key}, smallest in the right subtree) "
                    f"is the next key in sorted order after {key}. Replacing with it maintains "
                    f"BST ordering while removing the target."
                ),
                concept_tag="avl_delete",
            ))
            node.key = successor.key
            node.right = self._delete(node.right, successor.key)

        # Rebalance on the way up (delete path — uses child BF for disambiguation)
        return self._rebalance(node, inserted_key=None)

    # ================================================================
    # Search
    # ================================================================

    def search(self, key: int) -> dict[str, Any]:
        """
        Search for a key in the AVL tree.
        Returns the path taken and whether the key was found.
        """
        self._steps = []
        path: list[int] = []
        found = self._search(self.root, key, path)

        return {
            "operation": "search",
            "key": key,
            "found": found,
            "path": path,
            "steps": [s.__dict__ for s in self._steps],
            "tree": self.export_nested(),
        }

    def _search(self, node: Optional[AVLNode], key: int, path: list[int]) -> bool:
        """Recursive BST search with step recording."""
        if not node:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} not found — reached empty position",
                why="The search path ended at a null node, meaning the key is not in the tree.",
                concept_tag="binary_search_property",
            ))
            return False

        path.append(node.key)
        self._steps.append(OperationStep(
            action="compare",
            node_keys=[key, node.key],
            description=f"Compare {key} with {node.key}",
            why=f"Following BST: go {'LEFT' if key < node.key else 'RIGHT' if key > node.key else 'FOUND'}.",
            concept_tag="binary_search_property",
        ))

        if key == node.key:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} found at depth {len(path)}",
                why=f"Search terminated after {len(path)} comparisons.",
                concept_tag="binary_search_property",
            ))
            return True
        elif key < node.key:
            return self._search(node.left, key, path)
        else:
            return self._search(node.right, key, path)

    # ================================================================
    # Export / Serialization (for D3 frontend visualization)
    # ================================================================

    def _capture_snapshot(self) -> Optional[dict]:
        """Capture current tree state as a D3-friendly nested dict."""
        return self.export_nested()

    def export_nested(self) -> Optional[dict[str, Any]]:
        """
        Export the tree as a nested dict (hierarchical format).
        Used by D3 tree layouts (tree, cluster).
        """
        return self._export_node(self.root)

    def _export_node(self, node: Optional[AVLNode]) -> Optional[dict[str, Any]]:
        if not node:
            return None
        bf = self._balance_factor(node)
        left = self._export_node(node.left)
        right = self._export_node(node.right)
        return {
            "key": node.key,
            "value": node.key,
            "height": node.height,
            "balance_factor": bf,
            "is_balanced": abs(bf) <= 1,
            "left": left,
            "right": right,
            "children": [child for child in (left, right) if child is not None],
        }

    def export_level_order(self) -> list[dict[str, Any]]:
        """
        Export the tree in level-order (BFS) as a flat array.
        Used by D3 force-directed or layered layouts.

        Each entry includes parent reference for edge drawing.
        """
        if not self.root:
            return []

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        queue: list[tuple[AVLNode, Optional[int], int, int]] = [(self.root, None, 0, 0)]
        # (node, parent_key, depth, index_in_level)

        while queue:
            node, parent_key, depth, idx = queue.pop(0)
            bf = self._balance_factor(node)

            nodes.append({
                "key": node.key,
                "depth": depth,
                "height": node.height,
                "balance_factor": bf,
                "is_balanced": abs(bf) <= 1,
                "parent": parent_key,
            })

            if parent_key is not None:
                edges.append({"source": parent_key, "target": node.key})

            if node.left:
                queue.append((node.left, node.key, depth + 1, idx * 2))
            if node.right:
                queue.append((node.right, node.key, depth + 1, idx * 2 + 1))

        return {"nodes": nodes, "edges": edges, "height": self._height(self.root)}

    def export_adjacency(self) -> dict[str, Any]:
        """
        Export as adjacency list + node properties.
        Used for graph-based layouts and validation.
        """
        if not self.root:
            return {"nodes": {}, "edges": []}

        nodes: dict[int, dict] = {}
        edges: list[tuple[int, int]] = []
        self._build_adjacency(self.root, nodes, edges)

        return {"nodes": nodes, "edges": edges}

    def export(self) -> Optional[dict[str, Any]]:
        """Backwards-compatible alias for export_nested()."""
        return self.export_nested()

    def _build_adjacency(
        self,
        node: Optional[AVLNode],
        nodes: dict[int, dict],
        edges: list[tuple[int, int]],
    ) -> None:
        if not node:
            return
        bf = self._balance_factor(node)
        nodes[node.key] = {
            "height": node.height,
            "balance_factor": bf,
            "is_balanced": abs(bf) <= 1,
        }
        if node.left:
            edges.append((node.key, node.left.key))
            self._build_adjacency(node.left, nodes, edges)
        if node.right:
            edges.append((node.key, node.right.key))
            self._build_adjacency(node.right, nodes, edges)

    # ================================================================
    # Validation (for symbolic validation engine integration)
    # ================================================================

    def validate(self) -> dict[str, Any]:
        """
        Validate all AVL invariants and return a detailed report.

        Checks:
        1. BST ordering (left < node < right for every node)
        2. Balance factor: |BF| <= 1 for every node
        3. Height consistency: height = 1 + max(left_height, right_height)

        Each violation includes a concept_tag for KG mapping and severity.
        """
        violations: list[dict] = []
        self._validate_node(self.root, violations)

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "tree": self.export_nested(),
        }

    def _validate_node(
        self,
        node: Optional[AVLNode],
        violations: list[dict],
        lo: float = float("-inf"),
        hi: float = float("inf"),
    ) -> None:
        if not node:
            return

        # --- Check BST ordering ---
        if node.key <= lo or node.key >= hi:
            violations.append({
                "type": ViolationType.BST_ORDERING.value,
                "rule_id": "AVL-001",
                "node": node.key,
                "severity": "high",
                "message": (
                    f"Node {node.key} violates BST ordering. "
                    f"It must be in range ({lo}, {hi})."
                ),
                "concept_tag": "binary_search_property",
            })

        # --- Check balance factor ---
        bf = self._balance_factor(node)
        if abs(bf) > 1:
            violations.append({
                "type": ViolationType.BALANCE_EXCEEDED.value,
                "rule_id": "AVL-002",
                "node": node.key,
                "balance_factor": bf,
                "severity": "high",
                "message": (
                    f"Node {node.key} has balance factor {bf} "
                    f"(must be -1, 0, or 1)."
                ),
                "concept_tag": "balance_factor_invariant",
            })

        # --- Check height consistency ---
        expected_height = 1 + max(self._height(node.left), self._height(node.right))
        if node.height != expected_height:
            violations.append({
                "type": ViolationType.HEIGHT_INCORRECT.value,
                "rule_id": "AVL-003",
                "node": node.key,
                "expected_height": expected_height,
                "actual_height": node.height,
                "severity": "medium",
                "message": (
                    f"Node {node.key} has height {node.height}, "
                    f"expected {expected_height}."
                ),
                "concept_tag": "height_definition",
            })

        # Recurse into subtrees with updated bounds
        new_lo = lo if node.key <= lo else node.key
        new_hi = hi if node.key >= hi else node.key
        self._validate_node(node.left, violations, lo, new_hi)
        self._validate_node(node.right, violations, new_lo, hi)

    # ================================================================
    # Internal result builder
    # ================================================================

    def _build_result(self, operation: str, key: int) -> dict[str, Any]:
        """Build the operation result dict consumed by agents."""
        return {
            "operation": operation,
            "key": key,
            "found": True,
            "tree": self.export_nested(),
            "level_order": self.export_level_order(),
            "log": [s.__dict__ for s in self._steps],
            "animation_steps": [
                {
                    "step_number": i + 1,
                    "tree": s.tree_state or self.export_nested(),
                    "description": s.description,
                    "step_type": s.action,
                    "highlighted_nodes": s.node_keys,
                    "why": s.why,
                }
                for i, s in enumerate(self._steps)
            ],
        }

    # ================================================================
    # Debug / Utility
    # ================================================================

    def pretty_print(self) -> str:
        """Return a text-based tree visualization for debugging."""
        lines: list[str] = []
        self._pretty_print(self.root, "", True, lines)
        return "\n".join(lines)

    def _pretty_print(
        self,
        node: Optional[AVLNode],
        prefix: str,
        is_last: bool,
        lines: list[str],
    ) -> None:
        if not node:
            return
        bf = self._balance_factor(node)
        symbol = "└── " if is_last else "├── "
        lines.append(f"{prefix}{symbol}{node.key} (h={node.height}, BF={bf})")
        extension = "    " if is_last else "│   "
        prefix += extension

        has_left = node.left is not None
        has_right = node.right is not None
        self._pretty_print(node.left, prefix, not has_right, lines)
        self._pretty_print(node.right, prefix, True, lines)

    def size(self) -> int:
        """Return the total number of nodes in the tree."""
        return self._count_nodes(self.root)

    @staticmethod
    def _count_nodes(node: Optional[AVLNode]) -> int:
        if not node:
            return 0
        return 1 + AVLTree._count_nodes(node.left) + AVLTree._count_nodes(node.right)
