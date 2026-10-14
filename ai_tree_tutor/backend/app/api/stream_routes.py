"""
SSE Stream Routes
==================
Server-Sent Events for streaming AI explanation chunks
to the frontend in real-time.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_llm
from app.llm.base_llm import LLMInterface
from app.llm.gemini_engine import GeminiEngine

logger = logging.getLogger(__name__)

router = APIRouter()


async def _stream_explanation(
    llm: LLMInterface,
    tree_type: str,
    operation: str,
    violation: dict,
    misconception: str,
    false_belief: str = "",
    prerequisite_gaps: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Yield SSE-formatted strings for each chunk of the AI explanation.

    Falls back to yielding the full response if the LLM does not
    support streaming.
    """
    if not llm.available:
        yield _sse_event("error", {"message": "LLM service unavailable"})
        return

    if isinstance(llm, GeminiEngine) and hasattr(llm, "stream_explanation"):
        async for chunk in llm.stream_explanation(
            tree_type, operation, violation, misconception,
            false_belief=false_belief,
            prerequisite_gaps=prerequisite_gaps or [],
        ):
            yield _sse_event("chunk", {"text": chunk})
        yield _sse_event("done", {})
    else:
        try:
            result = llm.generate_explanation(
                tree_type, operation, violation, misconception,
                false_belief=false_belief or None,
                prerequisite_gaps=prerequisite_gaps or None,
            )
            if result:
                yield _sse_event("full", result)
            else:
                yield _sse_event("error", {"message": "Empty response from LLM"})
        except Exception as e:
            logger.exception("Explanation generation failed")
            yield _sse_event("error", {"message": str(e)})
        finally:
            yield _sse_event("done", {})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.get("/explanation/{operation_id}")
async def stream_explanation(
    operation_id: str,
    tree_type: str = "avl",
    operation: str = "insert",
    key: int = 0,
    llm: LLMInterface = Depends(get_llm),
):
    """
    SSE endpoint that streams an AI explanation for a given operation.

    Query params:
    - tree_type (default: avl)
    - operation (default: insert)
    - key (default: 0)

    Frontend usage::

        const source = new EventSource(
            `/api/stream/explanation/${opId}?tree_type=avl&operation=insert&key=15`
        );
        source.addEventListener("chunk", (e) => updateText(JSON.parse(e.data).text));
        source.addEventListener("done", (e) => source.close());
        source.addEventListener("error", (e) => console.error(e));
    """
    violation = {
        "type": "streaming_explanation",
        "rule_id": operation_id,
        "node": key,
    }
    misconception = f"Reviewing {operation} on {tree_type} with key {key}"

    return EventSourceResponse(
        _stream_explanation(
            llm, tree_type, operation, violation, misconception,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/teaching/{session_id}")
async def stream_teaching(
    session_id: str,
    tree_type: str = "avl",
    operation: str = "insert",
    misconception: str = "",
    llm: LLMInterface = Depends(get_llm),
):
    """
    SSE endpoint for streaming teaching explanations by session.
    """
    violation = {"type": "teaching", "session": session_id}

    return EventSourceResponse(
        _stream_explanation(
            llm, tree_type, operation, violation, misconception,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
