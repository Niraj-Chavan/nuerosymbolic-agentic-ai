from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.context.agent_context import AgentContext
from app.llm.base_llm import LLMInterface
from app.models.enums import ScaffoldingLevel

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


class TeachingAgent(BaseAgent):
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self._fallback_bank: Dict[str, Any] = self._load_fallback_bank()
        self._session_flow: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _load_fallback_bank() -> Dict[str, Any]:
        path = os.path.join(DATA_DIR, "fallback_explanations.json")
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    async def process(self, ctx: AgentContext) -> AgentContext:
        teaching = []
        for i, diagnosis in enumerate(ctx.diagnoses):
            violation = diagnosis.get("violation", {})
            misconception = diagnosis.get("misconception", "")
            false_belief = diagnosis.get("false_belief", "")
            prerequisite_gaps = diagnosis.get("prerequisite_gaps", [])
            attempt_number = ctx.metadata.get("attempt_number", 1)
            student_ability = ctx.metadata.get("student_ability", "medium")

            previous = ctx.metadata.get("teaching_history", [])
            previous_explanations = [t.get("explanation", "") for t in previous if t.get("explanation")]

            material = self._teach_one(
                ctx.tree_type, ctx.operation, violation, misconception,
                false_belief=false_belief,
                prerequisite_gaps=prerequisite_gaps,
                attempt_number=attempt_number,
                student_ability=student_ability,
                previous_explanations=previous_explanations,
            )
            teaching.append(material)

        flow_state = self._get_flow_state(ctx.session_id)
        flow_state["teaching_count"] = flow_state.get("teaching_count", 0) + len(teaching)
        flow_state["topics_covered"] = list(set(
            flow_state.get("topics_covered", []) +
            [d.get("concept_id", "") for d in ctx.diagnoses]
        ))

        ctx.teaching_materials = teaching
        ctx.metadata["teaching_count"] = flow_state["teaching_count"]
        ctx.metadata["scaffolding_level"] = self._select_scaffolding_level(flow_state)

        return ctx

    # ------------------------------------------------------------------
    # Socratic teaching with guided questioning
    # ------------------------------------------------------------------

    def _teach_one(
        self,
        tree_type: str,
        operation: str,
        violation: Dict,
        misconception: str,
        false_belief: str = "",
        prerequisite_gaps: Optional[List[str]] = None,
        attempt_number: int = 1,
        student_ability: str = "medium",
        previous_explanations: Optional[List[str]] = None,
    ) -> Dict:
        rule_id = violation.get("rule_id", "") or violation.get("type", "")
        lookup_key = f"{tree_type}:{rule_id}"
        prereq_gaps = prerequisite_gaps or []

        scaffolding = self._scaffolding_for_attempt(attempt_number, student_ability)

        if self.llm.available:
            try:
                ai = self.llm.generate_explanation(
                    tree_type, operation, violation, misconception,
                    false_belief=false_belief or None,
                    prerequisite_gaps=prereq_gaps if prereq_gaps else None,
                    student_history=previous_explanations,
                )
                if ai and "explanation" in ai:
                    ai["source"] = "neural"
                    ai["scaffolding_level"] = scaffolding.value
                    ai["guiding_question"] = self._socratic_question(
                        tree_type, misconception, scaffolding,
                    )
                    return ai
            except Exception:
                pass

        fallback = self._fallback_bank.get(lookup_key, {})
        if not fallback:
            fallback = self._generic_fallback(tree_type, misconception, scaffolding)

        fallback["source"] = "symbolic"
        fallback["scaffolding_level"] = scaffolding.value
        fallback["guiding_question"] = self._socratic_question(
            tree_type, misconception, scaffolding,
        )
        return fallback

    # ------------------------------------------------------------------
    # Socratic question generator
    # ------------------------------------------------------------------

    def _socratic_question(
        self,
        tree_type: str,
        misconception: str,
        scaffolding: ScaffoldingLevel,
    ) -> str:
        questions = {
            ScaffoldingLevel.MINIMAL: (
                f"What property of {tree_type} does your approach violate?"
            ),
            ScaffoldingLevel.SOCRATIC: (
                f"If your understanding were correct, what would happen to the "
                f"{tree_type}'s invariants after this operation? Why is that a problem?"
            ),
            ScaffoldingLevel.DIRECTIVE: (
                f"Consider the specific invariant related to '{misconception}'. "
                f"How does your current approach fail to maintain it?"
            ),
            ScaffoldingLevel.EXPLANATORY: (
                f"Trace through the operation step by step. At which step does "
                f"the {tree_type} property break, and what should you do differently?"
            ),
        }
        return questions.get(scaffolding, questions[ScaffoldingLevel.SOCRATIC])

    # ------------------------------------------------------------------
    # Scaffolding level selection
    # ------------------------------------------------------------------

    @staticmethod
    def _scaffolding_for_attempt(
        attempt_number: int,
        student_ability: str,
    ) -> ScaffoldingLevel:
        if student_ability == "strong":
            if attempt_number <= 2:
                return ScaffoldingLevel.MINIMAL
            if attempt_number <= 4:
                return ScaffoldingLevel.SOCRATIC
            return ScaffoldingLevel.DIRECTIVE
        if student_ability == "struggling":
            if attempt_number <= 1:
                return ScaffoldingLevel.SOCRATIC
            if attempt_number <= 3:
                return ScaffoldingLevel.DIRECTIVE
            return ScaffoldingLevel.EXPLANATORY
        return ScaffoldingLevel.SOCRATIC

    @staticmethod
    def _select_scaffolding_level(flow_state: Dict[str, Any]) -> str:
        count = flow_state.get("teaching_count", 0)
        if count <= 2:
            return "socratic"
        if count <= 5:
            return "directive"
        return "explanatory"

    # ------------------------------------------------------------------
    # Adaptive follow-up generation
    # ------------------------------------------------------------------

    def generate_follow_up(
        self,
        tree_type: str,
        operation: str,
        misconception: str,
        student_response: str,
        previous_materials: List[Dict],
    ) -> Dict[str, Any]:
        if self.llm.available:
            try:
                prompt = (
                    f"The student responded to a teaching explanation about {misconception} "
                    f"on {tree_type} '{operation}' with: '{student_response}'. "
                    f"Previous explanations: {previous_materials[-1].get('explanation', '')[:200] if previous_materials else 'none'}.\n\n"
                    f"Generate a Socratic follow-up that probes deeper into their understanding. "
                    f"Do NOT give the answer — ask a question that makes them reason further."
                )
                result = self.llm._query(prompt)
                if result and "explanation" in result:
                    return result
            except Exception:
                pass

        return {
            "explanation": "Let's think about this differently.",
            "guiding_question": f"Can you trace through the {operation} operation step by step and identify where the {misconception} might occur?",
            "source": "symbolic",
        }

    # ------------------------------------------------------------------
    # Flow state management
    # ------------------------------------------------------------------

    def _get_flow_state(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._session_flow:
            self._session_flow[session_id] = {
                "teaching_count": 0,
                "topics_covered": [],
                "current_scaffolding": "socratic",
            }
        return self._session_flow[session_id]

    # ------------------------------------------------------------------
    # Fallback generators
    # ------------------------------------------------------------------

    def _generic_fallback(
        self,
        tree_type: str,
        misconception: str,
        scaffolding: ScaffoldingLevel,
    ) -> Dict:
        return {
            "explanation": (
                f"In {tree_type}, certain invariants must be maintained. "
                f"The error related to '{misconception}' suggests a misunderstanding "
                f"of how the tree preserves its properties after operations."
            ),
            "step_by_step": [
                f"Step 1: Identify the violated property — WHY: Understanding which property was violated guides the fix",
                f"Step 2: Review the mathematical rule — WHY: Tree invariants are precise mathematical conditions",
                f"Step 3: Trace the operation step by step — WHY: Finding where the invariant broke helps correct understanding",
                f"Step 4: Apply the correction — WHY: Practice reinforces correct mental models",
            ],
            "detailed_example": f"Review the operation trace above and identify where the {tree_type} property was violated.",
            "why_this_matters": f"Without maintaining {tree_type} invariants, the guaranteed O(log n) time complexity cannot be achieved.",
            "guiding_question": self._socratic_question(tree_type, misconception, scaffolding),
            "key_rule": f"The {tree_type} invariant: refer to your textbook for the precise {tree_type} properties.",
            "common_mistake": "Students often focus on the mechanics of the operation without verifying the invariants afterward.",
            "visual_trace": "Use the tree visualizer above to see the current tree state.",
        }
