from __future__ import annotations

import json
import math
import os
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.context.agent_context import AgentContext
from app.llm.base_llm import LLMInterface
from app.models.enums import QuestionType

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class QuizAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, concept_graph: ConceptGraphAgent):
        self.llm = llm
        self.concept_graph = concept_graph
        self._question_bank: List[Dict[str, Any]] = self._load_question_bank()
        self._history: List[Dict[str, Any]] = []
        self._session_profiles: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _load_question_bank() -> List[Dict[str, Any]]:
        path = os.path.join(DATA_DIR, "question_bank.json")
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def process(self, ctx: AgentContext) -> AgentContext:
        return ctx

    # ------------------------------------------------------------------
    # Adaptive quiz generation
    # ------------------------------------------------------------------

    def generate_quiz(
        self,
        tree_type: Optional[str] = None,
        num_questions: int = 5,
        difficulty: str = "mixed",
        focus_weak: bool = True,
        question_types: Optional[List[str]] = None,
        misconception_targeted: Optional[str] = None,
        target_mastery: float = 0.7,
        max_question_difficulty: Optional[float] = None,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        pool = list(self._question_bank)

        if tree_type:
            pool = [q for q in pool if q.get("tree_type") == tree_type]

        if question_types:
            pool = [q for q in pool if q.get("question_type", "conceptual") in question_types]

        if max_question_difficulty is not None:
            pool = [q for q in pool if q.get("difficulty", 0.5) <= max_question_difficulty]

        if misconception_targeted:
            targeted = [q for q in pool if q.get("misconception_targeted", "") == misconception_targeted]
            if targeted:
                pool = targeted

        used_ids = {q.get("id") for quiz in self._history
                     for q in quiz.get("questions", [])
                     if quiz.get("session_id") == session_id}
        if len(pool) - len(used_ids) >= num_questions:
            pool = [q for q in pool if q.get("id") not in used_ids]

        if not pool and self.llm.available:
            generated = self.llm.generate_quiz_question(
                tree_type=tree_type or "avl",
                concept="Balanced Trees",
                difficulty=0.5,
            )
            if generated and generated.get("question"):
                pool = [generated]

        selected = []
        weak_concepts = set()

        if focus_weak:
            weak = self.concept_graph.get_weak_concepts(threshold=0.5)
            weak_concepts = {w["concept"].lower() for w in weak}
            weak_qs = [q for q in pool if q.get("concept", "").lower() in weak_concepts]
            random.shuffle(weak_qs)
            selected.extend(weak_qs[:num_questions // 2])

        remaining = num_questions - len(selected)

        if difficulty and difficulty != "mixed":
            target_diff = self._difficulty_value(difficulty)
            scored = [(q, abs(q.get("difficulty", 0.5) - target_diff)) for q in pool if q not in selected]
            scored.sort(key=lambda x: x[1])
            selected.extend([q for q, _ in scored[:remaining]])
        else:
            remaining_pool = [q for q in pool if q not in selected]
            if focus_weak and weak_concepts:
                concept_counts = defaultdict(int)
                for q in remaining_pool:
                    concept_counts[q.get("concept", "").lower()] += 1
                remaining_pool.sort(
                    key=lambda q: (
                        -(q.get("concept", "").lower() in weak_concepts),
                        -concept_counts.get(q.get("concept", "").lower(), 0),
                    )
                )
            random.shuffle(remaining_pool)
            selected.extend(remaining_pool[:remaining])

        for q in selected:
            self._shuffle_options(q)

        quiz = {
            "questions": selected,
            "total": len(selected),
            "focus_weak": focus_weak,
            "difficulty_target": difficulty,
            "question_type_distribution": self._type_distribution(selected),
            "average_difficulty": round(
                sum(q.get("difficulty", 0.5) for q in selected) / len(selected), 2
            ) if selected else 0,
            "session_id": session_id,
        }
        self._history.append({"questions": selected, "answers": None, "session_id": session_id})
        return quiz

    # ------------------------------------------------------------------
    # Difficulty scaling algorithm
    # ------------------------------------------------------------------

    def scale_difficulty(
        self,
        session_id: str,
        performance_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        profile = self._get_session_profile(session_id)
        recent = performance_history[-5:] if len(performance_history) >= 5 else performance_history
        if not recent:
            return {"recommended_difficulty": "mixed", "target_mastery": 0.7}

        avg_score = sum(r.get("percentage", 50) for r in recent) / len(recent)

        if avg_score >= 90:
            rec_diff = "hard"
            target = 0.85
        elif avg_score >= 80:
            rec_diff = "medium"
            target = 0.8
        elif avg_score >= 65:
            rec_diff = "medium"
            target = 0.7
        elif avg_score >= 50:
            rec_diff = "medium_easy"
            target = 0.65
        else:
            rec_diff = "easy"
            target = 0.6

        profile["last_difficulty"] = rec_diff
        profile["last_target"] = target

        return {
            "recommended_difficulty": rec_diff,
            "target_mastery": target,
            "average_performance": round(avg_score, 1),
            "performance_trend": self._performance_trend(performance_history),
        }

    # ------------------------------------------------------------------
    # Conceptual assessment model
    # ------------------------------------------------------------------

    def assess_conceptual_depth(
        self,
        session_id: str,
        tree_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        profile = self._get_session_profile(session_id)
        history = [h for h in self._history if h.get("session_id") == session_id]

        if tree_type:
            relevant = []
            for h in history:
                for q in h.get("questions", []):
                    if q.get("tree_type") == tree_type:
                        relevant.append(h)
                        break
            history = relevant

        type_counts = defaultdict(int)
        type_correct = defaultdict(int)
        total_questions = 0
        total_correct = 0

        for h in history:
            if not h.get("answers"):
                continue
            for q, ans in zip(h.get("questions", []), h["answers"]):
                total_questions += 1
                qtype = q.get("question_type", "conceptual")
                type_counts[qtype] += 1
                correct = q.get("shuffled_correct", q.get("correct_index", -1))
                if ans == correct:
                    total_correct += 1
                    type_correct[qtype] += 1

        if total_questions == 0:
            return {
                "total_questions": 0,
                "overall_mastery": 0,
                "conceptual_mastery": 0,
                "reasoning_mastery": 0,
                "visualization_mastery": 0,
                "type_breakdown": {},
                "weakness_areas": [],
            }

        type_breakdown = {}
        for qt in QuestionType:
            t = qt.value
            total = type_counts.get(t, 0)
            correct = type_correct.get(t, 0)
            type_breakdown[t] = {
                "attempted": total,
                "correct": correct,
                "mastery": round(correct / total, 2) if total > 0 else 0,
            }

        conceptual_m = type_breakdown.get("conceptual", {}).get("mastery", 0)
        reasoning_m = type_breakdown.get("reasoning", {}).get("mastery", 0)
        visualization_m = type_breakdown.get("visualization", {}).get("mastery", 0)
        trace_m = type_breakdown.get("trace", {}).get("mastery", 0)
        misconception_m = type_breakdown.get("misconception_targeted", {}).get("mastery", 0)

        weakness_areas = [
            qt for qt, data in type_breakdown.items()
            if data.get("attempted", 0) >= 2 and data.get("mastery", 1) < 0.6
        ]

        return {
            "total_questions": total_questions,
            "overall_mastery": round(total_correct / total_questions, 2),
            "conceptual_mastery": conceptual_m,
            "reasoning_mastery": reasoning_m,
            "visualization_mastery": visualization_m,
            "trace_mastery": trace_m,
            "misconception_repair_mastery": misconception_m,
            "type_breakdown": type_breakdown,
            "weakness_areas": weakness_areas,
        }

    # ------------------------------------------------------------------
    # Quiz evaluation with conceptual feedback
    # ------------------------------------------------------------------

    def evaluate_quiz(
        self,
        questions: List[Dict],
        answers: List[int],
        session_id: str = "default",
        attempt_number: int = 1,
    ) -> Dict[str, Any]:
        score = 0
        results = []
        concept_performance: Dict[str, List[bool]] = defaultdict(list)

        for i, (q, ans) in enumerate(zip(questions, answers)):
            correct_idx = q.get("shuffled_correct", q.get("correct_index", -1))
            is_correct = ans == correct_idx
            if is_correct:
                score += 1

            concept = q.get("concept", "Advanced Trees")
            question_type = q.get("question_type", "conceptual")
            difficulty = q.get("difficulty", 0.5)

            # Map question bank concept string to actual ConceptTaxonomy ID
            concept_mapping = {
                "AVL Rotations": "avl_rotation_mechanics",
                "B+ Tree Delete Algorithm": "bplus_delete",
                "B+ Tree Insert Algorithm": "bplus_insert",
                "B+ Tree Leaf vs Internal Structure": "bplus_structure",
                "B-Tree Insertion": "btree_insert",
                "Balance Factor": "avl_balance_factor",
                "Heap Property": "heap_property",
                "Heapify": "heapify",
                "Internal Node Split (Median Promoted)": "bplus_internal_split",
                "Leaf Linked List Maintenance": "bplus_leaf_linkage",
                "Leaf Split (Median Copied)": "bplus_leaf_split",
                "Red-Black Tree Insertion": "rb_insert_fixup",
                "Red-Black Tree Properties": "rb_properties",
                "Segment Tree Structure": "seg_range",
            }
            taxonomy_id = concept_mapping.get(concept, concept)

            if is_correct:
                self.concept_graph.record_success(taxonomy_id)
            else:
                self.concept_graph.record_mistake(taxonomy_id)

            concept_performance[concept].append(is_correct)

            results.append({
                "question_index": i,
                "question": q.get("question", ""),
                "question_type": question_type,
                "difficulty": difficulty,
                "your_answer": q.get("shuffled_options", [])[ans] if ans < len(q.get("shuffled_options", [])) else "N/A",
                "correct_answer": q.get("shuffled_options", [])[correct_idx] if correct_idx < len(q.get("shuffled_options", [])) else "N/A",
                "correct": is_correct,
                "explanation": q.get("explanation", ""),
                "reasoning_steps": q.get("reasoning_steps", []),
            })

        total = len(questions)
        pct = round(score / total * 100, 1) if total else 0
        grade = self._compute_grade(pct)

        weak = self.concept_graph.get_weak_concepts(threshold=0.5)
        recommendations = []
        for w in weak[:3]:
            recommendations.append({
                "concept": w["concept"],
                "mastery": w["mastery"],
                "suggestion": f"Review {w['concept']} — current mastery: {w['mastery']:.0%}",
            })

        conceptual_depth = self.assess_conceptual_depth(session_id)

        return {
            "score": score,
            "total": total,
            "percentage": pct,
            "grade": grade,
            "results": results,
            "weak_points": [r["concept"] for r in recommendations],
            "recommendations": recommendations,
            "progress": self.concept_graph.get_progress_summary(),
            "conceptual_depth": conceptual_depth,
            "attempt_number": attempt_number,
        }

    # ------------------------------------------------------------------
    # Session-aware next quiz suggestion
    # ------------------------------------------------------------------

    def suggest_next_quiz(
        self,
        session_id: str,
        tree_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        history = [h for h in self._history if h.get("session_id") == session_id]
        evaluations = [h for h in history if h.get("answers") is not None]

        performance_history = []
        for h in evaluations:
            qs = h.get("questions", [])
            ans = h.get("answers", [])
            if qs and ans:
                correct = sum(1 for q, a in zip(qs, ans) if a == q.get("shuffled_correct", q.get("correct_index", -1)))
                performance_history.append({
                    "percentage": round(correct / len(qs) * 100, 1),
                    "total": len(qs),
                    "correct": correct,
                })

        difficulty_scale = self.scale_difficulty(session_id, performance_history)
        conceptual_depth = self.assess_conceptual_depth(session_id, tree_type)

        weak = self.concept_graph.get_weak_concepts(threshold=0.5)
        weak_concepts = [w["concept"] for w in weak[:3]]

        suggested_types = self._suggest_question_types(conceptual_depth)

        return {
            "recommended_difficulty": difficulty_scale["recommended_difficulty"],
            "target_mastery": difficulty_scale["target_mastery"],
            "focus_concepts": weak_concepts,
            "suggested_question_types": suggested_types,
            "conceptual_weaknesses": conceptual_depth.get("weakness_areas", []),
            "num_questions": self._suggest_question_count(performance_history),
        }

    # ------------------------------------------------------------------
    # Hint generation (delegates to LLM)
    # ------------------------------------------------------------------

    def generate_hint(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        attempt_number: int = 1,
        previous_hints: Optional[List[str]] = None,
        student_ability: str = "medium",
    ) -> Dict[str, Any]:
        if self.llm.available:
            try:
                return self.llm.generate_adaptive_hint(
                    tree_type, operation, violation,
                    attempt_number, previous_hints, student_ability,
                )
            except Exception:
                pass

        hints = {
            1: {"hint": f"Review {violation.get('type', 'this tree property')}.", "scaffolding_level": "minimal"},
            2: {"hint": "What invariant must hold after this operation?", "scaffolding_level": "socratic"},
            3: {"hint": f"Check the {violation.get('type', 'relevant')} property.", "scaffolding_level": "directive"},
        }
        return hints.get(attempt_number, {
            "hint": f"Review the {violation.get('type', 'tree property')} and trace the operation step by step.",
            "scaffolding_level": "explanatory",
        })

    # ------------------------------------------------------------------
    # History and reporting
    # ------------------------------------------------------------------

    def get_quiz_history(self, session_id: Optional[str] = None) -> List[Dict]:
        history = self._history
        if session_id:
            history = [h for h in history if h.get("session_id") == session_id]
        return [
            {
                "total": q.get("total", len(q.get("questions", []))),
                "questions": len(q.get("questions", [])),
                "session_id": q.get("session_id"),
                "has_answers": q.get("answers") is not None,
            }
            for q in history
        ]

    def get_learning_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        history = self._history
        if session_id:
            history = [h for h in history if h.get("session_id") == session_id]

        total_quizzes = len(history)
        total_questions = sum(len(h.get("questions", [])) for h in history)
        total_answered = sum(1 for h in history if h.get("answers") is not None)

        conceptual_depth = self.assess_conceptual_depth(session_id or "default")

        return {
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "total_answered": total_answered,
            "progress": self.concept_graph.get_progress_summary(),
            "conceptual_depth": conceptual_depth,
        }

    def _suggest_operations(self, concept: str) -> List[str]:
        mapping = {
            "Balance Factor": ["Insert nodes that create left-skewed trees", "Practice computing balance factors"],
            "AVL Rotations": ["Insert 3 into [10, 5, 15]", "Insert 1 into [10, 5]"],
            "RB Insert": ["Insert 10, 5, 15 into Red-Black tree", "Practice recolor vs rotate decisions"],
            "Heap Property": ["Insert into min-heap and check parent <= children", "Build heap from array"],
        }
        return mapping.get(concept, [f"Practice {concept} operations"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_session_profile(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._session_profiles:
            self._session_profiles[session_id] = {
                "last_difficulty": None,
                "last_target": 0.7,
                "history": [],
            }
        return self._session_profiles[session_id]

    @staticmethod
    def _shuffle_options(q: Dict[str, Any]) -> None:
        options = q.get("options", [])
        correct = options[q["correct_index"]]
        indices = list(range(len(options)))
        random.shuffle(indices)
        q["shuffled_options"] = [options[i] for i in indices]
        q["shuffled_correct"] = indices.index(q["correct_index"])

    @staticmethod
    def _difficulty_value(difficulty: str) -> float:
        mapping = {
            "easy": 0.2,
            "medium_easy": 0.35,
            "medium": 0.5,
            "hard": 0.7,
            "expert": 0.9,
        }
        return mapping.get(difficulty, 0.5)

    @staticmethod
    def _compute_grade(pct: float) -> str:
        if pct >= 90:
            return "A"
        if pct >= 80:
            return "B"
        if pct >= 70:
            return "C"
        if pct >= 60:
            return "D"
        return "F"

    @staticmethod
    def _type_distribution(questions: List[Dict]) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for q in questions:
            t = q.get("question_type", "conceptual")
            dist[t] = dist.get(t, 0) + 1
        return dist

    @staticmethod
    def _performance_trend(history: List[Dict[str, Any]]) -> str:
        if len(history) < 3:
            return "insufficient_data"
        recent = [h.get("percentage", 50) for h in history[-3:]]
        if recent[-1] > recent[0]:
            return "improving"
        if recent[-1] < recent[0]:
            return "declining"
        return "stable"

    @staticmethod
    def _suggest_question_types(conceptual_depth: Dict[str, Any]) -> List[str]:
        weak = conceptual_depth.get("weakness_areas", [])
        if not weak:
            return ["reasoning", "visualization", "conceptual"]
        return weak + [t for t in ["conceptual", "reasoning", "trace", "visualization"] if t not in weak][:2]

    @staticmethod
    def _suggest_question_count(performance_history: List[Dict]) -> int:
        if not performance_history:
            return 5
        avg = sum(h.get("total", 5) for h in performance_history) / len(performance_history)
        return max(3, min(10, round(avg)))
