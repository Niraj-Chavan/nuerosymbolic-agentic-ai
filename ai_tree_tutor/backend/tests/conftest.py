"""
Global Test Fixtures
=====================
Shared fixtures for all test modules:
  - async_test_db: in-memory SQLite test database with all tables
  - test_client: FastAPI TestClient with mocked dependencies
  - mock_llm: LLMInterface implementation returning canned responses
  - sample_avl_tree: populated AVL tree instance
  - agent_context: pre-configured AgentContext for agent tests
"""

from __future__ import annotations

import os
import sys
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Ensure the backend directory is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.connection import Base, async_session_factory, engine
from app.main import app as _app


# =========================================================================
# Mock LLM — returns canned responses, never touches an API
# =========================================================================

class MockLLM:
    """LLMInterface stand-in that returns predetermined responses."""

    def __init__(self):
        self.call_log: List[Dict[str, Any]] = []
        self._responses: Dict[str, Any] = {
            "diagnose_misconception": {
                "misconception": "The student likely forgot to update heights after insertion.",
                "root_cause": "Height not updated before balance check",
                "concept_area": "AVL height tracking",
            },
            "generate_explanation": {
                "explanation": "After inserting a node, update heights bottom-up before checking balance.",
                "step_by_step": [
                    "1. Insert the node using BST rules.",
                    "2. Walk back up and update each node's height.",
                    "3. Check the balance factor at each node.",
                    "4. Rotate if balance factor exceeds ±1.",
                ],
                "key_rule": "AVL trees require |balance_factor| <= 1 at every node.",
                "common_mistake": "Forgetting to update heights before computing balance.",
            },
            "explain_complexity": {
                "time_complexity": "O(log n)",
                "space_complexity": "O(log n)",
                "reasoning": "AVL operations traverse a single root-to-leaf path.",
            },
            "generate_quiz_question": {
                "question": "What is the balance factor of an AVL node?",
                "options": ["height(left) - height(right)", "height(right) - height(left)", "left - right", "right - left"],
                "correct": 0,
                "explanation": "Balance factor = height(left) - height(right).",
            },
            "generate_adaptive_hint": {
                "hint": "Check the height of the left and right children.",
                "type": "procedural",
            },
            "evaluate_answer": {
                "is_correct": False,
                "misconception_detected": "confuses height with key value",
                "feedback": "Height is the number of edges from node to deepest leaf.",
            },
        }

    @property
    def available(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "mock"

    def diagnose_misconception(self, tree_type: str, operation: str,
                                violation: Dict[str, Any],
                                misconception_context: Optional[Dict] = None) -> Dict[str, Any]:
        self.call_log.append(("diagnose_misconception", tree_type, operation, violation))
        return dict(self._responses["diagnose_misconception"])

    def generate_explanation(self, tree_type: str, operation: str,
                              violation: Dict[str, Any], misconception: str,
                              false_belief: Optional[str] = None,
                              prerequisite_gaps: Optional[List[str]] = None,
                              student_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        self.call_log.append(("generate_explanation", tree_type, operation, violation, misconception))
        return dict(self._responses["generate_explanation"])

    def explain_complexity(self, tree_type: str, operation: str,
                            student_mastery: float = 0.5) -> Dict[str, Any]:
        self.call_log.append(("explain_complexity", tree_type, operation))
        return dict(self._responses["explain_complexity"])

    def generate_quiz_question(self, tree_type: str, concept: str,
                                difficulty: float, student_mastery: float = 0.5,
                                question_type: str = "reasoning",
                                misconception: Optional[str] = None) -> Dict[str, Any]:
        self.call_log.append(("generate_quiz_question", tree_type, concept))
        return dict(self._responses["generate_quiz_question"])

    def generate_adaptive_hint(self, tree_type: str, operation: str,
                                violation: Dict[str, Any], attempt_number: int,
                                previous_hints: Optional[List[str]] = None,
                                student_ability: str = "medium") -> Dict[str, Any]:
        self.call_log.append(("generate_adaptive_hint", tree_type, operation))
        return dict(self._responses["generate_adaptive_hint"])

    def evaluate_answer(self, question: Dict[str, Any], student_answer: str,
                         correct_answer: str, is_correct: bool,
                         student_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        self.call_log.append(("evaluate_answer", question.get("id", "")))
        return dict(self._responses["evaluate_answer"])

    def get_system_prompt(self) -> str:
        return "Mock system prompt for testing."

    def get_quiz_system_prompt(self) -> str:
        return "Mock quiz system prompt for testing."


@pytest.fixture
def mock_llm() -> MockLLM:
    """Return a MockLLM that never makes API calls."""
    return MockLLM()


# =========================================================================
# Test database — in-memory SQLite
# =========================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def _setup_test_env():
    """Ensure environment variables are set for tests."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("LLM_PROVIDER", "mock")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
    os.environ.setdefault("ASYNC_AI_GENERATION", "false")
    yield


@pytest.fixture
async def async_test_db() -> AsyncGenerator:
    """
    Create all tables in an in-memory SQLite database.
    Drops them after the test.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# =========================================================================
# FastAPI test client — overrides dependencies with mocks
# =========================================================================

@pytest.fixture
def test_app(mock_llm) -> FastAPI:
    """
    Return the FastAPI app with mocked dependencies.
    Overrides the LLM dependency so no real API key is needed.
    """
    from app.dependencies import init_services, shutdown_services

    # Re-initialize services so our env vars take effect
    shutdown_services()

    # Monkey-patch the LLM creation to return our mock
    import app.dependencies as deps
    original_create = deps._create_llm

    def _mock_create_llm():
        return mock_llm

    deps._create_llm = _mock_create_llm
    init_services()

    yield _app

    deps._create_llm = original_create
    shutdown_services()


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =========================================================================
# Sample AVL tree fixture
# =========================================================================

@pytest.fixture
def sample_avl_tree():
    """
    Return an AVLTree pre-populated with keys [10, 20, 30, 40, 50, 25].
    This tree requires rotations and provides a realistic test surface.
    """
    from app.trees.avl import AVLTree
    tree = AVLTree()
    for key in [10, 20, 30, 40, 50, 25]:
        tree.insert(key)
    return tree


# =========================================================================
# AgentContext fixture
# =========================================================================

@pytest.fixture
def agent_context():
    """Return a pre-configured AgentContext for agent pipeline tests."""
    from app.context.agent_context import AgentContext
    return AgentContext(
        session_id="test-session-001",
        tree_type="avl",
        operation="insert",
        key=15,
    )


@pytest.fixture
async def populated_context(agent_context, sample_avl_tree):
    """Return an AgentContext with a tree already inserted and exported."""
    agent_context.tree_instance = sample_avl_tree
    agent_context.tree_export = sample_avl_tree.export_nested()
    return agent_context
