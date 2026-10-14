"""
Quiz Background Tasks
======================
Specialised async tasks for quiz operations.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.workers.celery_app import celery_app
from app.workers.tasks import _get_llm


@celery_app.task(bind=True, max_retries=3)
def evaluate_quiz_answers_task(
    self,
    questions: List[Dict[str, Any]],
    answers: List[int],
) -> Dict[str, Any]:
    """Evaluate quiz answers in background and generate feedback."""
    try:
        llm = _get_llm()
        score = 0
        feedback_list = []

        for i, (q, ans) in enumerate(zip(questions, answers)):
            correct = q.get("correct_index", -1)
            is_correct = ans == correct
            if is_correct:
                score += 1

            ai_feedback = llm.evaluate_answer(q, str(ans))
            feedback_list.append({
                "question_index": i,
                "correct": is_correct,
                "ai_feedback": ai_feedback,
            })

        total = len(questions)
        return {
            "score": score,
            "total": total,
            "percentage": round(score / total * 100, 1) if total else 0,
            "feedback": feedback_list,
            "status": "completed",
        }
    except Exception as exc:
        raise self.retry(exc=exc)
