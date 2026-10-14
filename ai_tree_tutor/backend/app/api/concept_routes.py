from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_concept_agent
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.models.schemas import ConceptQueryRequest

router = APIRouter()


@router.get("")
async def get_all_concepts(
    agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    return agent.get_full_graph()


@router.get("/progress")
async def get_progress(
    agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    return agent.get_progress_summary()


@router.get("/weak")
async def get_weak_concepts(
    threshold: float = 0.4,
    agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    return agent.get_weak_concepts(threshold)


@router.post("/query")
async def query_concept(
    req: ConceptQueryRequest,
    agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    result = agent.get_concept_data(req.concept)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept}' not found")
    return result
