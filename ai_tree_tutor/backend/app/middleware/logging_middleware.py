"""
Structured Logging Middleware
==============================
Wraps each request with structlog context, logs request/response
with timing, and provides helpers for agent + LLM call logging.
"""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.processors import JSONRenderer, TimeStamper, add_log_level


def configure_structlog(environment: str = "development") -> None:
    processors = [
        structlog.stdlib.filter_by_level,
        add_log_level,
        TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if environment == "production":
        processors.append(JSONRenderer())
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    else:
        processors.append(structlog.dev.ConsoleRenderer())
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        query = str(request.url.query)

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        log = logger.bind(
            method=method,
            path=path,
            query=query,
            status=response.status_code,
            duration_ms=elapsed_ms,
        )

        if response.status_code >= 500:
            log.error("request_failed")
        elif response.status_code >= 400:
            log.warning("request_client_error")
        else:
            log.info("request_completed")

        return response


# ---------------------------------------------------------------------------
# Ad-hoc log helpers used inside routes / agents
# ---------------------------------------------------------------------------

def log_agent_execution(agent_name: str, duration_ms: float, result: str | None = None, error: str | None = None) -> None:
    log = logger.bind(agent=agent_name, duration_ms=round(duration_ms, 1))
    if error:
        log.error("agent_execution_failed", error=error)
    else:
        log.info("agent_execution_completed", result=result)


def log_llm_call(provider: str, model: str, latency_ms: float, tokens_in: int = 0, tokens_out: int = 0, error: str | None = None) -> None:
    log = logger.bind(provider=provider, model=model, latency_ms=round(latency_ms, 1), tokens_in=tokens_in, tokens_out=tokens_out)
    if error:
        log.error("llm_call_failed", error=error)
    else:
        log.info("llm_call_completed")


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    logger.bind(**context or {}).error(
        "unhandled_error",
        error_type=type(error).__name__,
        error_message=str(error),
        stack_trace=traceback.format_exc(),
    )
