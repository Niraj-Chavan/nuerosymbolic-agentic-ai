"""
Background AI Tasks
====================
Celery tasks for slow operations (AI generation).
These run in worker processes, not in the request-response cycle.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.llm.base_llm import LLMInterface
from app.llm.gemini_engine import GeminiEngine
from app.config import settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Cache LLM instance per worker process
_llm: LLMInterface | None = None


def _get_llm() -> LLMInterface:
    global _llm
    if _llm is None:
        _llm = GeminiEngine(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    return _llm


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def ai_diagnose_task(
    self,
    tree_type: str,
    operation: str,
    violations: list,
) -> Dict[str, Any]:
    """
    Run AI misconception diagnosis in background.
    Falls back gracefully on failure.
    """
    try:
        llm = _get_llm()
        results = []
        for violation in violations:
            diagnosis = llm.diagnose_misconception(tree_type, operation, violation)
            results.append(diagnosis)
        return {"diagnoses": results, "status": "completed"}
    except Exception as exc:
        logger.exception("AI diagnosis task failed")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def ai_teach_task(
    self,
    tree_type: str,
    operation: str,
    diagnoses: list,
) -> Dict[str, Any]:
    """
    Run AI teaching generation in background.
    """
    try:
        llm = _get_llm()
        results = []
        for d in diagnoses:
            teaching = llm.generate_explanation(
                tree_type,
                operation,
                d.get("violation", {}),
                d.get("misconception", ""),
            )
            results.append(teaching)
        return {"teaching": results, "status": "completed"}
    except Exception as exc:
        logger.exception("AI teaching task failed")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def ai_generate_quiz_task(
    self,
    tree_type: str,
    concept: str,
    difficulty: str,
    count: int = 1,
) -> Dict[str, Any]:
    """
    Generate quiz questions via AI in background.
    """
    try:
        llm = _get_llm()
        questions = []
        for _ in range(count):
            q = llm.generate_quiz_question(tree_type, concept, difficulty)
            questions.append(q)
        return {"questions": questions, "status": "completed"}
    except Exception as exc:
        logger.exception("AI quiz generation task failed")
        raise self.retry(exc=exc)


def dispatch_ai_diagnosis(
    tree_type: str,
    operation: str,
    violations: list,
) -> str:
    """Dispatch diagnosis task and return task ID."""
    task = ai_diagnose_task.delay(tree_type, operation, violations)
    return task.id


def dispatch_ai_teaching(
    tree_type: str,
    operation: str,
    diagnoses: list,
) -> str:
    """Dispatch teaching task and return task ID."""
    task = ai_teach_task.delay(tree_type, operation, diagnoses)
    return task.id


def get_task_result(task_id: str) -> Dict[str, Any] | None:
    """Retrieve a completed task result from Celery."""
    from celery.result import AsyncResult
    result = AsyncResult(task_id, app=celery_app)
    if result.ready():
        if result.successful():
            return result.result
        return {"status": "failed", "error": str(result.result)}
    return {"status": "pending"}
