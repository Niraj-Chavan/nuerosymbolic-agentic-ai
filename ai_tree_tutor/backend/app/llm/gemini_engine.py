"""
Gemini Engine v2 — Google Gemini LLM Implementation
=====================================================
Implements the enhanced LLMInterface v2 with streaming support for SSE.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.llm.base_llm import LLMInterface
from app.llm.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class GeminiEngine(LLMInterface):
    """LLMInterface implementation for Google Gemini with streaming support."""

    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model
        self._model = None
        self._templates = PromptTemplates()

        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self._model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=self._templates.system(),
                )
            except TypeError:
                self._model = genai.GenerativeModel(self.model_name)

    @property
    def available(self) -> bool:
        return self._model is not None

    @property
    def provider_name(self) -> str:
        return "gemini"

    def get_system_prompt(self) -> str:
        return self._templates.system()

    def get_quiz_system_prompt(self) -> str:
        return self._templates.quiz_system_prompt()

    # ------------------------------------------------------------------
    # Streaming for SSE
    # ------------------------------------------------------------------

    async def stream_explanation(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception: str,
        false_belief: Optional[str] = None,
        prerequisite_gaps: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.available:
            yield "AI service unavailable. Check your API key."
            return

        prompt = self._templates.teaching(
            tree_type, operation, violation, misconception,
            false_belief, prerequisite_gaps, None,
        )

        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.warning("Gemini streaming failed: %s", e)
            yield f"\n[Error: {e}]"

    # ------------------------------------------------------------------
    # Diagnosis
    # ------------------------------------------------------------------

    def diagnose_misconception(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        prompt = self._templates.diagnosis(
            tree_type, operation, violation, misconception_context,
        )
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Teaching explanation
    # ------------------------------------------------------------------

    def generate_explanation(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception: str,
        false_belief: Optional[str] = None,
        prerequisite_gaps: Optional[List[str]] = None,
        student_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        prompt = self._templates.teaching(
            tree_type, operation, violation, misconception,
            false_belief, prerequisite_gaps, student_history,
        )
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Adaptive hint
    # ------------------------------------------------------------------

    def generate_adaptive_hint(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        attempt_number: int,
        previous_hints: Optional[List[str]] = None,
        student_ability: str = "medium",
    ) -> Dict[str, Any]:
        prompt = self._templates.adaptive_hint(
            tree_type, operation, violation,
            attempt_number, previous_hints, student_ability,
        )
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Quiz question generation
    # ------------------------------------------------------------------

    def generate_quiz_question(
        self,
        tree_type: str,
        concept: str,
        difficulty: float,
        student_mastery: float = 0.5,
        question_type: str = "reasoning",
        misconception: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt = self._templates.quiz_question(
            tree_type, concept, difficulty, student_mastery,
            question_type, misconception,
        )
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Answer evaluation
    # ------------------------------------------------------------------

    def evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        correct_answer: str,
        is_correct: bool,
        student_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        prompt = self._templates.answer_evaluation(
            question, student_answer, correct_answer, is_correct, student_history,
        )
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Complexity explanation
    # ------------------------------------------------------------------

    def explain_complexity(
        self,
        tree_type: str,
        operation: str,
        student_mastery: float = 0.5,
    ) -> Dict[str, Any]:
        prompt = self._templates.complexity(tree_type, operation, student_mastery)
        return self._query(prompt)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _query(self, prompt: str) -> Dict[str, Any]:
        if not self.available:
            return self._fallback()

        response = None
        try:
            response = self._model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            result = json.loads(text)
            return result
        except json.JSONDecodeError:
            logger.warning("Gemini returned non-JSON: %s", getattr(response, "text", "")[:200])
            # Fall back to returning the raw text as the response if it's not JSON
            return {
                "response": getattr(response, "text", "").strip(),
                "repaired": False,
                "widget": None,
                "fallback": True,
            }
        except Exception as e:
            logger.warning("Gemini query failed: %s", e)
            return {
                "response": f"I encountered an error: {str(e)}",
                "repaired": False,
                "widget": None,
                "fallback": True,
            }

    def _fallback(self) -> Dict[str, Any]:
        return {
            "diagnosis": "AI service unavailable. Check your API key.",
            "explanation": "The symbolic validator detected a violation. Review the tree invariants.",
            "guiding_question": "What property must be maintained after each operation?",
            "fallback": True,
        }
