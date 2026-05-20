"""
OpenAI Engine — OpenAI LLM Implementation
===========================================
Implements LLMInterface for OpenAI API (GPT-4o / GPT-4o-mini).
Supports full response and streaming modes.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    from openai import AsyncOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.llm.base_llm import LLMInterface
from app.llm.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class OpenAIEngine(LLMInterface):
    """LLMInterface implementation for OpenAI with streaming support."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model
        self._client: OpenAI | None = None
        self._async_client: AsyncOpenAI | None = None
        self._templates = PromptTemplates()

        if OPENAI_AVAILABLE and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
            self._async_client = AsyncOpenAI(api_key=self.api_key)

    @property
    def available(self) -> bool:
        return self._client is not None and self._async_client is not None

    @property
    def provider_name(self) -> str:
        return "openai"

    def get_system_prompt(self) -> str:
        return self._templates.system()

    def get_quiz_system_prompt(self) -> str:
        return self._templates.quiz_system_prompt()

    # ------------------------------------------------------------------
    # Internal query (sync, used by Celery workers)
    # ------------------------------------------------------------------

    def _query(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        if not self.available:
            return self._fallback()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1024,
            )
            text = response.choices[0].message.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("OpenAI returned non-JSON: %s", text[:200])
            return {"error": "Failed to parse JSON response", "fallback": True}
        except Exception as e:
            logger.warning("OpenAI query failed: %s", e)
            return {"error": str(e), "fallback": True}

    # ------------------------------------------------------------------
    # Async query (used in request-response cycle)
    # ------------------------------------------------------------------

    async def _query_async(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        if not self.available:
            return self._fallback()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1024,
            )
            text = response.choices[0].message.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("OpenAI returned non-JSON")
            return {"error": "Failed to parse JSON", "fallback": True}
        except Exception as e:
            logger.warning("OpenAI async query failed: %s", e)
            return {"error": str(e), "fallback": True}

    # ------------------------------------------------------------------
    # Streaming (for SSE)
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
            stream = await self._async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self._templates.system()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
                if content:
                    yield content
        except Exception as e:
            logger.warning("OpenAI streaming failed: %s", e)
            yield f"\n[Error: {e}]"

    # ------------------------------------------------------------------
    # LLMInterface methods
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
        return self._query(prompt, system=self.get_system_prompt())

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
        return self._query(prompt, system=self.get_system_prompt())

    def explain_complexity(
        self,
        tree_type: str,
        operation: str,
        student_mastery: float = 0.5,
    ) -> Dict[str, Any]:
        prompt = self._templates.complexity(tree_type, operation, student_mastery)
        return self._query(prompt)

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
        return self._query(prompt, system=self.get_quiz_system_prompt())

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

    def evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        correct_answer: str = "",
        is_correct: bool = False,
        student_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        prompt = self._templates.answer_evaluation(
            question, student_answer, correct_answer, is_correct, student_history,
        )
        return self._query(prompt)

    @staticmethod
    def _fallback() -> Dict[str, Any]:
        return {
            "diagnosis": "AI service unavailable. Check your API key.",
            "explanation": "The symbolic validator detected a violation. Review the tree invariants.",
            "guiding_question": "What property must be maintained after each operation?",
            "fallback": True,
        }
