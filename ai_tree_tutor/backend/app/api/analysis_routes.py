from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import get_llm
from app.llm.base_llm import LLMInterface

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "AI Tree Tutor API",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@router.get("/health")
async def health(llm: LLMInterface = Depends(get_llm)):
    return {
        "status": "healthy",
        "llm_available": llm.available,
        "llm_provider": llm.provider_name,
        "environment": settings.environment,
    }


@router.get("/complexity/{tree_type}/{operation}")
async def get_complexity(
    tree_type: str,
    operation: str,
    llm: LLMInterface = Depends(get_llm),
):
    return llm.explain_complexity(tree_type, operation)
