"""
Misconception Detection Engine v2
===================================
Neuro-symbolic misconception detection with:
  1. Hierarchical misconception taxonomy
  2. Prerequisite dependency modelling with Bayesian inference
  3. Pattern-based root cause analysis
  4. Multi-factor severity scoring
  5. Adaptive remediation path generation

Architecture:
  Engine
  ├── ConceptTaxonomy       — Hierarchical concept/violation maps
  ├── PrerequisiteModel     — DAG of concept dependencies
  ├── InferenceEngine       — Multi-signal root cause analysis
  │   ├── PatternMatcher    — Recognizes violation patterns
  │   ├── RootCauseAnalyzer — Traces to root via prerequisites
  │   └── ConfidenceScorer  — Bayesian confidence estimation
  ├── SeverityScorer        — Multi-factor severity calculation
  └── RemediationEngine     — Adaptive learning path generator
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ==============================================================================
# I. Domain Enums & Data Classes
# ==============================================================================

class ConceptCategory(Enum):
    PREREQUISITE = "prerequisite"
    CORE = "core"
    OPERATION = "operation"
    META = "meta"


class MisconceptionPattern(Enum):
    SURFACE_SLIP = "surface_slip"
    CONCEPT_GAP = "concept_gap"
    PREREQUISITE_HOLE = "prerequisite_hole"
    CONFUSION = "confusion"
    PROCEDURAL_ERROR = "procedural_error"
    PERSISTENT_MISCONCEPTION = "persistent_misconception"
    COMPOUND_FAILURE = "compound_failure"


class SeverityLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConceptNode:
    """A concept in the taxonomy with its position in the prerequisite DAG."""
    id: str
    name: str
    category: ConceptCategory
    prerequisites: List[str] = field(default_factory=list)
    difficulty: float = 0.5
    is_hub: bool = False
    false_belief: str = ""  # the common false belief about this concept
    analogous_concepts: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)


@dataclass
class ViolationSignature:
    """A specific violation type linked to concepts."""
    violation_type: str
    tree_type: str
    primary_concept: str
    secondary_concepts: List[str] = field(default_factory=list)
    base_severity: SeverityLevel = SeverityLevel.MEDIUM
    base_confidence: float = 0.85
    description: str = ""


@dataclass
class MisconceptionDiagnosis:
    """Output of the inference engine — a diagnosed misconception."""
    concept_id: str
    concept_name: str
    pattern: MisconceptionPattern
    root_cause: str
    description: str
    false_belief: str
    severity: SeverityLevel
    confidence: float
    prerequisite_gaps: List[str] = field(default_factory=list)
    supporting_violations: List[Dict] = field(default_factory=list)
    affected_operations: List[str] = field(default_factory=list)
    analogous_to: List[str] = field(default_factory=list)


@dataclass
class RemediationPath:
    """A single remediation step in a learning path."""
    step_type: str  # 'review_prerequisite', 'targeted_practice', 'concept_explanation', 'guided_exercise', 'deeper_challenge'
    concept_id: str
    description: str
    estimated_difficulty: float = 0.5
    prerequisites_met: bool = True
    estimated_mastery_gain: float = 0.1


@dataclass
class RemediationPlan:
    """Full remediation plan generated from diagnoses."""
    diagnoses: List[MisconceptionDiagnosis] = field(default_factory=list)
    overall_severity: SeverityLevel = SeverityLevel.NONE
    learning_path: List[RemediationPath] = field(default_factory=list)
    critical_gaps: List[str] = field(default_factory=list)
    recommended_focus: str = ""
    estimated_sessions: int = 1


@dataclass
class StudentHistoryEntry:
    """A single recorded student interaction."""
    timestamp: float
    tree_type: str
    operation: str
    violations: List[Dict[str, Any]]
    success: bool
    concepts_tested: List[str] = field(default_factory=list)
    diagnosis_snapshot: Optional[Dict] = None


@dataclass
class StudentProfile:
    """Tracks the student's learning state over time."""
    history: List[StudentHistoryEntry] = field(default_factory=list)
    concept_mastery: Dict[str, float] = field(default_factory=dict)
    misconception_history: Dict[str, List[datetime]] = field(default_factory=dict)
    total_attempts: int = 0
    weak_concepts: Set[str] = field(default_factory=set)


# ==============================================================================
# II. Concept Taxonomy — Hierarchical Knowledge Map
# ==============================================================================

