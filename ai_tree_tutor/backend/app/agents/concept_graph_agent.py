"""
Concept Graph Agent v3 — Weighted Prerequisite Knowledge Graph
================================================================
Enhanced with:
  1. Weighted prerequisite edges (0.0-1.0 importance)
  2. Confidence scores per concept mastery estimate
  3. Misconception propagation through downstream dependents
  4. Mastery decay over time (forgetting curve)
  5. Adaptive learning recommendations
  6. Prerequisite impact scoring (blocked concepts)
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from app.agents.base_agent import BaseAgent
from app.agents.misconception_engine import ConceptTaxonomy, ConceptCategory
from app.context.agent_context import AgentContext


# ==============================================================================
# Weighted Graph Models
# ==============================================================================

# Default edge weights: how much a concept depends on each prerequisite
PREREQUISITE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "avl_balance_factor": {"tree_height": 0.9, "bst_property": 0.7},
    "avl_rotation_cases": {"avl_balance_factor": 0.9, "avl_rotation_mechanics": 0.8},
    "avl_insert": {"bst_search": 0.9, "avl_balance_factor": 0.8, "avl_rotation_cases": 0.9, "avl_height_update": 0.7},
    "avl_delete": {"bst_delete": 0.9, "avl_insert": 0.7},
    "rb_recoloring": {"rb_properties": 0.9},
    "rb_rotation_mechanics": {"rb_recoloring": 0.7, "pointer_manipulation": 0.8},
    "rb_insert_fixup": {"bst_search": 0.9, "rb_uncle_identification": 0.8, "rb_recoloring": 0.9, "rb_rotation_mechanics": 0.9},
    "rb_delete_fixup": {"bst_delete": 0.9, "rb_insert_fixup": 0.8},
    "rb_black_height": {"rb_properties": 0.8, "tree_height": 0.6},
    "heap_sift_up": {"heap_property": 0.9, "array_indexing": 0.7},
    "heap_sift_down": {"heap_property": 0.9, "array_indexing": 0.7},
    "heapify": {"heap_sift_down": 0.9},
    "btree_node_split": {"btree_properties": 0.9},
    "btree_cascading_split": {"btree_node_split": 0.9, "recursion": 0.7},
    "btree_merge": {"btree_properties": 0.9, "btree_borrow": 0.7},
    "seg_build": {"seg_range": 0.9, "recursion": 0.8},
    "seg_range_query": {"seg_build": 0.9, "recursion": 0.7},
    "seg_range_update": {"seg_point_update": 0.8, "seg_range_query": 0.7},
}

# Decay parameters (Ebbinghaus forgetting curve)
DECAY_HALF_LIFE_DAYS: Dict[str, float] = {
    ConceptCategory.PREREQUISITE.value: 30.0,  # Prerequisites decay slowly
    ConceptCategory.CORE.value: 14.0,          # Core concepts: 2 weeks
    ConceptCategory.OPERATION.value: 7.0,      # Operation details: 1 week
    ConceptCategory.META.value: 21.0,          # Meta insights: 3 weeks
}


@dataclass
class ConceptMastery:
    """Enhanced mastery tracking per concept."""
    value: float = 0.5       # 0.0-1.0 mastery estimate
    confidence: float = 0.3   # 0.0-1.0 confidence in the estimate
    attempts: int = 0
    mistakes: int = 0
    streak: int = 0           # consecutive correct attempts
    last_attempt_time: float = 0.0
    last_decay_time: float = 0.0
    misconception_count: int = 0


@dataclass
class LearningRecommendation:
    """A single actionable learning recommendation."""
    concept_id: str
    concept_name: str
    recommendation_type: str  # 'review_prerequisite', 'practice_concept', 'remediate_misconception', 'advance'
    priority: int             # 1-5 (5 = highest)
    reason: str
    estimated_impact: float   # 0.0-1.0 how much this will improve overall mastery
    suggested_exercises: List[str] = field(default_factory=list)


# ==============================================================================
# Main Agent
# ==============================================================================

class ConceptGraphAgent(BaseAgent):
    """
    Weighted knowledge graph with mastery tracking, confidence estimation,
    temporal decay, misconception propagation, and adaptive recommendations.
    """

    def __init__(self):
        self.taxonomy = ConceptTaxonomy()
        self.graph = nx.DiGraph()
        self._build_weighted_graph()
        self.mastery: Dict[str, ConceptMastery] = {}
        self._recommendation_cache: Optional[List[LearningRecommendation]] = None
        self._cache_time: float = 0.0

    def _build_weighted_graph(self) -> None:
        """Build NetworkX graph with weighted prerequisite edges."""
        for c in self.taxonomy.get_all_concepts():
            self.graph.add_node(
                c.id,
                name=c.name,
                category=c.category.value,
                difficulty=c.difficulty,
                is_hub=c.is_hub,
            )
        for c in self.taxonomy.get_all_concepts():
            for prereq_id in c.prerequisites:
                weight = PREREQUISITE_WEIGHTS.get(c.id, {}).get(prereq_id, 0.5)
                self.graph.add_edge(c.id, prereq_id, weight=weight, type="prerequisite")

    # ------------------------------------------------------------------
    # Mastery tracking with confidence and decay
    # ------------------------------------------------------------------

    def _get_mastery(self, concept_id: str) -> ConceptMastery:
        if concept_id not in self.mastery:
            concept = self.taxonomy.get_concept(concept_id)
            initial = 0.3 if (concept and concept.difficulty > 0.5) else 0.5
            self.mastery[concept_id] = ConceptMastery(value=initial)
        return self.mastery[concept_id]

    def record_success(self, concept_id: str) -> None:
        m = self._get_mastery(concept_id)
        self._apply_decay(m)

        m.attempts += 1
        m.streak += 1
        m.last_attempt_time = time.time()

        # Bayesian update: more evidence → higher confidence
        evidence_strength = min(0.15, 0.05 + 0.02 * m.streak)
        m.value = min(1.0, m.value + evidence_strength * (1 - m.value))

        # Confidence increases with more successful attempts
        m.confidence = min(0.95, m.confidence + 0.08 * (1 - m.confidence))

        # Invalidate recommendation cache
        self._recommendation_cache = None

    def record_mistake(self, concept_id: str, violation_type: Optional[str] = None) -> None:
        m = self._get_mastery(concept_id)
        self._apply_decay(m)

        m.attempts += 1
        m.streak = 0
        m.mistakes += 1
        m.misconception_count += 1
        m.last_attempt_time = time.time()

        # Decrease mastery proportional to current value
        penalty = 0.18 * m.value
        m.value = max(0.0, m.value - penalty)

        # Confidence drops when unexpected failures occur
        m.confidence = max(0.1, m.confidence - 0.1)

        # Propagate to downstream dependents
        self._propagate_misconception(concept_id)

        self._recommendation_cache = None

    def _apply_decay(self, m: ConceptMastery) -> None:
        """Apply temporal decay using Ebbinghaus forgetting curve."""
        if m.last_decay_time == 0:
            m.last_decay_time = time.time()
            return

        now = time.time()
        days_elapsed = (now - m.last_decay_time) / 86400.0
        if days_elapsed < 0.1:  # Less than 2.4 hours, skip
            return

        concept_id = None
        for cid, cm in self.mastery.items():
            if cm is m:
                concept_id = cid
                break

        concept = self.taxonomy.get_concept(concept_id) if concept_id else None
        category = concept.category.value if concept else ConceptCategory.CORE.value
        half_life = DECAY_HALF_LIFE_DAYS.get(category, 14.0)

        # Exponential decay: mastery *= 2^(-days/half_life)
        decay_factor = math.pow(2, -days_elapsed / half_life)
        m.value = max(0.0, m.value * decay_factor)
        m.last_decay_time = now

    def _propagate_misconception(self, concept_id: str) -> None:
        """
        Propagate the impact of a misconception to downstream concepts.
        
        If concept A is a prerequisite for B, and A just had a mistake,
        then B's effective mastery is reduced proportionally to the
        edge weight between A and B.
        """
        # Find all concepts that depend on this one
        dependents = [
            node for node in self.graph.nodes()
            if concept_id in [
                e[1] for e in self.graph.in_edges(node)
            ]
        ]
        for dep_id in dependents:
            edge_data = self.graph.get_edge_data(dep_id, concept_id)
            if not edge_data:
                continue
            weight = edge_data.get("weight", 0.5)
            dep_m = self._get_mastery(dep_id)
            if dep_m.value > 0:
                # Reduce mastery proportionally to edge weight
                propagation_penalty = 0.06 * weight
                dep_m.value = max(0.0, dep_m.value - propagation_penalty)

    # ------------------------------------------------------------------
    # Recommendation engine
    # ------------------------------------------------------------------

    def get_recommendations(self, max_results: int = 5) -> List[LearningRecommendation]:
        """Generate adaptive learning recommendations sorted by priority."""
        now = time.time()
        if self._recommendation_cache and (now - self._cache_time) < 60:
            return self._recommendation_cache[:max_results]

        recs: List[LearningRecommendation] = []

        for concept_id, m in list(self.mastery.items()):
            concept = self.taxonomy.get_concept(concept_id)
            if not concept:
                continue

            name = concept.name
            prereqs = concept.prerequisites

            # Check if prerequisites are weak
            weak_prereqs = [
                pid for pid in prereqs
                if self._get_mastery(pid).value < 0.4
            ]

            # Type 1: Review weak prerequisites
            for pid in weak_prereqs:
                prereq_concept = self.taxonomy.get_concept(pid)
                if not prereq_concept:
                    continue
                prereq_m = self._get_mastery(pid)
                edge_w = self.graph.get_edge_data(concept_id, pid, {}).get("weight", 0.5)
                priority = self._compute_recommendation_priority(prereq_m, edge_w, prereq_concept.is_hub)
                recs.append(LearningRecommendation(
                    concept_id=pid,
                    concept_name=prereq_concept.name,
                    recommendation_type="review_prerequisite",
                    priority=priority,
                    reason=f"Prerequisite for {name} is weak (mastery: {prereq_m.value:.0%})",
                    estimated_impact=edge_w * (1 - prereq_m.value),
                ))

            # Type 2: Practice weak concepts
            if m.value < 0.4 and m.confidence > 0.2:
                priority = self._compute_recommendation_priority(m, 1.0, concept.is_hub)
                recs.append(LearningRecommendation(
                    concept_id=concept_id,
                    concept_name=name,
                    recommendation_type="practice_concept",
                    priority=priority,
                    reason=f"Low mastery ({m.value:.0%}) with {m.misconception_count} recorded misconceptions",
                    estimated_impact=1.0 - m.value,
                ))

            # Type 3: Remediate persistent misconceptions
            if m.misconception_count >= 3 and m.value < 0.5:
                recs.append(LearningRecommendation(
                    concept_id=concept_id,
                    concept_name=name,
                    recommendation_type="remediate_misconception",
                    priority=5,
                    reason=f"Persistent misconception ({m.misconception_count} occurrences) blocking progress",
                    estimated_impact=0.8,
                ))

            # Type 4: Advance if strong
            if m.value >= 0.8 and m.confidence >= 0.6 and m.streak >= 3:
                dependents = [
                    n for n in self.graph.nodes()
                    if concept_id in [e[1] for e in self.graph.in_edges(n)]
                ]
                for dep_id in dependents:
                    dep_m = self._get_mastery(dep_id)
                    if dep_m.value < 0.4:
                        dep_concept = self.taxonomy.get_concept(dep_id)
                        if dep_concept:
                            recs.append(LearningRecommendation(
                                concept_id=dep_id,
                                concept_name=dep_concept.name,
                                recommendation_type="advance",
                                priority=4,
                                reason=f"Prerequisite {name} is strong — ready to learn {dep_concept.name}",
                                estimated_impact=0.7,
                            ))

        # Sort by priority (desc) then estimated impact (desc)
        recs.sort(key=lambda r: (r.priority, r.estimated_impact), reverse=True)
        self._recommendation_cache = recs
        self._cache_time = time.time()

        return recs[:max_results]

    @staticmethod
    def _compute_recommendation_priority(
        mastery: ConceptMastery,
        edge_weight: float,
        is_hub: bool,
    ) -> int:
        """Compute priority score 1-5 for a recommendation."""
        priority = 2
        if mastery.value < 0.2:
            priority += 2
        elif mastery.value < 0.4:
            priority += 1
        if is_hub:
            priority += 1
        if edge_weight > 0.8:
            priority += 1
        return min(5, priority)

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, ctx: AgentContext) -> AgentContext:
        ctx.concept_updates = []

        if ctx.has_violations:
            for v in ctx.violations:
                concepts = self._violation_to_concepts(v)
                for cid in concepts:
                    vtype = v.get("type", v.get("rule_id", "unknown"))
                    self.record_mistake(cid, vtype)
                    ctx.concept_updates.append({
                        "concept": cid,
                        "action": "mistake",
                        "mastery": self._get_mastery(cid).value,
                    })
        else:
            tree_concepts = self.taxonomy.get_concepts_for_tree(ctx.tree_type)
            for c in tree_concepts:
                if c.category.value in ("core", "operation"):
                    self.record_success(c.id)
                    ctx.concept_updates.append({
                        "concept": c.id,
                        "action": "success",
                        "mastery": self._get_mastery(c.id).value,
                    })

        ctx.metadata["recommendations"] = [
            {
                "concept": r.concept_name,
                "type": r.recommendation_type,
                "priority": r.priority,
                "reason": r.reason,
            }
            for r in self.get_recommendations(3)
        ]

        return ctx

    # ------------------------------------------------------------------
    # Violation mapping
    # ------------------------------------------------------------------

    def _violation_to_concepts(self, violation: Dict) -> List[str]:
        vtype = violation.get("type", violation.get("rule_id", "unknown"))
        tree_type = violation.get("tree_type", "")
        if not tree_type:
            tree_type = violation.get("rule_id", "").split(":")[0]
        sig = self.taxonomy.get_violation_signature(tree_type, vtype)
        if sig:
            return [sig.primary_concept] + sig.secondary_concepts
        return [f"{tree_type}:{vtype}"]

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_weak_concepts(self, threshold: float = 0.4) -> List[Dict[str, Any]]:
        weak = []
        for concept_id, m in list(self.mastery.items()):
            if m.value >= threshold:
                continue
            concept = self.taxonomy.get_concept(concept_id)
            node_data = self.graph.nodes.get(concept_id, {})
            prereq_blocked = self._prerequisites_weak(concept_id, threshold)

            weak.append({
                "concept": concept_id,
                "concept_name": node_data.get("name", concept_id),
                "mastery": round(m.value, 2),
                "confidence": round(m.confidence, 2),
                "attempts": m.attempts,
                "mistakes": m.mistakes,
                "streak": m.streak,
                "misconception_count": m.misconception_count,
                "is_hub": node_data.get("is_hub", False),
                "category": node_data.get("category", ""),
                "prerequisites_weak": prereq_blocked,
                "priority": self._compute_priority(m, node_data.get("is_hub", False), prereq_blocked),
            })

        return sorted(weak, key=lambda x: (x["priority"], x["mastery"]))

    def _prerequisites_weak(self, concept_id: str, threshold: float) -> bool:
        concept = self.taxonomy.get_concept(concept_id)
        if not concept:
            return False
        for prereq_id in concept.prerequisites:
            if self._get_mastery(prereq_id).value < threshold:
                return True
        return False

    def _compute_priority(self, m: ConceptMastery, is_hub: bool, prereq_blocked: bool) -> int:
        priority = 3
        if m.value < 0.2:
            priority += 1
        if is_hub:
            priority += 1
        if prereq_blocked:
            priority += 1
        if m.misconception_count >= 3:
            priority += 1
        return min(5, priority)

    def get_full_graph(self) -> Dict[str, Any]:
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            m = self._get_mastery(node_id)
            nodes.append({
                "id": node_id,
                "name": attrs.get("name", node_id),
                "type": attrs.get("category", "concept"),
                "mastery": round(m.value, 2),
                "confidence": round(m.confidence, 2),
                "attempts": m.attempts,
                "mistakes": m.mistakes,
                "streak": m.streak,
                "is_hub": attrs.get("is_hub", False),
                "difficulty": attrs.get("difficulty", 0.5),
            })
        return {
            "nodes": nodes,
            "edges": [
                {
                    "from": u,
                    "to": v,
                    "weight": d.get("weight", 0.5),
                    "type": d.get("type", "prerequisite"),
                }
                for u, v, d in self.graph.edges(data=True)
            ],
        }

    def get_progress_summary(self) -> Dict[str, Any]:
        all_concepts = self.taxonomy.get_all_concepts()
        total = len(all_concepts)
        if total == 0:
            return {
                "total_concepts": 0, "mastered": 0, "in_progress": 0,
                "not_started": 0, "average_mastery": 0.0,
                "average_confidence": 0.0, "hub_mastery": 0.0,
                "prerequisite_gaps": 0, "persistent_misconceptions": 0,
            }

        scores = [self._get_mastery(c.id).value for c in all_concepts]
        confidences = [self._get_mastery(c.id).confidence for c in all_concepts]

        mastered = sum(1 for s in scores if s >= 0.8)
        in_progress = sum(1 for s in scores if 0.2 <= s < 0.8)
        not_started = sum(1 for s in scores if s < 0.2)
        avg = sum(scores) / len(scores)

        hub_ids = {
            n for n, a in self.graph.nodes(data=True)
            if a.get("is_hub", False)
        }
        hub_scores = [self._get_mastery(hid).value for hid in hub_ids if hid in self.mastery]
        hub_mastery = sum(hub_scores) / len(hub_scores) if hub_scores else 0

        gap_count = sum(
            1 for c in all_concepts
            if self._prerequisites_weak(c.id, 0.4)
        )

        persistent = sum(
            1 for c in all_concepts
            if self._get_mastery(c.id).misconception_count >= 3
        )

        return {
            "total_concepts": total,
            "mastered": mastered,
            "in_progress": in_progress,
            "not_started": not_started,
            "average_mastery": round(avg, 2),
            "average_confidence": round(sum(confidences) / len(confidences), 2),
            "hub_mastery": round(hub_mastery, 2),
            "prerequisite_gaps": gap_count,
            "persistent_misconceptions": persistent,
        }

    def get_concept_data(self, concept_id: str) -> Optional[Dict[str, Any]]:
        concept = self.taxonomy.get_concept(concept_id)
        if not concept and concept_id not in self.graph:
            return None

        m = self._get_mastery(concept_id)
        node_data = self.graph.nodes.get(concept_id, {})

        prereqs = []
        for pid in (concept.prerequisites if concept else []):
            pm = self._get_mastery(pid)
            edge_w = self.graph.get_edge_data(concept_id, pid, {}).get("weight", 0.5)
            p_concept = self.taxonomy.get_concept(pid)
            prereqs.append({
                "id": pid,
                "name": p_concept.name if p_concept else pid,
                "weight": edge_w,
                "mastery": round(pm.value, 2),
                "weak": pm.value < 0.4,
            })

        return {
            "id": concept_id,
            "name": node_data.get("name", concept_id),
            "type": node_data.get("category", "concept"),
            "difficulty": node_data.get("difficulty", 0.5),
            "is_hub": node_data.get("is_hub", False),
            "mastery": round(m.value, 2),
            "confidence": round(m.confidence, 2),
            "attempts": m.attempts,
            "mistakes": m.mistakes,
            "streak": m.streak,
            "misconception_count": m.misconception_count,
            "prerequisites": sorted(prereqs, key=lambda p: -p["weight"]),
            "dependents": [
                node_id for node_id in self.graph.nodes()
                if concept_id in [e[1] for e in self.graph.in_edges(node_id)]
            ],
        }

    def get_mastery(self, concept_id: str) -> float:
        return self._get_mastery(concept_id).value
