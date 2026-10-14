import traceback
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.agents.step_recorder import StepRecorderRegistry
from app.cache.redis_client import invalidate_tree_cache
from app.config import settings
from app.context.agent_context import AgentContext
from app.core.operation_pipeline import OperationPipeline
from app.dependencies import (
    get_pipeline,
    get_step_recorder,
    get_tree_agent,
)
from app.middleware.logging_middleware import log_agent_execution
from app.models.schemas import (
    RangeQueryRequest,
    TreeOperationRequest,
    TreeResetRequest,
)
from app.workers.tasks import dispatch_ai_diagnosis, dispatch_ai_teaching

router = APIRouter()


@router.get("")
async def list_trees():
    from app.core import tree_factory
    return {
        "trees": tree_factory.supported_trees(),
        "operations": tree_factory.supported_operations(),
    }


@router.post("/operate")
async def operate_tree(
    req: TreeOperationRequest,
    pipeline: OperationPipeline = Depends(get_pipeline),
):
    start = time.perf_counter()
    try:
        ctx = AgentContext(
            session_id=req.session_id,
            tree_type=req.tree_type,
            operation=req.operation,
            key=req.key,
            options=req.options,
        )
        ctx = await pipeline.execute(ctx)

        if ctx.has_errors:
            raise HTTPException(status_code=500, detail=ctx.errors)

        log_agent_execution("Pipeline", (time.perf_counter() - start) * 1000)

        await invalidate_tree_cache(req.session_id, req.tree_type)

        async_task_ids = {}
        if settings.async_ai_generation and ctx.has_violations:
            async_task_ids["diagnosis"] = dispatch_ai_diagnosis(
                ctx.tree_type, ctx.operation, ctx.violations,
            )
            async_task_ids["teaching"] = dispatch_ai_teaching(
                ctx.tree_type, ctx.operation, ctx.diagnoses,
            )

        resp = {
            "operation": req.operation,
            "key": req.key,
            "tree": ctx.tree_export,
            "log": ctx.operation_log,
            "validation": {
                "valid": ctx.validation_valid,
                "violations": ctx.violations,
                "affected_nodes": ctx.affected_nodes,
            },
            "diagnosis": {"misconceptions": ctx.diagnoses} if ctx.diagnoses else None,
            "teaching": ctx.teaching_materials or None,
            "complexity": ctx.complexity,
            "concept_update": ctx.concept_updates,
            "async_task_ids": async_task_ids or None,
            "found": ctx.found,
            "search_path": ctx.search_path,
        }
        return resp

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_tree(
    req: TreeResetRequest,
    tree_agent=Depends(get_tree_agent),
):
    try:
        return tree_agent.reset(req.tree_type, req.session_id, **req.options)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/{tree_type}")
async def export_tree(
    tree_type: str,
    session_id: str = "default",
    heap_type: Optional[str] = None,
    order: Optional[int] = None,
    tree_agent=Depends(get_tree_agent),
):
    options = {}
    if heap_type:
        options["heap_type"] = heap_type
    if order:
        options["order"] = order
    return tree_agent.get_tree_export(tree_type, session_id, **options)


@router.post("/operate-steps")
async def operate_steps(
    req: TreeOperationRequest,
    tree_agent=Depends(get_tree_agent),
    step_recorder: StepRecorderRegistry = Depends(get_step_recorder),
):
    try:
        tree = tree_agent.get_or_create(req.tree_type, req.session_id, **req.options)
        result = step_recorder.record(req.tree_type, req.operation, tree, req.key, **req.options)
        return {
            "operation": req.operation,
            "key": req.key,
            "tree": result.get("tree"),
            "log": result.get("log", []),
            "animation_steps": result.get("animation_steps", []),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment/range-query")
async def segment_range_query(
    req: RangeQueryRequest,
    tree_agent=Depends(get_tree_agent),
):
    tree = tree_agent.get_or_create("segment_tree", req.session_id)
    return tree.range_query(req.left, req.right)
