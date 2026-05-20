from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import Difficulty, QuestionType, ScaffoldingLevel


# ============================================================ Request Schemas

class TreeOperationRequest(BaseModel):
    tree_type: str = Field(..., description="avl | red_black | heap | segment_tree | btree | bplus_tree")
    operation: str = Field(..., description="insert | delete | search")
    key: int = Field(..., description="The key/value to operate on")
    session_id: str = Field(default="default")
    options: Dict[str, Any] = Field(default_factory=dict)


class TreeResetRequest(BaseModel):
    tree_type: str
    session_id: str = "default"
    options: Dict[str, Any] = Field(default_factory=dict)


class ConceptQueryRequest(BaseModel):
    concept: str


class RangeQueryRequest(BaseModel):
    left: int
    right: int
    session_id: str = "default"


class QuizGenerateRequest(BaseModel):
    tree_type: Optional[str] = Field(default=None)
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="mixed")
    focus_weak: bool = Field(default=True)
    question_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by question types: conceptual, reasoning, trace, visualization, misconception_targeted",
    )
    misconception_targeted: Optional[str] = Field(
        default=None,
        description="Specific misconception to target with questions",
    )
    target_mastery: float = Field(
        default=0.7,
        ge=0.0, le=1.0,
        description="Target mastery level: questions are chosen to help student reach this mastery",
    )
    max_question_difficulty: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Cap question difficulty for struggling students",
    )


class QuizSubmitRequest(BaseModel):
    questions: List[Dict[str, Any]]
    answers: List[int]
    session_id: str = Field(default="default")
    attempt_number: int = Field(default=1, ge=1)


# ============================================================ Teaching Schemas

class HintRequest(BaseModel):
    tree_type: str
    operation: str
    violation: Dict[str, Any]
    attempt_number: int = Field(default=1, ge=1)
    previous_hints: Optional[List[str]] = None
    student_ability: str = Field(default="medium")


class TeachingRequest(BaseModel):
    tree_type: str
    operation: str
    violation: Dict[str, Any]
    misconception: str
    false_belief: Optional[str] = None
    prerequisite_gaps: Optional[List[str]] = None
    session_id: str = Field(default="default")


# ============================================================ Response Schemas

class ViolationDetail(BaseModel):
    type: str
    message: str
    node: Optional[Any] = None


class DiagnosisDetail(BaseModel):
    violation: Dict[str, Any] = {}
    source: str = "symbolic"
    misconception: Optional[str] = None
    root_cause: Optional[str] = None
    concept_area: Optional[str] = None
    severity: Optional[str] = None
    related_concepts: List[str] = []


class TeachingDetail(BaseModel):
    source: str = "symbolic"
    explanation: Optional[str] = None
    step_by_step: List[str] = []
    example: Optional[str] = None
    guiding_question: Optional[str] = None
    key_rule: Optional[str] = None
    common_mistake: Optional[str] = None
    scaffolding_level: Optional[str] = None


class TreeOperationResponse(BaseModel):
    operation: str
    key: int
    tree: Optional[Dict[str, Any]] = None
    log: List[Dict[str, Any]] = []
    validation: Dict[str, Any] = {}
    diagnosis: Optional[Dict[str, Any]] = None
    teaching: Optional[List[Dict[str, Any]]] = None
    complexity: Optional[Dict[str, Any]] = None
    concept_update: Optional[Dict[str, Any]] = None
    async_task_ids: Optional[Dict[str, str]] = None


class ProgressResponse(BaseModel):
    total_concepts: int
    mastered: int
    in_progress: int
    not_started: int
    average_mastery: float


class ConceptResponse(BaseModel):
    concept: str
    mastery: float
    mistakes: int
    attempts: int
    children: List[str] = []
    parents: List[str] = []


class QuizRecommendationResponse(BaseModel):
    concept: str
    mastery: float
    suggested_operations: List[str] = []
    priority: str = "medium"
    suggested_question_types: List[str] = []
