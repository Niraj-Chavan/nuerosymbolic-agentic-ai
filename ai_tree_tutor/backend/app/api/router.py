"""
API Router — Aggregates all sub-routers
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.tree_routes import router as tree_router
from app.api.concept_routes import router as concept_router
from app.api.quiz_routes import router as quiz_router
from app.api.analysis_routes import router as analysis_router
from app.api.stream_routes import router as stream_router
from app.api.tutor_routes import router as tutor_router

router = APIRouter(prefix="/api")

router.include_router(tree_router, prefix="/tree")
router.include_router(concept_router, prefix="/concepts")
router.include_router(quiz_router, prefix="/quiz")
router.include_router(analysis_router)
router.include_router(stream_router, prefix="/stream")
router.include_router(tutor_router, prefix="/tutor")
