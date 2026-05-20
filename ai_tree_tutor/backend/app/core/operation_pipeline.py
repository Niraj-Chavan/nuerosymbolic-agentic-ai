from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.agents.base_agent import BaseAgent
from app.context.agent_context import AgentContext

logger = logging.getLogger(__name__)

Handler = Tuple[BaseAgent, Callable[[AgentContext], bool]]
AsyncHandler = Callable[[AgentContext], bool]


class OperationPipeline:
    def __init__(self):
        self._handlers: List[Handler] = []
        self._async_handlers: List[Tuple[BaseAgent, AsyncHandler]] = []
        self._event_listeners: Dict[str, List[Callable]] = {}
        self._parallel_groups: List[List[Handler]] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add_handler(
        self,
        agent: BaseAgent,
        condition: Optional[Callable[[AgentContext], bool]] = None,
    ) -> OperationPipeline:
        self._handlers.append((agent, condition or (lambda ctx: True)))
        logger.debug("Pipeline: registered %s", agent.name)
        return self

    def add_async_handler(
        self,
        agent: BaseAgent,
        condition: Optional[AsyncHandler] = None,
    ) -> OperationPipeline:
        self._async_handlers.append((agent, condition or (lambda ctx: True)))
        logger.debug("Pipeline: registered async handler %s", agent.name)
        return self

    def add_parallel_group(
        self,
        agents: List[Tuple[BaseAgent, Optional[Callable]]],
    ) -> OperationPipeline:
        group = [(a, c or (lambda ctx: True)) for a, c in agents]
        self._parallel_groups.append(group)
        logger.debug("Pipeline: registered parallel group with %d agents", len(agents))
        return self

    def remove_handler(self, agent: BaseAgent) -> None:
        self._handlers = [(a, c) for a, c in self._handlers if a is not agent]

    # ------------------------------------------------------------------
    # Event system
    # ------------------------------------------------------------------

    def on(self, event_type: str, listener: Callable) -> None:
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)

    def _emit(self, event_type: str, ctx: AgentContext, data: Optional[Dict] = None) -> None:
        for listener in self._event_listeners.get(event_type, []):
            try:
                listener(ctx, data or {})
            except Exception as e:
                logger.warning("Pipeline event listener error: %s", e)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self, ctx: AgentContext) -> AgentContext:
        logger.info(
            "Pipeline start: %s/%s/%s on %s",
            ctx.tree_type, ctx.operation, ctx.key, ctx.session_id,
        )

        ctx.pipeline_start_time = time.time()
        ctx.event_log.clear()

        ctx.record_event("pipeline_start", "Pipeline", {
            "tree_type": ctx.tree_type,
            "operation": ctx.operation,
        })

        try:
            await self._run_sequential(ctx)
            await self._run_async(ctx)
            await self._run_parallel_groups(ctx)
        except Exception as e:
            ctx.errors.append(f"Pipeline: {e}")
            logger.exception("Pipeline execution error: %s", e)

        duration = ctx.pipeline_duration_ms
        ctx.record_event("pipeline_end", "Pipeline", {
            "duration_ms": duration,
            "error_count": len(ctx.errors),
            "violation_count": len(ctx.violations),
        })

        self._emit("pipeline.complete", ctx, {"duration_ms": duration})

        logger.info(
            "Pipeline end: %d errors, %d violations, %.0fms",
            len(ctx.errors), len(ctx.violations), duration,
        )
        return ctx

    # ------------------------------------------------------------------
    # Sequential execution
    # ------------------------------------------------------------------

    async def _run_sequential(self, ctx: AgentContext) -> None:
        for agent, condition in self._handlers:
            if not condition(ctx):
                logger.debug("Pipeline: skipping %s (condition false)", agent.name)
                ctx.record_event("skip", agent.name, {"reason": "condition_false"})
                continue

            logger.debug("Pipeline: running %s", agent.name)
            start = time.time()
            try:
                ctx = await agent.process(ctx)
                elapsed = (time.time() - start) * 1000
                ctx.record_event("complete", agent.name, duration_ms=elapsed)
                self._emit(f"agent.{agent.name}.complete", ctx, {"duration_ms": elapsed})
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                ctx.errors.append(f"{agent.name}: {e}")
                ctx.record_event("error", agent.name, {
                    "error": str(e),
                    "duration_ms": elapsed,
                })
                logger.exception("Pipeline error in %s: %s", agent.name, e)
                self._emit(f"agent.{agent.name}.error", ctx, {"error": str(e)})
                if self._is_critical(agent):
                    logger.error("Pipeline: critical error in %s, aborting", agent.name)
                    ctx.record_event("abort", "Pipeline", {"reason": f"critical_error_in_{agent.name}"})
                    break

    # ------------------------------------------------------------------
    # Async (fire-and-forget) execution
    # ------------------------------------------------------------------

    async def _run_async(self, ctx: AgentContext) -> None:
        tasks = []
        for agent, condition in self._async_handlers:
            if not condition(ctx):
                continue
            task = asyncio.create_task(
                self._run_async_agent(agent, ctx),
                name=f"async_{agent.name}",
            )
            tasks.append(task)
            ctx.record_event("dispatched", agent.name, {"type": "async"})

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning("Async agent %s failed: %s", tasks[i].get_name(), result)

    async def _run_async_agent(self, agent: BaseAgent, ctx: AgentContext) -> None:
        start = time.time()
        try:
            await agent.process(ctx)
            elapsed = (time.time() - start) * 1000
            ctx.record_event("async_complete", agent.name, duration_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            ctx.record_event("async_error", agent.name, {
                "error": str(e),
                "duration_ms": elapsed,
            })
            raise

    # ------------------------------------------------------------------
    # Parallel group execution
    # ------------------------------------------------------------------

    async def _run_parallel_groups(self, ctx: AgentContext) -> None:
        for group in self._parallel_groups:
            qualified = [(a, c) for a, c in group if c(ctx)]
            if not qualified:
                continue

            ctx.record_event("parallel_start", "Pipeline", {
                "agent_count": len(qualified),
            })

            tasks = [
                self._run_single_in_group(agent, ctx)
                for agent, _ in qualified
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            ctx.record_event("parallel_end", "Pipeline", {
                "agent_count": len(qualified),
            })

    async def _run_single_in_group(self, agent: BaseAgent, ctx: AgentContext) -> None:
        start = time.time()
        try:
            await agent.process(ctx)
            elapsed = (time.time() - start) * 1000
            ctx.record_event("parallel_complete", agent.name, duration_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            ctx.record_event("parallel_error", agent.name, {
                "error": str(e),
                "duration_ms": elapsed,
            })
            raise

    # ------------------------------------------------------------------
    # Coordination strategy: adaptive decision-making
    # ------------------------------------------------------------------

    def configure_coordination(self, strategy: str = "balanced") -> None:
        if strategy == "fast":
            self._handlers = [h for h in self._handlers if not self._is_heavy(h[0])]
        elif strategy == "thorough":
            pass
        elif strategy == "diagnosis_first":
            self._handlers.sort(
                key=lambda h: 0 if h[0].name == "DiagnosisAgent" else 1
            )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._handlers.clear()
        self._async_handlers.clear()
        self._event_listeners.clear()
        self._parallel_groups.clear()

    @staticmethod
    def _is_critical(agent: BaseAgent) -> bool:
        critical = {"TreeExecutionAgent", "ValidationAgent"}
        return agent.name in critical

    @staticmethod
    def _is_heavy(agent: BaseAgent) -> bool:
        heavy = {"QuizAgent", "DiagnosisAgent"}
        return agent.name in heavy
