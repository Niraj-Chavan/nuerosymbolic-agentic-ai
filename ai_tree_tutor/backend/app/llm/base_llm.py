"""
LLM Interface v2 — Abstract Base with Enhanced Methods
========================================================
Adds adaptive hint, reasoning question generation, and
misconception-targeted evaluation to the interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMInterface(ABC):
    """Abstract interface for large language model interactions."""

    @abstractmethod
    def diagnose_misconception(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Interpret a symbolic violation and produce a misconception diagnosis."""
        ...

    @abstractmethod
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
        """Generate a pedagogical explanation using WHY-before-WHAT format."""
        ...

    @abstractmethod
    def explain_complexity(
        self,
        tree_type: str,
        operation: str,
        student_mastery: float = 0.5,
    ) -> Dict[str, Any]:
        """Explain time/space complexity of an operation."""
        ...

    @abstractmethod
    def generate_quiz_question(
        self,
        tree_type: str,
        concept: str,
        difficulty: float,
        student_mastery: float = 0.5,
        question_type: str = "reasoning",
        misconception: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a quiz question targeting a specific concept."""
        ...

    @abstractmethod
    def generate_adaptive_hint(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        attempt_number: int,
        previous_hints: Optional[List[str]] = None,
        student_ability: str = "medium",
    ) -> Dict[str, Any]:
        """Generate a progressively revealing hint based on attempt count."""
        ...

    @abstractmethod
    def evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        correct_answer: str,
        is_correct: bool,
        student_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Evaluate a student answer and detect misconceptions."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for model initialisation."""
        ...

    @abstractmethod
    def get_quiz_system_prompt(self) -> str:
        """Return the system prompt for quiz generation mode."""
        ...

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether the LLM service is configured and reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return 'gemini', 'openai', 'mock', etc."""
        ...
