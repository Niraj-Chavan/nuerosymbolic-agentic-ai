from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.concept_graph_agent import ConceptGraphAgent
from app.agents.quiz_agent import QuizAgent
from app.dependencies import get_concept_agent, get_quiz_agent
from app.models.schemas import (
    HintRequest,
    QuizGenerateRequest,
    QuizSubmitRequest,
)
from app.workers.tasks import get_task_result

router = APIRouter()


@router.post("/generate")
async def generate_quiz(
    req: QuizGenerateRequest,
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
):
    try:
        return quiz_agent.generate_quiz(
            tree_type=req.tree_type,
            num_questions=req.num_questions,
            difficulty=req.difficulty,
            focus_weak=req.focus_weak,
            question_types=req.question_types,
            misconception_targeted=req.misconception_targeted,
            target_mastery=req.target_mastery,
            max_question_difficulty=req.max_question_difficulty,
            session_id="default",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_quiz(
    req: QuizSubmitRequest,
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
):
    try:
        return quiz_agent.evaluate_quiz(
            req.questions, req.answers,
            session_id=req.session_id,
            attempt_number=req.attempt_number,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def suggest_next_quiz(
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
    session_id: str = Query(default="default"),
    tree_type: str = Query(default=None),
):
    try:
        return quiz_agent.suggest_next_quiz(
            session_id=session_id,
            tree_type=tree_type or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hint")
async def generate_hint(
    req: HintRequest,
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
):
    try:
        return quiz_agent.generate_hint(
            tree_type=req.tree_type,
            operation=req.operation,
            violation=req.violation,
            attempt_number=req.attempt_number,
            previous_hints=req.previous_hints,
            student_ability=req.student_ability,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conceptual-depth")
async def conceptual_depth(
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
    session_id: str = Query(default="default"),
    tree_type: str = Query(default=None),
):
    try:
        return quiz_agent.assess_conceptual_depth(
            session_id=session_id,
            tree_type=tree_type or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def quiz_history(
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
    session_id: str = Query(default=None),
):
    return quiz_agent.get_quiz_history(session_id=session_id or None)


@router.get("/report")
async def learning_report(
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
    session_id: str = Query(default=None),
):
    return quiz_agent.get_learning_report(session_id=session_id or None)


@router.get("/recommendations")
async def get_recommendations(
    quiz_agent: QuizAgent = Depends(get_quiz_agent),
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    weak = concept_agent.get_weak_concepts(threshold=0.5)
    recs = []
    for w in weak:
        ops = quiz_agent._suggest_operations(w["concept"])
        recs.append({
            "concept": w["concept"],
            "mastery": w["mastery"],
            "suggested_operations": ops,
            "priority": "high" if w["mastery"] < 0.3 else "medium",
        })
    return recs


@router.get("/task/{task_id}")
async def get_task(
    task_id: str,
):
    result = get_task_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
