"""
Production-Level Red-Black Tree Implementation
================================================
Self-balancing binary search tree where each node carries a colour
(red or black) and the tree satisfies five invariants:

  1. Every node is either RED or BLACK.
  2. The root is always BLACK.
  3. All leaves (NIL) are BLACK.
  4. If a node is RED, both its children are BLACK
     (no two consecutive red nodes on any path).
  5. Every path from a given node to its descendant leaves
     contains the same number of BLACK nodes (uniform black-height).

These properties guarantee the tree height is at most 2*log2(n+1),
ensuring O(log n) operations.

Designed for the Neuro-Symbolic AI Tutoring System with:
- Step-by-step recoloring and rotation recording for frontend animation
- Visualization-friendly JSON serialization with colour + black-height
- Concept-tagged violations for symbolic validation integration
- Educational metadata on every state change (WHY each recolor/rotation)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================
# Colour constants (use booleans for compactness; str for export)
# ============================================================
RED = True
BLACK = False

COLOUR_NAME = {RED: "RED", BLACK: "BLACK"}


class ViolationType(Enum):
    """Red-Black invariant violation types for symbolic validation."""
    ROOT_NOT_BLACK = "root_not_black"
    CONSECUTIVE_RED = "consecutive_red_nodes"
    UNEQUAL_BLACK_HEIGHT = "unequal_black_height"
    BST_ORDERING = "bst_violation"


class InsertFixCase(Enum):
    """Red-Black insert fix-up cases."""
    UNCLE_RED = "uncle_red_recolor"
    LEFT_TRIANGLE = "left_triangle_rotate"   # LR zig-zag
    LEFT_LINE = "left_line_rotate"           # LL zig-zig
    RIGHT_TRIANGLE = "right_triangle_rotate"  # RL zig-zag
    RIGHT_LINE = "right_line_rotate"          # RR zig-zig


@dataclass
class RBNode:
    """A node in the Red-Black tree.

    Uses sentinel NIL pattern: all leaf references point to a shared
    NIL node (colour BLACK) instead of None. This simplifies the
    invariant checks — every real node always has two children.
    """
    key: int
    color: bool = RED
    left: Optional["RBNode"] = None
    right: Optional["RBNode"] = None
    parent: Optional["RBNode"] = None


@dataclass
class OperationStep:
    """A single recorded step during a tree operation."""
    action: str           # "compare", "insert", "recolor", "rotation", "delete", "result"
    node_keys: list[int]  # Affected node keys
    description: str      # Human-readable description
    why: str              # Educational explanation of WHY this step occurs
    concept_tag: str      # Maps to KnowledgeGraph concept node
    tree_state: Optional[dict] = None  # Snapshot at this point


class RedBlackTree:
    """
    Red-Black self-balancing binary search tree.

    Uses the sentinel NIL pattern for cleaner invariant maintenance.
    The NIL sentinel is always BLACK and serves as a stand-in for
    absent children, making every real node a proper internal node
    with exactly two children.
    """

    def __init__(self):
        # Sentinel NIL node: shared, always BLACK, key=0 (irrelevant)
        self.NIL = RBNode(key=0, color=BLACK)
        self.NIL.left = self.NIL
        self.NIL.right = self.NIL
        self.NIL.parent = None

        self.root: RBNode = self.NIL
        self._steps: list[OperationStep] = []

    # ================================================================
    # Helper methods
    # ================================================================

    def _color_name(self, node: RBNode) -> str:
        """Return 'RED' or 'BLACK' for a node."""
        return COLOUR_NAME[node.color]

    def _is_red(self, node: RBNode) -> bool:
        """Check if a node is RED (NIL is always BLACK, so safe)."""
        return node != self.NIL and node.color == RED

    def _is_black(self, node: RBNode) -> bool:
        """Check if a node is BLACK."""
        return node == self.NIL or node.color == BLACK

    def _sibling(self, node: RBNode) -> RBNode:
        """Return the sibling of a node (NIL if no sibling)."""
        if node.parent is None:
            return self.NIL
        if node == node.parent.left:
            return node.parent.right
        return node.parent.left

    def _uncle(self, node: RBNode) -> RBNode:
        """Return the uncle of a node (parent's sibling)."""
        if node.parent is None or node.parent.parent is None:
            return self.NIL
        return self._sibling(node.parent)

    # ================================================================
    # Rotation methods (update parent pointers + NIL handling)
    # ================================================================

    def _rotate_left(self, x: RBNode) -> RBNode:
        """
        Left rotation around x:

             x                 y
            / \\               / \\
           α   y      =>      x   γ
              / \\           / \\
             β   γ          α   β

        y becomes the new subtree root.
        x becomes y's left child.
        β (y's former left) becomes x's right child.
        """
        y = x.right

        # Move y's left subtree to x's right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x

        # Link y to x's parent
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        # Complete rotation
        y.left = x
        x.parent = y

        self._steps.append(OperationStep(
            action="rotation",
            node_keys=[y.key, x.key],
            description=f"Left rotation: {y.key} becomes parent of {x.key}",
            why=(
                f"A left rotation at {x.key} restructures the subtree so that {y.key} "
                f"becomes the new root. This preserves BST ordering while helping to "
                f"resolve a Red-Black property violation."
            ),
            concept_tag="rb_rotation_left",
        ))
        return y

    def _rotate_right(self, x: RBNode) -> RBNode:
        """
        Right rotation around x:

               x                 y
              / \\               / \\
             y   γ      =>      α   x
            / \\                   / \\
           α   β                  β   γ

        y becomes the new subtree root.
        x becomes y's right child.
        β (y's former right) becomes x's left child.
        """
        y = x.left

        # Move y's right subtree to x's left
        x.left = y.right
        if y.right != self.NIL:
            y.right.parent = x

        # Link y to x's parent
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y

        # Complete rotation
        y.right = x
        x.parent = y

        self._steps.append(OperationStep(
            action="rotation",
            node_keys=[y.key, x.key],
            description=f"Right rotation: {y.key} becomes parent of {x.key}",
            why=(
                f"A right rotation at {x.key} restructures the subtree so that {y.key} "
                f"becomes the new root. This preserves BST ordering while helping to "
                f"resolve a Red-Black property violation."
            ),
            concept_tag="rb_rotation_right",
        ))
        return y

    # ================================================================
    # Transplant (subtree replacement for delete)
    # ================================================================

    def _transplant(self, u: RBNode, v: RBNode) -> None:
        """
        Replace subtree rooted at u with subtree rooted at v.
        Only rewires parent-child links; does NOT update v's children.

        This is a pure structural operation used during deletion.
        """
        if u.parent is None:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _minimum(self, node: RBNode) -> RBNode:
        """Find the node with the minimum key in the subtree."""
        while node.left != self.NIL:
            node = node.left
        return node

    # ================================================================
    # Insert
    # ================================================================

    def insert(self, key: int) -> dict[str, Any]:
        """
        Insert a key into the Red-Black tree.

        Algorithm:
        1. Standard BST insert the new node as RED.
           (Inserting RED doesn't affect black-height — property 5.)
        2. Fix violations:
           - If parent is BLACK, no violation (done).
           - If parent is RED, we have a red-red violation (property 4).
             Fix using recoloring and/or rotations based on uncle's colour.

        Returns a dict with operation metadata, tree export, and step log.
        """
        self._steps = []

        self._steps.append(OperationStep(
            action="insert",
            node_keys=[key],
            description=f"Begin RB insert: key = {key} (new node starts RED)",
            why="New nodes are always inserted RED to avoid changing black-height on any path.",
            concept_tag="rb_insert",
            tree_state=self._capture_snapshot(),
        ))

        # BST insert
        new_node = RBNode(key=key, color=RED, left=self.NIL, right=self.NIL)
        parent = None
        current = self.root

        while current != self.NIL:
            parent = current
            self._steps.append(OperationStep(
                action="compare",
                node_keys=[key, current.key],
                description=f"Compare {key} with {current.key}",
                why=f"BST rule: go {'LEFT' if key < current.key else 'RIGHT'}.",
                concept_tag="binary_search_property",
            ))
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                # Duplicate key
                self._steps.append(OperationStep(
                    action="result",
                    node_keys=[key],
                    description=f"Key {key} already exists — no duplicate insertion",
                    why="Red-Black trees maintain unique keys.",
                    concept_tag="rb_insert",
                    tree_state=self._capture_snapshot(),
                ))
                return self._build_result("insert", key)

        # Link new node into the tree
        new_node.parent = parent
        if parent is None:
            self.root = new_node
            # Root must be BLACK (property 2)
            self._steps.append(OperationStep(
                action="recolor",
                node_keys=[key],
                description=f"Node {key} is the root → set to BLACK",
                why="Property 2: the root of a Red-Black tree must always be BLACK.",
                concept_tag="rb_root_property",
            ))
            new_node.color = BLACK
        elif key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node

        self._steps.append(OperationStep(
            action="insert",
            node_keys=[key],
            description=f"Inserted node {key} as RED child of "
                        f"{parent.key if parent else 'root'}",
            why="New node is RED to preserve black-height invariant.",
            concept_tag="rb_insert",
        ))

        # Fix any Red-Black violations
        if new_node.parent and new_node.parent.parent:
            self._fix_insert(new_node)

        self._steps.append(OperationStep(
            action="result",
            node_keys=[],
            description=f"Insert of {key} complete. "
                        f"Black-height = {self._black_height(self.root)}.",
            why="All Red-Black properties are satisfied after fix-up.",
            concept_tag="rb_insert",
            tree_state=self._capture_snapshot(),
        ))

        return self._build_result("insert", key)

    def _fix_insert(self, k: RBNode) -> None:
        """
        Fix Red-Black violations after insertion.

        The only possible violation is a RED node with a RED parent
        (property 4). We resolve it by examining the uncle:

        Case 1: Uncle is RED
          → Recolor parent and uncle to BLACK, grandparent to RED.
            Then recurse up from grandparent.

        Case 2: Uncle is BLACK and k is an inner grandchild (zig-zag)
          → Rotate to make it an outer grandchild (zig-zig), fall through.

        Case 3: Uncle is BLACK and k is an outer grandchild (zig-zig)
          → Rotate grandparent, recolor. Done.
        """
        while k.parent and k.parent.color == RED:
            if k.parent == k.parent.parent.right:
                # Mirror case: parent is right child of grandparent
                uncle = k.parent.parent.left

                if self._is_red(uncle):
                    # Case 1: Uncle is RED → recolor and move up
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[uncle.key, k.parent.key, k.parent.parent.key],
                        description=f"Case 1 (uncle RED): recolor uncle {uncle.key}→BLACK, "
                                    f"parent {k.parent.key}→BLACK, "
                                    f"grandparent {k.parent.parent.key}→RED",
                        why=(
                            f"When the uncle is RED, we can simply recolor: parent and uncle "
                            f"become BLACK (adding 1 black to their subtrees), grandparent becomes "
                            f"RED (preserving black-height). The violation may propagate upward, "
                            f"so we check from grandparent."
                        ),
                        concept_tag="rb_recolor_uncle",
                    ))
                    uncle.color = BLACK
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    k = k.parent.parent
                else:
                    # Uncle is BLACK
                    if k == k.parent.left:
                        # Case 2: Zig-zag (k is left child of right parent)
                        self._steps.append(OperationStep(
                            action="rotation",
                            node_keys=[k.parent.key, k.key],
                            description=f"Case 2 (RL zig-zag): right rotate at {k.parent.key}",
                            why=(
                                f"k ({k.key}) is the LEFT child of its RED parent. "
                                f"This zig-zag pattern is converted to zig-zig by rotating "
                                f"right at the parent, making k the parent."
                            ),
                            concept_tag="rb_insert_rl",
                        ))
                        k = k.parent
                        self._rotate_right(k)

                    # Case 3: Zig-zig → rotate grandparent, recolor
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[k.parent.key, k.parent.parent.key],
                        description=f"Case 3: recolor parent {k.parent.key}→BLACK, "
                                    f"grandparent {k.parent.parent.key}→RED",
                        why=(
                            f"After straightening to zig-zig, we rotate the grandparent "
                            f"and swap colours: the old parent becomes BLACK (it's now the "
                            f"root of this subtree) and the old grandparent becomes RED."
                        ),
                        concept_tag="rb_recolor_fix",
                    ))
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    self._rotate_left(k.parent.parent)

            else:
                # Symmetric case: parent is left child of grandparent
                uncle = k.parent.parent.right

                if self._is_red(uncle):
                    # Case 1: Uncle is RED → recolor and move up
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[uncle.key, k.parent.key, k.parent.parent.key],
                        description=f"Case 1 (uncle RED): recolor uncle {uncle.key}→BLACK, "
                                    f"parent {k.parent.key}→BLACK, "
                                    f"grandparent {k.parent.parent.key}→RED",
                        why=(
                            f"When the uncle is RED, we recolor parent and uncle to BLACK, "
                            f"grandparent to RED. This preserves black-height on all paths "
                            f"through this subtree, but may push the violation upward."
                        ),
                        concept_tag="rb_recolor_uncle",
                    ))
                    uncle.color = BLACK
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    k = k.parent.parent
                else:
                    # Uncle is BLACK
                    if k == k.parent.right:
                        # Case 2: Zig-zag (k is right child of left parent)
                        self._steps.append(OperationStep(
                            action="rotation",
                            node_keys=[k.parent.key, k.key],
                            description=f"Case 2 (LR zig-zag): left rotate at {k.parent.key}",
                            why=(
                                f"k ({k.key}) is the RIGHT child of its RED parent. "
                                f"This zig-zag pattern is converted to zig-zig by rotating "
                                f"left at the parent, making k the parent."
                            ),
                            concept_tag="rb_insert_lr",
                        ))
                        k = k.parent
                        self._rotate_left(k)

                    # Case 3: Zig-zig → rotate grandparent, recolor
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[k.parent.key, k.parent.parent.key],
                        description=f"Case 3: recolor parent {k.parent.key}→BLACK, "
                                    f"grandparent {k.parent.parent.key}→RED",
                        why=(
                            f"After straightening to zig-zig, we rotate the grandparent "
                            f"and swap colours: the old parent becomes BLACK and the "
                            f"old grandparent becomes RED."
                        ),
                        concept_tag="rb_recolor_fix",
                    ))
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    self._rotate_right(k.parent.parent)

            if k == self.root:
                break

        # Ensure root is always BLACK (property 2)
        if self.root.color != BLACK:
            self._steps.append(OperationStep(
                action="recolor",
                node_keys=[self.root.key],
                description=f"Root {self.root.key} set to BLACK (final safety check)",
                why="Property 2: the root must always be BLACK.",
                concept_tag="rb_root_property",
            ))
            self.root.color = BLACK

    # ================================================================
    # Delete
    # ================================================================

    def delete(self, key: int) -> dict[str, Any]:
        """
        Delete a key from the Red-Black tree.

        Algorithm:
        1. Standard BST delete (using transplant for subtree replacement).
        2. Track the colour of the removed/moved node.
        3. If a BLACK node was removed, black-height is violated → fix.

        Returns a dict with operation metadata, tree export, and step log.
        """
        self._steps = []

        self._steps.append(OperationStep(
            action="delete",
            node_keys=[key],
            description=f"Begin RB delete: key = {key}",
            why="Deletion follows BST rules, then fixes any Red-Black property violations.",
            concept_tag="rb_delete",
            tree_state=self._capture_snapshot(),
        ))

        self._delete_node(key)

        self._steps.append(OperationStep(
            action="result",
            node_keys=[],
            description=f"Delete of {key} complete. "
                        f"Black-height = {self._black_height(self.root)}.",
            why="All Red-Black properties are restored after fix-up.",
            concept_tag="rb_delete",
            tree_state=self._capture_snapshot(),
        ))

        return self._build_result("delete", key)

    def _delete_node(self, key: int) -> None:
        """
        Delete the node with the given key.

        We find the actual node z to remove (or its in-order successor
        if z has two children), transplant it out, and if the removed
        node was BLACK, call _fix_delete to restore invariants.
        """
        # Find node z with the key
        z = self.NIL
        current = self.root
        while current != self.NIL:
            if current.key == key:
                z = current
            if key <= current.key:
                current = current.left
            else:
                current = current.right

        if z == self.NIL:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} not found in tree",
                why="The key does not exist; nothing to delete.",
                concept_tag="rb_delete",
            ))
            return

        self._steps.append(OperationStep(
            action="delete",
            node_keys=[key],
            description=f"Found node {key} to delete (colour: {self._color_name(z)})",
            why="This is the deletion target. We determine the transplant strategy.",
            concept_tag="rb_delete",
        ))

        # y is the node that will be removed from the tree
        # (either z itself, or z's in-order successor)
        y = z
        y_original_color = y.color

        if z.left == self.NIL:
            # z has 0 or 1 child (right)
            x = z.right
            self._steps.append(OperationStep(
                action="delete",
                node_keys=[key],
                description=f"Node {key} has no left child → transplant with right child",
                why="With at most one child, transplant is straightforward.",
                concept_tag="rb_delete",
            ))
            self._transplant(z, z.right)
        elif z.right == self.NIL:
            # z has exactly 1 child (left)
            x = z.left
            self._steps.append(OperationStep(
                action="delete",
                node_keys=[key],
                description=f"Node {key} has no right child → transplant with left child",
                why="With exactly one child, that child takes this node's place.",
                concept_tag="rb_delete",
            ))
            self._transplant(z, z.left)
        else:
            # z has two children: use in-order successor
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right

            self._steps.append(OperationStep(
                action="delete",
                node_keys=[key, y.key],
                description=f"Node {key} has 2 children → "
                            f"replace with in-order successor {y.key}",
                why=(
                    f"The in-order successor ({y.key}) is the smallest key in the right "
                    f"subtree. It has at most one child, so transplant is simple."
                ),
                concept_tag="rb_delete",
            ))

            if y.parent == z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y

            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

            self._steps.append(OperationStep(
                action="recolor",
                node_keys=[y.key],
                description=f"Successor {y.key} inherits colour "
                            f"{self._color_name(z)} from deleted node",
                why="The successor takes the deleted node's colour to preserve black-height.",
                concept_tag="rb_delete",
            ))

        # If the removed node was BLACK, black-height is violated
        if y_original_color == BLACK:
            self._steps.append(OperationStep(
                action="recolor",
                node_keys=[x.key] if x != self.NIL else [],
                description=f"Removed node was BLACK → black-height violated. "
                            f"Starting fix-up from {x.key if x != self.NIL else 'NIL'}",
                why=(
                    f"Removing a BLACK node decreases the black-count on all paths "
                    f"through that subtree. The fix-up restores uniform black-height."
                ),
                concept_tag="rb_black_height",
            ))
            self._fix_delete(x)

    def _fix_delete(self, x: RBNode) -> None:
        """
        Fix Red-Black violations after deletion.

        The violation is that node x carries an "extra black" (it's
        effectively doubly-black or black+NIL). We push this extra
        black upward until:
        - x becomes the root (absorb the extra black), or
        - x is RED (change it to BLACK and we're done).

        We resolve it by examining x's sibling:

        Case 1: Sibling is RED
          → Rotate parent, recolor sibling BLACK, parent RED.
            New sibling is now BLACK → continue to cases 2/3/4.

        Case 2: Sibling is BLACK and both children are BLACK
          → Recolor sibling RED, move extra black to parent.
            x = parent, repeat.

        Case 3: Sibling is BLACK, inner child is RED, outer child is BLACK
          → Rotate sibling, recolor. Now outer child is RED → case 4.

        Case 4: Sibling is BLACK and outer child is RED
          → Rotate parent, swap colours, remove extra black. Done.
        """
        while x != self.root and x.color == BLACK:
            if x == x.parent.left:
                s = x.parent.right  # sibling

                # Case 1: Sibling is RED
                if self._is_red(s):
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key, x.parent.key],
                        description=f"Delete Case 1: sibling {s.key} is RED → "
                                    f"recolor sibling→BLACK, parent→RED, "
                                    f"left rotate at {x.parent.key}",
                        why=(
                            f"When the sibling is RED, we rotate the parent and recolour. "
                            f"The new sibling (one of the old sibling's children) is BLACK, "
                            f"allowing us to proceed to cases 2/3/4."
                        ),
                        concept_tag="rb_delete_sibling_red",
                    ))
                    s.color = BLACK
                    x.parent.color = RED
                    self._rotate_left(x.parent)
                    s = x.parent.right

                # Case 2: Both of sibling's children are BLACK
                if self._is_black(s.left) and self._is_black(s.right):
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key],
                        description=f"Delete Case 2: both children of sibling {s.key} "
                                    f"are BLACK → recolor sibling→RED, move black up",
                        why=(
                            f"When both of the sibling's children are BLACK, we can "
                            f"recolour the sibling RED (removing one black from its side) "
                            f"and move the extra black to the parent. We then repeat from "
                            f"the parent."
                        ),
                        concept_tag="rb_delete_both_black",
                    ))
                    s.color = RED
                    x = x.parent
                else:
                    # Case 3: Sibling's outer child is BLACK (inner is RED)
                    if self._is_black(s.right):
                        self._steps.append(OperationStep(
                            action="recolor",
                            node_keys=[s.key, s.left.key],
                            description=f"Delete Case 3: sibling's right child is BLACK → "
                                        f"recolor sibling's left→BLACK, sibling→RED, "
                                        f"right rotate at sibling {s.key}",
                            why=(
                                f"The inner child (left) of the sibling is RED and the outer "
                                f"child (right) is BLACK. We rotate the sibling to convert "
                                f"this into Case 4 where the outer child is RED."
                            ),
                            concept_tag="rb_delete_inner_red",
                        ))
                        s.left.color = BLACK
                        s.color = RED
                        self._rotate_right(s)
                        s = x.parent.right

                    # Case 4: Sibling's outer child is RED
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key, x.parent.key],
                        description=f"Delete Case 4: sibling's right child is RED → "
                                    f"recolor sibling to parent's colour, "
                                    f"parent→BLACK, sibling's right→BLACK, "
                                    f"left rotate at {x.parent.key}",
                        why=(
                            f"The outer child of the sibling is RED. We rotate the parent, "
                            f"swap colours, and the extra black is absorbed. This is the "
                            f"terminating case."
                        ),
                        concept_tag="rb_delete_outer_red",
                    ))
                    s.color = x.parent.color
                    x.parent.color = BLACK
                    s.right.color = BLACK
                    self._rotate_left(x.parent)
                    x = self.root  # Extra black is resolved
            else:
                # Mirror case: x is right child
                s = x.parent.left  # sibling

                # Case 1: Sibling is RED
                if self._is_red(s):
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key, x.parent.key],
                        description=f"Delete Case 1 (mirror): sibling {s.key} is RED → "
                                    f"recolor sibling→BLACK, parent→RED, "
                                    f"right rotate at {x.parent.key}",
                        why=(
                            f"When the sibling is RED, we rotate the parent and recolour. "
                            f"The new sibling is BLACK, allowing us to proceed to cases 2/3/4."
                        ),
                        concept_tag="rb_delete_sibling_red",
                    ))
                    s.color = BLACK
                    x.parent.color = RED
                    self._rotate_right(x.parent)
                    s = x.parent.left

                # Case 2: Both of sibling's children are BLACK
                if self._is_black(s.right) and self._is_black(s.left):
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key],
                        description=f"Delete Case 2 (mirror): both children of sibling "
                                    f"{s.key} are BLACK → recolor sibling→RED, move black up",
                        why=(
                            f"When both of the sibling's children are BLACK, we recolour "
                            f"the sibling RED and move the extra black to the parent."
                        ),
                        concept_tag="rb_delete_both_black",
                    ))
                    s.color = RED
                    x = x.parent
                else:
                    # Case 3: Sibling's outer child is BLACK (inner is RED)
                    if self._is_black(s.left):
                        self._steps.append(OperationStep(
                            action="recolor",
                            node_keys=[s.key, s.right.key],
                            description=f"Delete Case 3 (mirror): sibling's left child is "
                                        f"BLACK → recolor sibling's right→BLACK, "
                                        f"sibling→RED, left rotate at sibling {s.key}",
                            why=(
                                f"The inner child (right) of the sibling is RED and the "
                                f"outer child (left) is BLACK. We rotate the sibling to "
                                f"convert this into Case 4."
                            ),
                            concept_tag="rb_delete_inner_red",
                        ))
                        s.right.color = BLACK
                        s.color = RED
                        self._rotate_left(s)
                        s = x.parent.left

                    # Case 4: Sibling's outer child is RED
                    self._steps.append(OperationStep(
                        action="recolor",
                        node_keys=[s.key, x.parent.key],
                        description=f"Delete Case 4 (mirror): sibling's left child is RED → "
                                    f"recolor sibling to parent's colour, "
                                    f"parent→BLACK, sibling's left→BLACK, "
                                    f"right rotate at {x.parent.key}",
                        why=(
                            f"The outer child of the sibling is RED. We rotate the parent, "
                            f"swap colours, and the extra black is absorbed. This is the "
                            f"terminating case."
                        ),
                        concept_tag="rb_delete_outer_red",
                    ))
                    s.color = x.parent.color
                    x.parent.color = BLACK
                    s.left.color = BLACK
                    self._rotate_right(x.parent)
                    x = self.root

        # If x ended up RED, make it BLACK (absorbs the extra black)
        x.color = BLACK

    # ================================================================
    # Search
    # ================================================================

    def search(self, key: int) -> dict[str, Any]:
        """Search for a key. Returns path and whether found."""
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

    def _search(self, node: RBNode, key: int, path: list[int]) -> bool:
        if node == self.NIL:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} not found — reached NIL",
                why="The search path ended at a NIL leaf.",
                concept_tag="binary_search_property",
            ))
            return False

        path.append(node.key)
        self._steps.append(OperationStep(
            action="compare",
            node_keys=[key, node.key],
            description=f"Compare {key} with {node.key} "
                        f"(colour: {self._color_name(node)})",
            why=f"BST rule: go {'LEFT' if key < node.key else 'RIGHT' if key > node.key else 'FOUND'}.",
            concept_tag="binary_search_property",
        ))

        if key == node.key:
            self._steps.append(OperationStep(
                action="result",
                node_keys=[key],
                description=f"Key {key} found (colour: {self._color_name(node)})",
                why=f"Search terminated after {len(path)} comparisons.",
                concept_tag="binary_search_property",
            ))
            return True
        elif key < node.key:
            return self._search(node.left, key, path)
        else:
            return self._search(node.right, key, path)

    # ================================================================
    # Black-height computation (for validation and export)
    # ================================================================

    def _black_height(self, node: RBNode) -> int:
        """
        Compute the black-height of a node.
        Black-height = number of BLACK nodes on any path from this
        node (exclusive) to a NIL leaf (inclusive).

        Returns -1 if black-height is inconsistent (for validation).
        """
        if node == self.NIL:
            return 1  # NIL counts as 1 black

        left_bh = self._black_height(node.left)
        right_bh = self._black_height(node.right)

        if left_bh == -1 or right_bh == -1 or left_bh != right_bh:
            return -1

        return left_bh + (1 if node.color == BLACK else 0)

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
        if self.root == self.NIL:
            return None

        bh = self._black_height(self.root)
        return self._export_node(self.root, black_height=1 if self.root.color == BLACK else 0, total_bh=bh)

    def _export_node(
        self,
        node: RBNode,
        black_height: int,
        total_bh: int,
    ) -> Optional[dict[str, Any]]:
        if node == self.NIL:
            return None

        current_bh = black_height + (1 if node.color == BLACK else 0)
        left = self._export_node(node.left, current_bh, total_bh)
        right = self._export_node(node.right, current_bh, total_bh)
        return {
            "key": node.key,
            "value": node.key,
            "color": self._color_name(node),
            "black_height_from_root": current_bh,
            "total_black_height": total_bh,
            "is_valid_black_height": current_bh == total_bh,
            "left": left,
            "right": right,
            "children": [child for child in (left, right) if child is not None],
        }

    def export_level_order(self) -> dict[str, Any]:
        """
        Export the tree in level-order (BFS) as a flat nodes + edges structure.
        Used by D3 force-directed or layered layouts.
        """
        if self.root == self.NIL:
            return {"nodes": [], "edges": [], "black_height": 0}

        bh = self._black_height(self.root)
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        queue: list[tuple[RBNode, Optional[int], int]] = [(self.root, None, 0)]

        current_bh = 1 if self.root.color == BLACK else 0

        while queue:
            node, parent_key, depth = queue.pop(0)
            node_bh = current_bh  # Simplified: recompute per node below

            # Recompute black-height from root for this node
            path_bh = self._path_black_height(node)

            nodes.append({
                "key": node.key,
                "depth": depth,
                "color": self._color_name(node),
                "black_height_from_root": path_bh,
                "total_black_height": bh,
                "is_valid_black_height": path_bh == bh,
                "parent": parent_key,
            })

            if parent_key is not None:
                edges.append({"source": parent_key, "target": node.key})

            if node.left != self.NIL:
                queue.append((node.left, node.key, depth + 1))
            if node.right != self.NIL:
                queue.append((node.right, node.key, depth + 1))

        return {"nodes": nodes, "edges": edges, "black_height": bh}

    def _path_black_height(self, node: RBNode) -> int:
        """Count BLACK nodes from root to this node (inclusive)."""
        count = 0
        current = node
        path: list[RBNode] = []
        while current is not None and current != self.NIL:
            path.append(current)
            current = current.parent
        path.reverse()
        for n in path:
            if n.color == BLACK:
                count += 1
        return count

    def export_adjacency(self) -> dict[str, Any]:
        """
        Export as adjacency list + node properties.
        Used for graph-based layouts and validation.
        """
        if self.root == self.NIL:
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
        node: RBNode,
        nodes: dict[int, dict],
        edges: list[tuple[int, int]],
    ) -> None:
        if node == self.NIL:
            return

        nodes[node.key] = {
            "color": self._color_name(node),
            "is_red": node.color == RED,
        }

        if node.left != self.NIL:
            edges.append((node.key, node.left.key))
            self._build_adjacency(node.left, nodes, edges)
        if node.right != self.NIL:
            edges.append((node.key, node.right.key))
            self._build_adjacency(node.right, nodes, edges)

    # ================================================================
    # Validation (for symbolic validation engine integration)
    # ================================================================

    def validate(self) -> dict[str, Any]:
        """
        Validate all Red-Black invariants and return a detailed report.

        Checks:
        1. Root is BLACK
        2. No two consecutive RED nodes (parent and child)
        3. All paths from root to NIL have equal black-height
        4. BST ordering (left < node < right)

        Each violation includes a concept_tag for KG mapping.
        """
        violations: list[dict] = []

        # Property 2: Root must be BLACK
        if self.root != self.NIL and self.root.color != BLACK:
            violations.append({
                "type": ViolationType.ROOT_NOT_BLACK.value,
                "rule_id": "RB-001",
                "severity": "high",
                "message": "Root node must be BLACK (Property 2).",
                "concept_tag": "rb_root_property",
            })

        # Property 4: No consecutive RED nodes
        self._check_no_consecutive_red(self.root, violations)

        # Property 5: Uniform black-height
        self._check_black_height(self.root, violations)

        # BST ordering (implicit in RB definition)
        self._check_bst(self.root, float("-inf"), float("inf"), violations)

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "tree": self.export_nested(),
        }

    def _check_no_consecutive_red(
        self,
        node: RBNode,
        violations: list[dict],
    ) -> None:
        """Property 4: A RED node cannot have a RED child."""
        if node == self.NIL:
            return

        if node.color == RED:
            if self._is_red(node.left):
                violations.append({
                    "type": ViolationType.CONSECUTIVE_RED.value,
                    "rule_id": "RB-002",
                    "parent": node.key,
                    "child": node.left.key,
                    "severity": "high",
                    "message": (
                        f"Red node {node.key} has a red child {node.left.key}. "
                        f"No two consecutive red nodes are allowed (Property 4)."
                    ),
                    "concept_tag": "rb_red_red_property",
                })
            if self._is_red(node.right):
                violations.append({
                    "type": ViolationType.CONSECUTIVE_RED.value,
                    "rule_id": "RB-002",
                    "parent": node.key,
                    "child": node.right.key,
                    "severity": "high",
                    "message": (
                        f"Red node {node.key} has a red child {node.right.key}. "
                        f"No two consecutive red nodes are allowed (Property 4)."
                    ),
                    "concept_tag": "rb_red_red_property",
                })

        self._check_no_consecutive_red(node.left, violations)
        self._check_no_consecutive_red(node.right, violations)

    def _check_black_height(
        self,
        node: RBNode,
        violations: list[dict],
    ) -> int:
        """
        Property 5: All paths from this node to NIL leaves must
        contain the same number of BLACK nodes.

        Returns the black-height, or -1 if inconsistent.
        """
        if node == self.NIL:
            return 1

        left_bh = self._check_black_height(node.left, violations)
        right_bh = self._check_black_height(node.right, violations)

        if left_bh == -1 or right_bh == -1:
            return -1

        if left_bh != right_bh:
            violations.append({
                "type": ViolationType.UNEQUAL_BLACK_HEIGHT.value,
                "rule_id": "RB-003",
                "node": node.key,
                "left_black_height": left_bh,
                "right_black_height": right_bh,
                "severity": "high",
                "message": (
                    f"Node {node.key} has unequal black-heights: "
                    f"left={left_bh}, right={right_bh}. "
                    f"All paths to NIL must have the same black-height (Property 5)."
                ),
                "concept_tag": "rb_black_height",
            })
            return -1

        return left_bh + (1 if node.color == BLACK else 0)

    def _check_bst(
        self,
        node: RBNode,
        lo: float,
        hi: float,
        violations: list[dict],
    ) -> None:
        """Check BST ordering invariant."""
        if node == self.NIL:
            return

        if node.key <= lo or node.key >= hi:
            violations.append({
                "type": ViolationType.BST_ORDERING.value,
                "rule_id": "RB-004",
                "node": node.key,
                "severity": "high",
                "message": (
                    f"Node {node.key} violates BST ordering. "
                    f"It must be in range ({lo}, {hi})."
                ),
                "concept_tag": "binary_search_property",
            })

        self._check_bst(node.left, lo, node.key, violations)
        self._check_bst(node.right, node.key, hi, violations)

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
        node: RBNode,
        prefix: str,
        is_last: bool,
        lines: list[str],
    ) -> None:
        if node == self.NIL:
            return

        symbol = "└── " if is_last else "├── "
        color_str = "R" if node.color == RED else "B"
        bh = self._path_black_height(node)
        lines.append(f"{prefix}{symbol}{node.key} ({color_str}, bh={bh})")

        extension = "    " if is_last else "│   "
        prefix += extension

        has_left = node.left != self.NIL
        has_right = node.right != self.NIL
        self._pretty_print(node.left, prefix, not has_right, lines)
        self._pretty_print(node.right, prefix, True, lines)

    def size(self) -> int:
        """Return the total number of real nodes (excluding NIL)."""
        return self._count_nodes(self.root)

    def _count_nodes(self, node: RBNode) -> int:
        if node == self.NIL:
            return 0
        return 1 + self._count_nodes(node.left) + self._count_nodes(node.right)