class ConceptTaxonomy:
    """
    Hierarchical taxonomy of all tree concepts organised by category.
    
    Four levels:
      PREREQUISITE — concepts that underpin all tree learning
      CORE        — central concepts for each tree type
      OPERATION   — specific operation algorithms
      META        — cross-cutting concerns (complexity, proofs)
    """

    def __init__(self):
        self._concepts: Dict[str, ConceptNode] = {}
        self._violations: Dict[str, ViolationSignature] = {}
        self._tree_concepts: Dict[str, List[str]] = defaultdict(list)
        self._build()

    def _build(self) -> None:
        self._add_prerequisites()
        self._add_avl_concepts()
        self._add_red_black_concepts()
        self._add_heap_concepts()
        self._add_btree_concepts()
        self._add_bplus_concepts()
        self._add_segment_concepts()
        self._add_meta_concepts()
        self._add_violation_signatures()

    def _add_prerequisites(self) -> None:
        """Level 0: Prerequisite concepts. If any of these fail, nothing above works."""
        prereqs = [
            ConceptNode("bst_property", "BST Ordering Property", ConceptCategory.PREREQUISITE,
                        difficulty=0.3, is_hub=True,
                        false_belief="'Left < parent < right' is optional — trees just store data"),
            ConceptNode("tree_height", "Tree Height & Depth", ConceptCategory.PREREQUISITE,
                        difficulty=0.3,
                        false_belief="Height and depth are the same concept"),
            ConceptNode("recursion", "Recursive Thinking", ConceptCategory.PREREQUISITE,
                        difficulty=0.5, is_hub=True,
                        false_belief="Recursion is an alternative to iteration, not a fundamental way to define tree structure"),
            ConceptNode("pointer_manipulation", "Pointer Manipulation", ConceptCategory.PREREQUISITE,
                        difficulty=0.4,
                        false_belief="Pointers can be reassigned in any order during restructuring"),
            ConceptNode("complete_binary_tree", "Complete Binary Tree Structure", ConceptCategory.PREREQUISITE,
                        difficulty=0.3,
                        false_belief="A complete tree is the same as a full tree"),
            ConceptNode("array_indexing", "Array Indexing for Trees", ConceptCategory.PREREQUISITE,
                        prerequisites=["complete_binary_tree"], difficulty=0.2,
                        false_belief="Parent-child index formulas are arbitrary"),
            ConceptNode("big_o", "Big-O Complexity Analysis", ConceptCategory.PREREQUISITE,
                        difficulty=0.4,
                        false_belief="Big-O is about counting operations exactly, not about growth rates"),
            ConceptNode("bst_search", "BST Search & Insert", ConceptCategory.PREREQUISITE,
                        prerequisites=["bst_property", "recursion"], difficulty=0.3,
                        false_belief="BST insertion replaces the root"),
            ConceptNode("bst_delete", "BST Delete (3 cases)", ConceptCategory.PREREQUISITE,
                        prerequisites=["bst_search"], difficulty=0.5,
                        false_belief="Deleting a node with two children can be done in place"),
            ConceptNode("subtree_properties", "Subtree Property Reasoning", ConceptCategory.PREREQUISITE,
                        prerequisites=["bst_property", "recursion"], difficulty=0.4, is_hub=True,
                        false_belief="Each subtree can be analyzed independently of its parent"),
        ]
        for c in prereqs:
            self._concepts[c.id] = c
            self._tree_concepts["prerequisites"].append(c.id)

    def _add_avl_concepts(self) -> None:
        """Level 1-2: AVL Tree concepts."""
        avl = [
            ConceptNode("avl_balance_factor", "Balance Factor Computation", ConceptCategory.CORE,
                        prerequisites=["tree_height", "bst_property"], difficulty=0.4,
                        false_belief="Balance factor is computed as left_height - right_height, and any non-zero value is wrong"),
            ConceptNode("avl_rotation_mechanics", "AVL Rotation Mechanics", ConceptCategory.CORE,
                        prerequisites=["pointer_manipulation", "bst_property"], difficulty=0.5,
                        analogous_concepts=["rb_rotation_mechanics"],
                        false_belief="Rotations rearrange keys arbitrarily"),
            ConceptNode("avl_rotation_cases", "Rotation Case Identification (LL/RR/LR/RL)", ConceptCategory.CORE,
                        prerequisites=["avl_balance_factor", "avl_rotation_mechanics"], difficulty=0.5,
                        false_belief="The rotation case is determined by the grandchild's position, not the child's"),
            ConceptNode("avl_height_update", "Height Update After Rotation", ConceptCategory.CORE,
                        prerequisites=["tree_height", "avl_rotation_mechanics"], difficulty=0.4,
                        false_belief="Height updates happen automatically during rotation"),
            ConceptNode("avl_insert", "AVL Insert Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_search", "avl_balance_factor", "avl_rotation_cases", "avl_height_update"],
                        difficulty=0.7, is_hub=True,
                        false_belief="AVL insertion is insert-then-rebalance-at-the-root"),
            ConceptNode("avl_delete", "AVL Delete Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_delete", "avl_insert"], difficulty=0.8,
                        false_belief="AVL deletion only requires rebalancing at the deletion point"),
        ]
        for c in avl:
            self._concepts[c.id] = c
            self._tree_concepts["avl"].append(c.id)

    def _add_red_black_concepts(self) -> None:
        """Level 1-2: Red-Black Tree concepts."""
        rb = [
            ConceptNode("rb_properties", "Red-Black Tree Properties (5 Rules)", ConceptCategory.CORE,
                        prerequisites=["bst_property"], difficulty=0.3, is_hub=True,
                        false_belief="The 5 RB properties are arbitrary rules to memorize"),
            ConceptNode("rb_uncle_identification", "Uncle Identification in RB Trees", ConceptCategory.CORE,
                        prerequisites=["rb_properties", "recursion"], difficulty=0.3,
                        false_belief="The uncle is always the parent's sibling regardless of orientation"),
            ConceptNode("rb_recoloring", "Recoloring Logic (Uncle = RED)", ConceptCategory.CORE,
                        prerequisites=["rb_properties"], difficulty=0.4,
                        false_belief="Recoloring fixes the violation permanently without needing to check higher"),
            ConceptNode("rb_rotation_mechanics", "RB Rotation Mechanics (Uncle = BLACK)", ConceptCategory.CORE,
                        prerequisites=["rb_recoloring", "pointer_manipulation"], difficulty=0.5,
                        analogous_concepts=["avl_rotation_mechanics"],
                        false_belief="RB rotations are the same as AVL rotations"),
            ConceptNode("rb_insert_fixup", "RB Insert Fix-Up Procedure", ConceptCategory.OPERATION,
                        prerequisites=["bst_search", "rb_uncle_identification", "rb_recoloring", "rb_rotation_mechanics"],
                        difficulty=0.7, is_hub=True,
                        false_belief="Insert fix-up only runs once and then the tree is valid"),
            ConceptNode("rb_delete_fixup", "RB Delete Fix-Up Procedure", ConceptCategory.OPERATION,
                        prerequisites=["bst_delete", "rb_insert_fixup"], difficulty=0.9,
                        false_belief="Delete fix-up is symmetric to insert fix-up"),
            ConceptNode("rb_black_height", "Black-Height Maintenance", ConceptCategory.CORE,
                        prerequisites=["rb_properties", "tree_height"], difficulty=0.6,
                        false_belief="Black-height is the same as tree height"),
        ]
        for c in rb:
            self._concepts[c.id] = c
            self._tree_concepts["red_black"].append(c.id)

    def _add_heap_concepts(self) -> None:
        heap = [
            ConceptNode("heap_property", "Heap Property (Min vs Max)", ConceptCategory.CORE,
                        prerequisites=["complete_binary_tree", "array_indexing"], difficulty=0.3,
                        false_belief="Min-heap means the smallest element can be anywhere"),
            ConceptNode("heap_sift_up", "Sift-Up (Bubble Up) Algorithm", ConceptCategory.CORE,
                        prerequisites=["heap_property", "array_indexing"], difficulty=0.4,
                        false_belief="Sift-up compares with both children"),
            ConceptNode("heap_sift_down", "Sift-Down (Bubble Down) Algorithm", ConceptCategory.CORE,
                        prerequisites=["heap_property", "array_indexing"], difficulty=0.4,
                        false_belief="Sift-down can stop as soon as one child is larger/smaller"),
            ConceptNode("heap_insert", "Heap Insert Operation", ConceptCategory.OPERATION,
                        prerequisites=["heap_property", "heap_sift_up", "complete_binary_tree"],
                        difficulty=0.5,
                        false_belief="Heap insertion requires finding the correct position first"),
            ConceptNode("heap_delete", "Heap Delete (Extract Root) Operation", ConceptCategory.OPERATION,
                        prerequisites=["heap_property", "heap_sift_down"], difficulty=0.5,
                        false_belief="Deleting the root leaves a hole that must be filled by shifting"),
            ConceptNode("heapify", "Build-Heap / Heapify Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["heap_sift_down"], difficulty=0.6,
                        false_belief="Building a heap from an array takes O(n log n) by inserting each element"),
        ]
        for c in heap:
            self._concepts[c.id] = c
            self._tree_concepts["heap"].append(c.id)

    def _add_btree_concepts(self) -> None:
        btree = [
            ConceptNode("btree_properties", "B-Tree Order & Key Limits", ConceptCategory.CORE,
                        prerequisites=["bst_property", "subtree_properties"], difficulty=0.4, is_hub=True,
                        false_belief="B-Tree order is the maximum number of keys, not children"),
            ConceptNode("btree_node_split", "Node Splitting Procedure", ConceptCategory.CORE,
                        prerequisites=["btree_properties"], difficulty=0.5,
                        false_belief="When a node splits, all keys are redistributed equally"),
            ConceptNode("btree_cascading_split", "Cascading Splits (Root Split)", ConceptCategory.CORE,
                        prerequisites=["btree_node_split", "recursion"], difficulty=0.6,
                        false_belief="When the root splits, the tree becomes shorter"),
            ConceptNode("btree_borrow", "Key Borrowing (Sibling Rotation)", ConceptCategory.CORE,
                        prerequisites=["btree_properties", "pointer_manipulation"], difficulty=0.5,
                        false_belief="Borrowing from a sibling always involves the same procedure"),
            ConceptNode("btree_merge", "Node Merging Procedure", ConceptCategory.CORE,
                        prerequisites=["btree_properties", "btree_borrow"], difficulty=0.5,
                        false_belief="Merging combines all keys from both nodes into one"),
            ConceptNode("btree_cascading_merge", "Cascading Merges", ConceptCategory.CORE,
                        prerequisites=["btree_merge", "recursion"], difficulty=0.7,
                        false_belief="Merges never propagate beyond one level"),
            ConceptNode("btree_insert", "B-Tree Insert Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_search", "btree_node_split", "btree_cascading_split"],
                        difficulty=0.7, is_hub=True,
                        false_belief="B-Tree insertion always adds a new leaf"),
            ConceptNode("btree_delete", "B-Tree Delete Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_delete", "btree_borrow", "btree_merge", "btree_cascading_merge"],
                        difficulty=0.8,
                        false_belief="B-Tree deletion follows the same pattern as BST deletion"),
        ]
        for c in btree:
            self._concepts[c.id] = c
            self._tree_concepts["btree"].append(c.id)

    def _add_bplus_concepts(self) -> None:
        bplus = [
            ConceptNode("bplus_structure", "B+ Tree Leaf vs Internal Structure", ConceptCategory.CORE,
                        prerequisites=["btree_properties"], difficulty=0.4,
                        false_belief="B+ Tree internal nodes store the same data as B-Tree internal nodes"),
            ConceptNode("bplus_leaf_linkage", "Leaf Linked List Maintenance", ConceptCategory.CORE,
                        prerequisites=["bplus_structure", "pointer_manipulation"], difficulty=0.5,
                        false_belief="Leaf linked list is automatically maintained during splits"),
            ConceptNode("bplus_leaf_split", "Leaf Split (Median Copied)", ConceptCategory.CORE,
                        prerequisites=["btree_node_split", "bplus_structure", "bplus_leaf_linkage"],
                        difficulty=0.5,
                        false_belief="Leaf splits in B+ Tree are identical to B-Tree splits"),
            ConceptNode("bplus_internal_split", "Internal Node Split (Median Promoted)", ConceptCategory.CORE,
                        prerequisites=["btree_node_split", "bplus_structure"], difficulty=0.5,
                        false_belief="Internal node splits in B+ Tree remove the median key"),
            ConceptNode("bplus_insert", "B+ Tree Insert Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_search", "bplus_leaf_split", "bplus_internal_split", "bplus_leaf_linkage"],
                        difficulty=0.7,
                        false_belief="B+ Tree insertion follows the same algorithm as B-Tree insertion"),
            ConceptNode("bplus_delete", "B+ Tree Delete Algorithm", ConceptCategory.OPERATION,
                        prerequisites=["bst_delete", "btree_borrow", "btree_merge", "bplus_leaf_linkage"],
                        difficulty=0.8,
                        false_belief="B+ Tree deletion never requires leaf linkage updates"),
        ]
        for c in bplus:
            self._concepts[c.id] = c
            self._tree_concepts["bplus_tree"].append(c.id)

    def _add_segment_concepts(self) -> None:
        seg = [
            ConceptNode("seg_range", "Segment Tree Range Representation", ConceptCategory.CORE,
                        prerequisites=["recursion", "array_indexing"], difficulty=0.4,
                        false_belief="A segment tree node's range is determined by its position in the array"),
            ConceptNode("seg_build", "Recursive Segment Tree Building", ConceptCategory.CORE,
                        prerequisites=["seg_range", "recursion"], difficulty=0.5,
                        false_belief="Building a segment tree takes the array and maps elements one-to-one"),
            ConceptNode("seg_point_update", "Point Update Propagation", ConceptCategory.CORE,
                        prerequisites=["seg_build", "recursion"], difficulty=0.4,
                        false_belief="A point update only changes the target leaf node"),
            ConceptNode("seg_range_query", "Range Query Composition", ConceptCategory.CORE,
                        prerequisites=["seg_build", "recursion"], difficulty=0.5,
                        false_belief="A range query visits every node in the query range"),
            ConceptNode("seg_range_update", "Range Update & Lazy Propagation", ConceptCategory.OPERATION,
                        prerequisites=["seg_point_update", "seg_range_query"], difficulty=0.8, is_hub=True,
                        false_belief="Lazy propagation means updates are delayed indefinitely"),
            ConceptNode("seg_lazy_push", "Lazy Tag Push-Down", ConceptCategory.CORE,
                        prerequisites=["seg_range_update"], difficulty=0.6,
                        false_belief="Lazy tags are automatically applied when children are accessed"),
        ]
        for c in seg:
            self._concepts[c.id] = c
            self._tree_concepts["segment_tree"].append(c.id)

    def _add_meta_concepts(self) -> None:
        meta = [
            ConceptNode("complexity_tradeoffs", "Tree Structure Complexity Trade-offs", ConceptCategory.META,
                        prerequisites=["big_o"], difficulty=0.6,
                        false_belief="All balanced trees have the same time complexity for all operations"),
            ConceptNode("invariant_maintenance", "Invariant Maintenance After Operations", ConceptCategory.META,
                        prerequisites=[], difficulty=0.5, is_hub=True,
                        false_belief="Tree invariants are checked only during initial learning, not real-world use"),
            ConceptNode("proof_techniques", "Tree Property Proof Techniques", ConceptCategory.META,
                        prerequisites=["recursion", "subtree_properties"], difficulty=0.7,
                        false_belief="Proofs about tree properties require global reasoning, not induction"),
        ]
        for c in meta:
            self._concepts[c.id] = c
            self._tree_concepts["meta"].append(c.id)

    def _add_violation_signatures(self) -> None:
        """Map every possible violation type to its primary and secondary concepts."""
        sigs = [
            # AVL
            ViolationSignature("balance_factor_exceeded", "avl", "avl_balance_factor",
                               secondary_concepts=["avl_rotation_cases", "avl_rotation_mechanics"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("bst_violation", "avl", "bst_property",
                               secondary_concepts=["avl_rotation_mechanics", "avl_insert"],
                               base_severity=SeverityLevel.CRITICAL, base_confidence=0.95),
            ViolationSignature("balance_factor_mismatch", "avl", "avl_balance_factor",
                               secondary_concepts=["tree_height", "avl_height_update"],
                               base_severity=SeverityLevel.MEDIUM, base_confidence=0.85),
            ViolationSignature("incorrect_height", "avl", "tree_height",
                               secondary_concepts=["avl_height_update"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("structural_violation", "avl", "pointer_manipulation",
                               secondary_concepts=["avl_rotation_mechanics"],
                               base_severity=SeverityLevel.CRITICAL, base_confidence=0.80),
            # Red-Black
            ViolationSignature("root_not_black", "red_black", "rb_properties",
                               secondary_concepts=["rb_insert_fixup"],
                               base_severity=SeverityLevel.MEDIUM, base_confidence=0.95),
            ViolationSignature("consecutive_red_nodes", "red_black", "rb_recoloring",
                               secondary_concepts=["rb_uncle_identification", "rb_rotation_mechanics"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.92),
            ViolationSignature("unequal_black_height", "red_black", "rb_black_height",
                               secondary_concepts=["rb_delete_fixup"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("bst_violation", "red_black", "bst_property",
                               secondary_concepts=["rb_rotation_mechanics"],
                               base_severity=SeverityLevel.CRITICAL, base_confidence=0.95),
            # Heap
            ViolationSignature("heap_property_violated", "heap", "heap_property",
                               secondary_concepts=["heap_sift_up", "heap_sift_down"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.88),
            ViolationSignature("structure_violation", "heap", "complete_binary_tree",
                               secondary_concepts=["heap_property"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.85),
            # B-Tree
            ViolationSignature("too_many_keys", "btree", "btree_node_split",
                               secondary_concepts=["btree_properties", "btree_cascading_split"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.92),
            ViolationSignature("too_few_keys", "btree", "btree_merge",
                               secondary_concepts=["btree_borrow", "btree_cascading_merge"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("unequal_leaf_depth", "btree", "btree_properties",
                               secondary_concepts=["btree_node_split", "btree_cascading_split"],
                               base_severity=SeverityLevel.CRITICAL, base_confidence=0.95),
            ViolationSignature("order_violation", "btree", "btree_properties",
                               secondary_concepts=["bst_property"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.93),
            # B+ Tree
            ViolationSignature("too_many_keys", "bplus_tree", "bplus_leaf_split",
                               secondary_concepts=["bplus_internal_split", "bplus_structure"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("too_few_keys", "bplus_tree", "bplus_delete",
                               secondary_concepts=["btree_merge", "bplus_leaf_linkage"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.88),
            ViolationSignature("leaf_linkage_broken", "bplus_tree", "bplus_leaf_linkage",
                               secondary_concepts=["bplus_leaf_split"],
                               base_severity=SeverityLevel.MEDIUM, base_confidence=0.85),
            ViolationSignature("unequal_leaf_depth", "bplus_tree", "bplus_structure",
                               secondary_concepts=["bplus_leaf_split", "bplus_internal_split"],
                               base_severity=SeverityLevel.CRITICAL, base_confidence=0.95),
            ViolationSignature("order_violation", "bplus_tree", "bplus_structure",
                               secondary_concepts=["bst_property"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.93),
            # Segment Tree
            ViolationSignature("invalid_range_sum", "segment_tree", "seg_build",
                               secondary_concepts=["seg_point_update"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.90),
            ViolationSignature("invalid_range_bounds", "segment_tree", "seg_range",
                               secondary_concepts=["seg_build"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.92),
            ViolationSignature("lazy_propagation_error", "segment_tree", "seg_range_update",
                               secondary_concepts=["seg_lazy_push"],
                               base_severity=SeverityLevel.HIGH, base_confidence=0.88),
            ViolationSignature("leaf_mismatch", "segment_tree", "seg_build",
                               secondary_concepts=["seg_range"],
                               base_severity=SeverityLevel.MEDIUM, base_confidence=0.85),
        ]
        for sig in sigs:
            key = f"{sig.tree_type}:{sig.violation_type}"
            self._violations[key] = sig

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        return self._concepts.get(concept_id)

    def get_violation_signature(self, tree_type: str, violation_type: str) -> Optional[ViolationSignature]:
        return self._violations.get(f"{tree_type}:{violation_type}")

    def get_concepts_for_tree(self, tree_type: str) -> List[ConceptNode]:
        ids = self._tree_concepts.get(tree_type, [])
        return [self._concepts[cid] for cid in ids if cid in self._concepts]

    def get_all_concepts(self) -> List[ConceptNode]:
        return list(self._concepts.values())

    def get_prerequisites(self, concept_id: str) -> List[ConceptNode]:
        concept = self._concepts.get(concept_id)
        if not concept:
            return []
        return [self._concepts[pid] for pid in concept.prerequisites if pid in self._concepts]

    def get_full_prerequisite_chain(self, concept_id: str) -> List[ConceptNode]:
        """Get the complete prerequisite chain (BFS) for a concept."""
        visited: Set[str] = set()
        chain: List[ConceptNode] = []
        queue = [concept_id]
        while queue:
            cid = queue.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            concept = self._concepts.get(cid)
            if concept:
                chain.append(concept)
                queue.extend(concept.prerequisites)
        return chain

    def get_prerequisite_hubs(self) -> List[ConceptNode]:
        """Concepts that serve as prerequisites for many others."""
        incoming = Counter()
        for c in self._concepts.values():
            for p in c.prerequisites:
                incoming[p] += 1
        hubs = [self._concepts[cid] for cid, count in incoming.most_common(10)
                if count >= 2 and cid in self._concepts]
        return hubs


# ==============================================================================
# III. Prerequisite Dependency Model
# ==============================================================================

class PrerequisiteModel:
    """
    DAG-based prerequisite reasoning engine.
    
    Infers which prerequisite concepts are likely weak based on:
      - Direct violation mapping
      - Violation patterns across concepts
      - Concept graph proximity
      - Historical weakness signals
    
    Uses Bayesian updating: P(weak | violation_evidence) for each concept.
    """

    def __init__(self, taxonomy: ConceptTaxonomy):
        self.taxonomy = taxonomy
        # Adjacency matrix: concept_id → set of dependent concepts
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._build_dependency_graph()

    def _build_dependency_graph(self) -> None:
        """Build reverse edges: concept → all concepts that depend on it."""
        for c in self.taxonomy.get_all_concepts():
            for prereq_id in c.prerequisites:
                self._dependents[prereq_id].add(c.id)

    def infer_weak_prerequisites(
        self,
        violated_concepts: List[str],
        mastery_scores: Dict[str, float],
        history: List[StudentHistoryEntry],
    ) -> List[Tuple[str, float]]:
        """
        Given violated concepts, infer which prerequisites are weak.
        
        Returns: list of (concept_id, weakness_probability) tuples.
        
        Inference rules:
          1. Direct: if a concept is violated, it's likely weak
          2. Prerequisite failure: if a concept is violated, its prerequisites 
             are also suspect (especially hub prerequisites)
          3. Repeated patterns: if multiple dependent concepts fail, the
             shared prerequisite is very likely weak
          4. Historical: if the prerequisite was weak before, it likely still is
        """
        weakness: Dict[str, float] = {}

        # Rule 1: Direct violation → high weakness
        for cid in violated_concepts:
            weakness[cid] = max(weakness.get(cid, 0), 0.9)

        # Rule 2: Prerequisite failure propagation
        for cid in violated_concepts:
            chain = self.taxonomy.get_full_prerequisite_chain(cid)
            for i, prereq in enumerate(chain):
                if prereq.id == cid:
                    continue
                # Decay confidence with distance
                distance = len(chain) - i
                prob = max(0.3, 0.8 - (distance - 1) * 0.15)
                weakness[prereq.id] = max(weakness.get(prereq.id, 0), prob)

        # Rule 3: Shared prerequisite pattern
        if len(violated_concepts) >= 2:
            for cid in violated_concepts:
                concept = self.taxonomy.get_concept(cid)
                if not concept:
                    continue
                for prereq_id in concept.prerequisites:
                    # Count how many violated concepts share this prerequisite
                    sharing = sum(
                        1 for vc in violated_concepts
                        if prereq_id in (self.taxonomy.get_concept(vc) or ConceptNode("", "", ConceptCategory.PREREQUISITE)).prerequisites
                    )
                    if sharing >= 2:
                        weakness[prereq_id] = max(weakness.get(prereq_id, 0), 0.7 + 0.1 * sharing)

        # Rule 4: Historical weakness
        for entry in history:
            if not entry.success:
                for cid in entry.concepts_tested:
                    weakness[cid] = max(weakness.get(cid, 0), 0.5)

        # Merge with existing mastery scores
        for cid in list(weakness.keys()):
            mastery = mastery_scores.get(cid, 0.5)
            if mastery > 0.7:
                weakness[cid] *= (1 - mastery)

        return sorted(weakness.items(), key=lambda x: -x[1])

    def get_impact_propagation(self, weak_concepts: List[str]) -> Dict[str, List[str]]:
        """
        Given weak concepts, determine which downstream concepts are affected.
        Returns: {affected_concept: [path_of_weak_prerequisites]}
        """
        impact: Dict[str, List[str]] = {}
        weak_set = set(weak_concepts)

        for c in self.taxonomy.get_all_concepts():
            chain = self.taxonomy.get_full_prerequisite_chain(c.id)
            broken = [p.id for p in chain if p.id in weak_set]
            if broken:
                impact[c.id] = broken

        return impact


# ==============================================================================
# IV. Inference Engine — Multi-Signal Root Cause Analysis
# ==============================================================================

class InferenceEngine:
    """
    Combines direct violation mapping, pattern recognition, and
    prerequisite propagation to infer the true conceptual misunderstanding.
    """

    def __init__(self, taxonomy: ConceptTaxonomy, prereq_model: PrerequisiteModel):
        self.taxonomy = taxonomy
        self.prereq_model = prereq_model

    def analyze(
        self,
        tree_type: str,
        operation: str,
        violations: List[Dict[str, Any]],
        profile: StudentProfile,
    ) -> List[MisconceptionDiagnosis]:
        if not violations:
            return []

        # Phase 1: Direct mapping of violations to concepts
        direct_concepts = self._map_violations_direct(tree_type, violations)

        # Phase 2: Pattern recognition on the violation set
        pattern = self._recognize_pattern(violations, direct_concepts, profile)

        # Phase 3: Infer root causes via prerequisite propagation
        weak_prereqs = self.prereq_model.infer_weak_prerequisites(
            [c[0] for c in direct_concepts],
            profile.concept_mastery,
            profile.history,
        )

        # Phase 4: Build diagnoses for each affected concept
        diagnoses = self._build_diagnoses(
            direct_concepts, pattern, weak_prereqs, violations,
        )

        # Phase 5: Merge overlapping diagnoses (keep highest confidence)
        diagnoses = self._merge_diagnoses(diagnoses)

        return diagnoses

    def _map_violations_direct(
        self,
        tree_type: str,
        violations: List[Dict],
    ) -> List[Tuple[str, float, ViolationSignature]]:
        """Map violations to primary concepts with confidence scores."""
        results: List[Tuple[str, float, ViolationSignature]] = []
        for v in violations:
            vtype = v.get("type", v.get("rule_id", "unknown"))
            sig = self.taxonomy.get_violation_signature(tree_type, vtype)
            if sig:
                results.append((sig.primary_concept, sig.base_confidence, sig))
                for secondary in sig.secondary_concepts:
                    results.append((secondary, sig.base_confidence * 0.6, sig))
        return results

    def _recognize_pattern(
        self,
        violations: List[Dict],
        direct_concepts: List[Tuple[str, float, Any]],
        profile: StudentProfile,
    ) -> MisconceptionPattern:
        """
        Classify the violation pattern from evidence.
        
        Patterns:
          SURFACE_SLIP:          1 violation, high mastery elsewhere
          CONCEPT_GAP:           Repeated same violation type
          PREREQUISITE_HOLE:     Violations span multiple tree types
          CONFUSION:             Different violation types for same tree
          PROCEDURAL_ERROR:      Single operation context, mechanical mistake
          PERSISTENT_MISCONCEPTION: Same violation across 3+ sessions
          COMPOUND_FAILURE:      Multiple different violations simultaneously
        """
        concept_ids = [c[0] for c in direct_concepts]
        unique_violation_types = set(v.get("type", "") for v in violations)

        # Check for persistent misconception (same violation in 3+ sessions)
        if profile.misconception_history:
            for cid in concept_ids:
                records = profile.misconception_history.get(cid, [])
                if len(records) >= 3:
                    return MisconceptionPattern.PERSISTENT_MISCONCEPTION

        # Check for prerequisite hole (violations across tree types)
        tree_types_in_history = set(e.tree_type for e in profile.history)
        if len(tree_types_in_history) >= 2:
            return MisconceptionPattern.PREREQUISITE_HOLE

        # Check for compound failure (many different violations)
        if len(unique_violation_types) >= 3:
            return MisconceptionPattern.COMPOUND_FAILURE

        # Check for confusion (different violation types, same concept)
        if len(unique_violation_types) >= 2:
            return MisconceptionPattern.CONFUSION

        # Check for concept gap (repeated same violation)
        for entry in reversed(profile.history[-10:]):
            for v in entry.violations:
                if v.get("type") == violations[0].get("type"):
                    return MisconceptionPattern.CONCEPT_GAP

        # Check for surface slip
        mastery_ok = all(
            profile.concept_mastery.get(cid, 0) > 0.5
            for cid in concept_ids
        )
        if mastery_ok and len(violations) == 1:
            return MisconceptionPattern.SURFACE_SLIP

        return MisconceptionPattern.PROCEDURAL_ERROR

    def _build_diagnoses(
        self,
        direct_concepts: List[Tuple[str, float, Any]],
        pattern: MisconceptionPattern,
        weak_prereqs: List[Tuple[str, float]],
        violations: List[Dict],
    ) -> List[MisconceptionDiagnosis]:
        """Build structured diagnoses from all evidence."""
        diagnoses: Dict[str, MisconceptionDiagnosis] = {}

        for concept_id, confidence, sig in direct_concepts:
            concept = self.taxonomy.get_concept(concept_id)
            if not concept:
                continue

            # Compute pattern-adjusted confidence
            adjusted_conf = self._adjust_confidence(confidence, pattern, concept_id)

            # Find prerequisite gaps
            gaps = [p.name for p in self.taxonomy.get_prerequisites(concept_id)]

            # Check if any weak prereqs are relevant
            weak_prereq_ids = {pid for pid, _ in weak_prereqs}
            matching_gaps = [p.name for p in self.taxonomy.get_prerequisites(concept_id)
                             if p.id in weak_prereq_ids]

            diagnosis = MisconceptionDiagnosis(
                concept_id=concept_id,
                concept_name=concept.name,
                pattern=pattern,
                root_cause=self._infer_root_cause(concept, pattern),
                description=self._build_description(concept, pattern, sig),
                false_belief=concept.false_belief,
                severity=sig.base_severity,
                confidence=adjusted_conf,
                prerequisite_gaps=gaps if matching_gaps else [],
                affected_operations=self._affected_operations(concept_id),
                analogous_to=concept.analogous_concepts,
            )
            diagnoses[concept_id] = diagnosis

        return list(diagnoses.values())

    def _adjust_confidence(self, base_confidence: float, pattern: MisconceptionPattern,
                           concept_id: str) -> float:
        """Adjust confidence based on pattern type."""
        factors = {
            MisconceptionPattern.SURFACE_SLIP: 0.6,
            MisconceptionPattern.CONCEPT_GAP: 0.9,
            MisconceptionPattern.PREREQUISITE_HOLE: 0.8,
            MisconceptionPattern.CONFUSION: 0.7,
            MisconceptionPattern.PROCEDURAL_ERROR: 0.75,
            MisconceptionPattern.PERSISTENT_MISCONCEPTION: 0.95,
            MisconceptionPattern.COMPOUND_FAILURE: 0.85,
        }
        return min(1.0, base_confidence * factors.get(pattern, 0.8))

    def _infer_root_cause(self, concept: ConceptNode, pattern: MisconceptionPattern) -> str:
        """Infer the root cause of the misconception based on evidence."""
        if pattern == MisconceptionPattern.PREREQUISITE_HOLE:
            prereq_names = [p.name for p in self.taxonomy.get_prerequisites(concept.id)]
            if prereq_names:
                return f"Weak foundational understanding: {prereq_names[0]}"
            return "Missing prerequisite concepts needed for this topic"

        if pattern == MisconceptionPattern.PERSISTENT_MISCONCEPTION:
            return f"Deeply ingrained misconception about {concept.name} that resists correction"

        if pattern == MisconceptionPattern.CONFUSION:
            analogies = concept.analogous_concepts
            if analogies:
                return f"Confusion between {concept.name} and analogous concept {analogies[0]}"
            return f"Uncertain application of {concept.name}"

        if pattern == MisconceptionPattern.CONCEPT_GAP:
            return f"Never fully understood {concept.name}"

        if pattern == MisconceptionPattern.COMPOUND_FAILURE:
            return f"Multiple simultaneous misunderstandings around {concept.name}"

        return f"Incomplete understanding of {concept.name}"

    def _build_description(self, concept: ConceptNode, pattern: MisconceptionPattern,
                           sig: ViolationSignature) -> str:
        """Build a natural-language description of the diagnosis."""
        base = f"Student's violation of '{sig.violation_type}' in {sig.tree_type} "
        if pattern == MisconceptionPattern.SURFACE_SLIP:
            return base + f"appears to be a surface-level slip. Core understanding of {concept.name} is intact."
        if pattern == MisconceptionPattern.CONCEPT_GAP:
            return base + f"indicates a persistent gap in understanding {concept.name}."
        if pattern == MisconceptionPattern.PREREQUISITE_HOLE:
            return base + f"suggests prerequisite knowledge of {concept.name} is underdeveloped."
        return base + f"indicates a misunderstanding of {concept.name}."

    def _affected_operations(self, concept_id: str) -> List[str]:
        """Determine which operations are affected by this misconception."""
        concept = self.taxonomy.get_concept(concept_id)
        if not concept:
            return []
        if concept.category == ConceptCategory.OPERATION:
            return [concept_id]
        # Find all operation concepts that depend on this
        affected = []
        for c in self.taxonomy.get_all_concepts():
            if c.category == ConceptCategory.OPERATION:
                chain_ids = {p.id for p in self.taxonomy.get_full_prerequisite_chain(c.id)}
                if concept_id in chain_ids:
                    affected.append(c.id)
        return affected

    def _merge_diagnoses(self, diagnoses: List[MisconceptionDiagnosis]) -> List[MisconceptionDiagnosis]:
        """Merge overlapping diagnoses by keeping the highest confidence per concept."""
        best: Dict[str, MisconceptionDiagnosis] = {}
        for d in diagnoses:
            if d.concept_id not in best or d.confidence > best[d.concept_id].confidence:
                best[d.concept_id] = d
        return sorted(best.values(), key=lambda d: (d.severity.value, d.confidence), reverse=True)


# ==============================================================================
# V. Severity Scorer — Multi-Factor Severity Calculation
# ==============================================================================

class SeverityScorer:
    """
    Computes severity from multiple factors:
    
      severity = min(CRITICAL, round(
          base_severity 
          * recency_multiplier(history)
          * frequency_multiplier(repeat_count)
          * hub_multiplier(is_hub)
          * prerequisite_impact(num_dependents)
          * pattern_multiplier(pattern)
      ))
    """

    def __init__(self, taxonomy: ConceptTaxonomy, prereq_model: PrerequisiteModel):
        self.taxonomy = taxonomy
        self.prereq_model = prereq_model

    def compute(
        self,
        diagnosis: MisconceptionDiagnosis,
        profile: StudentProfile,
    ) -> SeverityLevel:
        base = diagnosis.severity.value
        if base == 0:
            return SeverityLevel.NONE

        concept = self.taxonomy.get_concept(diagnosis.concept_id)

        # Factor 1: Base severity
        severity = float(base)

        # Factor 2: Recency — recent violations are more severe
        recency_mult = self._recency_multiplier(diagnosis.concept_id, profile)
        severity *= recency_mult

        # Factor 3: Frequency — repeated violations escalate
        freq_mult = self._frequency_multiplier(diagnosis.concept_id, profile)
        severity *= freq_mult

        # Factor 4: Hub penalty — weak hub concepts cascade to many dependents
        if concept and concept.is_hub:
            severity *= 1.5

        # Factor 5: Prerequisite impact — how many dependents are blocked
        impact = self.prereq_model.get_impact_propagation([diagnosis.concept_id])
        num_affected = len(impact)
        if num_affected > 3:
            severity *= 1.3
        elif num_affected > 0:
            severity *= 1.1

        # Factor 6: Pattern multiplier
        pattern_mult = {
            MisconceptionPattern.SURFACE_SLIP: 0.7,
            MisconceptionPattern.CONCEPT_GAP: 1.3,
            MisconceptionPattern.PREREQUISITE_HOLE: 1.5,
            MisconceptionPattern.CONFUSION: 1.1,
            MisconceptionPattern.PROCEDURAL_ERROR: 1.0,
            MisconceptionPattern.PERSISTENT_MISCONCEPTION: 1.8,
            MisconceptionPattern.COMPOUND_FAILURE: 1.4,
        }
        severity *= pattern_mult.get(diagnosis.pattern, 1.0)

        # Clamp to valid range
        severity = max(1.0, min(4.0, severity))
        return SeverityLevel(round(severity))

    def _recency_multiplier(self, concept_id: str, profile: StudentProfile) -> float:
        """Recent violations increase severity."""
        timestamps = profile.misconception_history.get(concept_id, [])
        if not timestamps:
            return 1.0

        # Most recent violation
        now = datetime.now()
        most_recent = timestamps[-1]
        days_ago = (now - most_recent).total_seconds() / 86400

        if days_ago < 0.01:  # Current session
            return 1.5
        if days_ago < 1:  # Within last day
            return 1.3
        if days_ago < 7:  # Within last week
            return 1.1
        return 1.0

    def _frequency_multiplier(self, concept_id: str, profile: StudentProfile) -> float:
        """Repeated violations increase severity multiplicatively."""
        records = profile.misconception_history.get(concept_id, [])
        count = len(records)

        if count == 0:
            return 1.0
        if count == 1:
            return 1.0
        if count == 2:
            return 1.25
        if count == 3:
            return 1.5
        if count >= 4:
            return min(2.0, 1.5 + 0.15 * (count - 3))

        return 1.0


# ==============================================================================
# VI. Remediation Engine — Adaptive Learning Path Generator
# ==============================================================================

class RemediationEngine:
    """
    Generates adaptive remediation plans based on diagnoses.
    
    Strategy:
      1. If prerequisite gaps exist → review prerequisites first
      2. If core concept is weak → targeted practice with scaffolding
      3. If operation is weak → guided exercises with trace
      4. If persistent → change approach, use analogies and Socratic questioning
    """

    def __init__(self, taxonomy: ConceptTaxonomy):
        self.taxonomy = taxonomy
        self.exercise_bank = self._build_exercise_bank()

    @staticmethod
    def _build_exercise_bank() -> Dict[str, List[Dict]]:
        """Exercises indexed by concept_id they target."""
        return {
            "bst_property": [
                {"type": "verification", "desc": "Given a tree, identify BST ordering violations"},
                {"type": "construction", "desc": "Insert keys into a BST tracking the comparison path"},
            ],
            "tree_height": [
                {"type": "computation", "desc": "Compute height of each node in a given tree"},
                {"type": "comparison", "desc": "Distinguish between height and depth for leaf nodes"},
            ],
            "avl_balance_factor": [
                {"type": "computation", "desc": "Compute balance factors for all nodes in an AVL tree"},
                {"type": "identification", "desc": "Identify which nodes violate AVL balance property"},
            ],
            "avl_rotation_mechanics": [
                {"type": "trace", "desc": "Trace pointer changes during a right rotation step-by-step"},
                {"type": "construction", "desc": "Draw the result after applying a left rotation to a given subtree"},
            ],
            "avl_rotation_cases": [
                {"type": "classification", "desc": "Classify each imbalance as LL, RR, LR, or RL"},
                {"type": "paired", "desc": "For each case, pair it with the correct rotation sequence"},
            ],
            "avl_insert": [
                {"type": "guided", "desc": "Insert 10, 20, 30 into an AVL tree with step-by-step guidance"},
                {"type": "unguided", "desc": "Insert 50, 25, 75, 12, 37 into an AVL tree and verify"},
                {"type": "debug", "desc": "Given a flawed AVL insertion trace, identify which step was wrong"},
            ],
            "rb_properties": [
                {"type": "verification", "desc": "Verify all 5 RB properties hold for a given tree"},
                {"type": "correction", "desc": "Fix a tree that violates one RB property at a time"},
            ],
            "rb_recoloring": [
                {"type": "simulation", "desc": "Simulate recoloring when uncle is RED during fix-up"},
                {"type": "classification", "desc": "Given a red-red violation, determine if uncle is RED or BLACK"},
            ],
            "heap_property": [
                {"type": "verification", "desc": "Given an array, verify heap property for all parent-child pairs"},
                {"type": "conversion", "desc": "Convert between min-heap and max-heap representations"},
            ],
            "btree_node_split": [
                {"type": "simulation", "desc": "Split a full B-Tree node (2t-1 keys) and identify median"},
                {"type": "trace", "desc": "Trace cascading split from leaf to root"},
            ],
            "seg_range_query": [
                {"type": "trace", "desc": "Given a segment tree, trace the nodes visited for a range query [2, 7]"},
                {"type": "construction", "desc": "Build a segment tree and answer range sum queries"},
            ],
            "seg_range_update": [
                {"type": "guided", "desc": "Perform a range update with lazy propagation step-by-step"},
                {"type": "debug", "desc": "Find the lazy propagation error in a given trace"},
            ],
        }

    def generate_plan(
        self,
        diagnoses: List[MisconceptionDiagnosis],
        profile: StudentProfile,
        tree_type: str,
        operation: str,
    ) -> RemediationPlan:
        if not diagnoses:
            return RemediationPlan(overall_severity=SeverityLevel.NONE,
                                    recommended_focus="No issues detected.")

        # Sort diagnoses by severity then confidence
        sorted_diags = sorted(
            diagnoses,
            key=lambda d: (d.severity.value, d.confidence),
            reverse=True,
        )

        path: List[RemediationPath] = []
        critical_gaps: List[str] = []
        visited_concepts: Set[str] = set()

        for diag in sorted_diags:
            concept = self.taxonomy.get_concept(diag.concept_id)
            if not concept:
                continue

            # Step 1: Review prerequisites if gaps exist
            if diag.prerequisite_gaps:
                for prereq in self.taxonomy.get_prerequisites(diag.concept_id):
                    if prereq.id not in visited_concepts:
                        mastery = profile.concept_mastery.get(prereq.id, 0)
                        path.append(RemediationPath(
                            step_type="review_prerequisite",
                            concept_id=prereq.id,
                            description=f"Review: {prereq.name} — needed to understand {diag.concept_name}",
                            estimated_difficulty=prereq.difficulty,
                            prerequisites_met=True,
                            estimated_mastery_gain=0.15,
                        ))
                        visited_concepts.add(prereq.id)

            # Step 2: Core explanation of the misconception
            if diag.concept_id not in visited_concepts:
                path.append(RemediationPath(
                    step_type="concept_explanation",
                    concept_id=diag.concept_id,
                    description=f"Understand: {diag.concept_name} — {diag.description}",
                    estimated_difficulty=concept.difficulty,
                    prerequisites_met=self._prerequisites_met(diag.concept_id, profile),
                    estimated_mastery_gain=0.1,
                ))
                visited_concepts.add(diag.concept_id)

            # Step 3: Targeted practice exercises
            exercises = self.exercise_bank.get(diag.concept_id, [])
            for ex in exercises:
                if ex["type"] == "debug" and diag.pattern == MisconceptionPattern.PERSISTENT_MISCONCEPTION:
                    continue
                path.append(RemediationPath(
                    step_type="targeted_practice",
                    concept_id=diag.concept_id,
                    description=ex["desc"],
                    estimated_difficulty=concept.difficulty + (0.2 if ex["type"] == "unguided" else 0),
                    prerequisites_met=self._prerequisites_met(diag.concept_id, profile),
                    estimated_mastery_gain=0.12,
                ))

            # Step 4: Analogous concepts if confusion pattern
            if diag.pattern == MisconceptionPattern.CONFUSION and diag.analogous_to:
                for analog in diag.analogous_to:
                    analog_concept = self.taxonomy.get_concept(analog)
                    if analog_concept and analog not in visited_concepts:
                        path.append(RemediationPath(
                            step_type="guided_exercise",
                            concept_id=analog,
                            description=f"Compare: {diag.concept_name} vs {analog_concept.name} — identify key differences",
                            estimated_difficulty=concept.difficulty + 0.1,
                            prerequisites_met=True,
                            estimated_mastery_gain=0.1,
                        ))

            # Track critical gaps
            if diag.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
                critical_gaps.append(diag.concept_name)

        # Estimate sessions needed
        estimated_sessions = max(1, math.ceil(len(path) / 4))

        # Determine overall severity
        overall = max(
            (d.severity for d in sorted_diags),
            key=lambda s: s.value,
        )

        # Build focus recommendation
        if critical_gaps:
            focus = f"Focus on: {', '.join(critical_gaps[:3])}"
        else:
            focus = "Reinforce current understanding with additional practice."

        return RemediationPlan(
            diagnoses=sorted_diags,
            overall_severity=overall,
            learning_path=path,
            critical_gaps=critical_gaps,
            recommended_focus=focus,
            estimated_sessions=estimated_sessions,
        )

    def _prerequisites_met(self, concept_id: str, profile: StudentProfile) -> bool:
        """Check if all prerequisites for a concept have sufficient mastery."""
        concept = self.taxonomy.get_concept(concept_id)
        if not concept:
            return True
        for prereq_id in concept.prerequisites:
            mastery = profile.concept_mastery.get(prereq_id, 0)
            if mastery < 0.5:
                return False
        return True


# ==============================================================================
# VII. Student Profile Manager — Tracks History & Mastery
# ==============================================================================

class StudentProfileManager:
    """
    Manages and queries student learning profiles.
    Tracks mastery, misconception history, and operation patterns.
    """

    def __init__(self, taxonomy: ConceptTaxonomy):
        self.taxonomy = taxonomy

    def record_attempt(
        self,
        profile: StudentProfile,
        tree_type: str,
        operation: str,
        violations: List[Dict],
        success: bool,
        diagnoses: List[MisconceptionDiagnosis],
    ) -> StudentProfile:
        """Record a student interaction and update profile."""
        entry = StudentHistoryEntry(
            timestamp=datetime.now().timestamp(),
            tree_type=tree_type,
            operation=operation,
            violations=violations,
            success=success,
        )

        profile.history.append(entry)
        profile.total_attempts += 1

        # Update concept mastery based on success/failure
        for diag in diagnoses:
            concept_id = diag.concept_id
            if concept_id not in profile.concept_mastery:
                profile.concept_mastery[concept_id] = 0.5

            if success:
                boost = 0.12 * (1 - profile.concept_mastery[concept_id])
                profile.concept_mastery[concept_id] = min(1.0,
                    profile.concept_mastery[concept_id] + boost)
            else:
                penalty = 0.15 * profile.concept_mastery[concept_id]
                profile.concept_mastery[concept_id] = max(0.0,
                    profile.concept_mastery[concept_id] - penalty)

            # Track misconception history
            if not success:
                if concept_id not in profile.misconception_history:
                    profile.misconception_history[concept_id] = []
                profile.misconception_history[concept_id].append(datetime.now())
                profile.weak_concepts.add(concept_id)

        # Also update for concepts that were tested but not diagnosed
        for v in violations:
            vtype = v.get("type", v.get("rule_id", "unknown"))
            sig = self.taxonomy.get_violation_signature(tree_type, vtype)
            if sig:
                cid = sig.primary_concept
                if cid not in profile.concept_mastery:
                    profile.concept_mastery[cid] = 0.5
                profile.concept_mastery[cid] = max(0.0,
                    profile.concept_mastery[cid] - 0.05)

        entry.diagnosis_snapshot = {
            d.concept_id: d.confidence for d in diagnoses
        } if diagnoses else None

        entry.concepts_tested = [
            d.concept_id for d in diagnoses
        ] if diagnoses else []

        return profile

    def get_mastery_summary(self, profile: StudentProfile, tree_type: str) -> Dict[str, Any]:
        """Get a summary of mastery for a specific tree type."""
        concepts = self.taxonomy.get_concepts_for_tree(tree_type)
        mastery_data = []
        for c in concepts:
            score = profile.concept_mastery.get(c.id, 0.5)
            records = profile.misconception_history.get(c.id, [])
            mastery_data.append({
                "concept_id": c.id,
                "concept_name": c.name,
                "category": c.category.value,
                "mastery": round(score, 2),
                "misconception_count": len(records),
                "is_hub": c.is_hub,
                "weak": score < 0.4,
            })

        # Calculate overall
        scores = [d["mastery"] for d in mastery_data]
        avg = sum(scores) / len(scores) if scores else 0

        return {
            "tree_type": tree_type,
            "concepts": mastery_data,
            "overall_mastery": round(avg, 2),
            "weak_concepts": [d for d in mastery_data if d["weak"]],
            "total_misconceptions": sum(d["misconception_count"] for d in mastery_data),
        }


# ==============================================================================
# VIII. Main Engine — Integrated Facade
# ==============================================================================

class MisconceptionEngine:
    """
    Integrated misconception detection engine.
    
    Usage:
        engine = MisconceptionEngine()
        profile = engine.create_profile()
        
        # After each operation:
        diagnoses = engine.analyze(profile, "avl", "insert", violations)
        plan = engine.remediate(profile, diagnoses, "avl", "insert")
        
        # Check mastery:
        summary = engine.get_mastery_summary(profile, "avl")
    """

    def __init__(self):
        self.taxonomy = ConceptTaxonomy()
        self.prereq_model = PrerequisiteModel(self.taxonomy)
        self.inference = InferenceEngine(self.taxonomy, self.prereq_model)
        self.severity = SeverityScorer(self.taxonomy, self.prereq_model)
        self.remediation = RemediationEngine(self.taxonomy)
        self.profile_manager = StudentProfileManager(self.taxonomy)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_profile(self) -> StudentProfile:
        """Create a new student profile."""
        return StudentProfile()

    def analyze(
        self,
        profile: StudentProfile,
        tree_type: str,
        operation: str,
        violations: List[Dict[str, Any]],
    ) -> List[MisconceptionDiagnosis]:
        """
        Analyze violations and produce misconception diagnoses.
        
        Args:
            profile: Student's learning profile
            tree_type: 'avl', 'red_black', etc.
            operation: 'insert', 'delete', 'search'
            violations: List of violation dicts from validator
        
        Returns:
            List of MisconceptionDiagnosis objects
        """
        diagnoses = self.inference.analyze(tree_type, operation, violations, profile)

        # Score severity for each
        for d in diagnoses:
            d.severity = self.severity.compute(d, profile)

        # Record to profile
        success = len(violations) == 0
        self.profile_manager.record_attempt(
            profile, tree_type, operation, violations, success, diagnoses,
        )

        return diagnoses

    def remediate(
        self,
        profile: StudentProfile,
        diagnoses: List[MisconceptionDiagnosis],
        tree_type: str,
        operation: str,
    ) -> RemediationPlan:
        """
        Generate an adaptive remediation plan from diagnoses.
        
        Args:
            profile: Student's learning profile
            diagnoses: Output from analyze()
            tree_type: Current tree type
            operation: Current operation
        
        Returns:
            RemediationPlan with learning path
        """
        return self.remediation.generate_plan(diagnoses, profile, tree_type, operation)

    def get_mastery_summary(self, profile: StudentProfile, tree_type: str) -> Dict[str, Any]:
        """Get structured mastery summary for a tree type."""
        return self.profile_manager.get_mastery_summary(profile, tree_type)

    def get_profile_summary(self, profile: StudentProfile) -> Dict[str, Any]:
        """Get a compact summary of the student's overall state."""
        weak = sorted(
            [(cid, score) for cid, score in profile.concept_mastery.items()
             if score < 0.4],
            key=lambda x: x[1],
        )
        total_misconceptions = sum(
            len(records) for records in profile.misconception_history.values()
        )
        return {
            "total_attempts": profile.total_attempts,
            "total_misconceptions": total_misconceptions,
            "weak_concepts": [
                {"concept_id": cid, "mastery": round(score, 2)}
                for cid, score in weak[:5]
            ],
            "persistent_issues": [
                cid for cid, records in profile.misconception_history.items()
                if len(records) >= 3
            ],
        }

    def query_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific concept."""
        concept = self.taxonomy.get_concept(concept_id)
        if not concept:
            return None
        prereq_names = [p.name for p in self.taxonomy.get_prerequisites(concept_id)]
        return {
            "id": concept.id,
            "name": concept.name,
            "category": concept.category.value,
            "difficulty": concept.difficulty,
            "is_hub": concept.is_hub,
            "false_belief": concept.false_belief,
            "prerequisites": prereq_names,
            "analogous_to": concept.analogous_concepts,
        }


# ==============================================================================
# IX. Convenience Function — One-Call Interface
# ==============================================================================

_engine: Optional[MisconceptionEngine] = None


def get_engine() -> MisconceptionEngine:
    """Get or create the singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = MisconceptionEngine()
    return _engine


def detect_misconceptions(
    tree_type: str,
    operation: str,
    violations: List[Dict[str, Any]],
    student_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    One-call interface. Returns serializable diagnosis dict.
    
    Example:
        result = detect_misconceptions(
            tree_type='avl',
            operation='insert',
            violations=[{'type': 'balance_factor_exceeded', 'node': 20}],
        )
    """
    engine = get_engine()
    profile = engine.create_profile()

    # Populate profile from history if provided
    if student_history:
        for entry in student_history:
            engine.analyze(
                profile,
                entry.get("tree_type", tree_type),
                entry.get("operation", operation),
                entry.get("violations", []),
            )

    diagnoses = engine.analyze(profile, tree_type, operation, violations)
    plan = engine.remediate(profile, diagnoses, tree_type, operation)

    return {
        "misconceptions": [
            {
                "concept_id": d.concept_id,
                "concept_name": d.concept_name,
                "pattern": d.pattern.value,
                "root_cause": d.root_cause,
                "description": d.description,
                "false_belief": d.false_belief,
                "severity": d.severity.name.lower(),
                "confidence": round(d.confidence, 2),
                "prerequisite_gaps": d.prerequisite_gaps,
                "affected_operations": d.affected_operations,
            }
            for d in plan.diagnoses
        ],
        "overall_severity": plan.overall_severity.name.lower(),
        "weak_concepts": list(set(d.concept_name for d in plan.diagnoses)),
        "critical_gaps": plan.critical_gaps,
        "recommended_focus": plan.recommended_focus,
        "estimated_sessions": plan.estimated_sessions,
        "learning_path": [
            {
                "step_type": p.step_type,
                "description": p.description,
                "prerequisites_met": p.prerequisites_met,
                "estimated_mastery_gain": p.estimated_mastery_gain,
            }
            for p in plan.learning_path[:8]
        ],
        "profile_summary": engine.get_profile_summary(profile),
    }
