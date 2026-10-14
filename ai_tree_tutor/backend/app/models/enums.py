from __future__ import annotations

from enum import Enum


class TreeType(str, Enum):
    AVL = "avl"
    RED_BLACK = "red_black"
    HEAP = "heap"
    SEGMENT_TREE = "segment_tree"
    BTREE = "btree"
    BPLUS_TREE = "bplus_tree"


class Operation(str, Enum):
    INSERT = "insert"
    DELETE = "delete"
    SEARCH = "search"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM_EASY = "medium_easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    MIXED = "mixed"


class QuestionType(str, Enum):
    CONCEPTUAL = "conceptual"
    REASONING = "reasoning"
    TRACE = "trace"
    VISUALIZATION = "visualization"
    MISCONCEPTION_TARGETED = "misconception_targeted"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class ScaffoldingLevel(str, Enum):
    MINIMAL = "minimal"
    SOCRATIC = "socratic"
    DIRECTIVE = "directive"
    EXPLANATORY = "explanatory"
