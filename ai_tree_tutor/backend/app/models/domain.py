"""
Domain Entities — Core domain objects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Violation:
    rule_id: str
    type: str
    message: str
    severity: str = "medium"
    affected_nodes: List[int] = field(default_factory=list)
    concept_tag: str = ""
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class Misconception:
    misconception: str
    root_cause: str
    concept_area: str
    severity: str = "medium"
    related_concepts: List[str] = field(default_factory=list)
    violation: Optional[Dict[str, Any]] = None


@dataclass
class TeachingMaterial:
    explanation: str = ""
    step_by_step: List[str] = field(default_factory=list)
    detailed_example: str = ""
    why_this_matters: str = ""
    guiding_question: str = ""
    key_rule: str = ""
    common_mistake: str = ""
    visual_trace: str = ""
    source: str = "symbolic"


@dataclass
class ConceptNode:
    name: str
    mastery: float = 0.0
    attempts: int = 0
    mistakes: int = 0
    children: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
