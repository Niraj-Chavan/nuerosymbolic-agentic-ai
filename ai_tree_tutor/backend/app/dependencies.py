from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request

from app.agents.base_agent import BaseAgent
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.step_recorder import StepRecorderRegistry
from app.agents.teaching_agent import TeachingAgent
from app.agents.tree_execution_agent import TreeExecutionAgent
from app.agents.validation_agent import ValidationAgent
from app.config import settings
from app.context.agent_context import AgentContext
from app.core.operation_pipeline import OperationPipeline
from app.llm.base_llm import LLMInterface
from app.llm.gemini_engine import GeminiEngine
from app.llm.openai_engine import OpenAIEngine
from app.agents.emotional_tracker import EmotionalStateTracker
from app.agents.meta_cognitive_agent import MetaCognitiveAgent
from app.agents.diagnostic_intelligence_agent import DiagnosticIntelligenceAgent
from app.agents.curriculum_architect_agent import CurriculumArchitectAgent
_llm: LLMInterface | None = None
_tree_agent: TreeExecutionAgent | None = None
_validation_agent: ValidationAgent | None = None
_diagnosis_agent: DiagnosisAgent | None = None
_teaching_agent: TeachingAgent | None = None
_concept_agent: ConceptGraphAgent | None = None
_quiz_agent: QuizAgent | None = None
_emotional_tracker: EmotionalStateTracker | None = None
_meta_agent: MetaCognitiveAgent | None = None
_diagnostic_agent: DiagnosticIntelligenceAgent | None = None
_curriculum_agent: CurriculumArchitectAgent | None = None
_session_memory: dict | None = None


def init_services() -> None:
    global _llm, _tree_agent, _validation_agent
    global _diagnosis_agent, _teaching_agent, _concept_agent, _quiz_agent
    global _emotional_tracker, _meta_agent, _diagnostic_agent, _curriculum_agent
    global _session_memory

    _llm = _create_llm()
    _tree_agent = TreeExecutionAgent()
    _validation_agent = ValidationAgent()
    _concept_agent = ConceptGraphAgent()
    _diagnosis_agent = DiagnosisAgent(llm=_llm)
    _teaching_agent = TeachingAgent(llm=_llm)
    _quiz_agent = QuizAgent(llm=_llm, concept_graph=_concept_agent)
    _emotional_tracker = EmotionalStateTracker(llm=_llm)
    _meta_agent = MetaCognitiveAgent(llm=_llm, concept_agent=_concept_agent, emotional_tracker=_emotional_tracker)
    _diagnostic_agent = DiagnosticIntelligenceAgent(llm=_llm, concept_agent=_concept_agent, emotional_tracker=_emotional_tracker)
    _curriculum_agent = CurriculumArchitectAgent(llm=_llm, concept_agent=_concept_agent)
    _session_memory = {}



def shutdown_services() -> None:
    global _llm, _tree_agent, _validation_agent
    global _diagnosis_agent, _teaching_agent, _concept_agent, _quiz_agent
    global _emotional_tracker, _meta_agent, _diagnostic_agent, _curriculum_agent
    global _session_memory
    _llm = None
    _tree_agent = None
    _validation_agent = None
    _diagnosis_agent = None
    _teaching_agent = None
    _concept_agent = None
    _quiz_agent = None
    _emotional_tracker = None
    _meta_agent = None
    _diagnostic_agent = None
    _curriculum_agent = None
    _session_memory = None



def _create_llm() -> LLMInterface:
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return GeminiEngine(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if provider == "openai":
        return OpenAIEngine(api_key=settings.openai_api_key, model=settings.openai_model)
    if provider == "mock":
        from tests.conftest import MockLLM
        return MockLLM()
    raise ValueError(f"Unknown LLM provider: {provider}")


# ---------------------------------------------------------------------------
# Session-aware context factory
# ---------------------------------------------------------------------------

def make_context(request: Request) -> AgentContext:
    ctx = AgentContext()
    session_id = request.headers.get("X-Session-Id", "default")

    if session_id in (_session_memory or {}):
        ctx.session_state.update(_session_memory[session_id])

    ctx.session_id = session_id
    ctx.store("session_id", session_id)
    return ctx


def persist_context(ctx: AgentContext) -> None:
    if _session_memory is not None:
        _session_memory[ctx.session_id] = dict(ctx.session_state)


async def parse_operation_request(request: Request) -> AgentContext:
    body = await request.json()
    session_id = body.get("session_id", "default")
    ctx = AgentContext(
        session_id=session_id,
        tree_type=body.get("tree_type", ""),
        operation=body.get("operation", ""),
        key=body.get("key"),
        options=body.get("options", {}),
    )

    if session_id in (_session_memory or {}):
        ctx.session_state.update(_session_memory[session_id])

    return ctx


# ---------------------------------------------------------------------------
# FastAPI dependency callables
# ---------------------------------------------------------------------------

def get_llm() -> LLMInterface:
    if _llm is None:
        raise RuntimeError("LLM not initialised.")
    return _llm


def get_tree_agent() -> TreeExecutionAgent:
    if _tree_agent is None:
        raise RuntimeError("TreeExecutionAgent not initialised.")
    return _tree_agent


def get_validation_agent() -> ValidationAgent:
    if _validation_agent is None:
        raise RuntimeError("ValidationAgent not initialised.")
    return _validation_agent


def get_concept_agent() -> ConceptGraphAgent:
    if _concept_agent is None:
        raise RuntimeError("ConceptGraphAgent not initialised.")
    return _concept_agent


def get_diagnostic_agent() -> DiagnosticIntelligenceAgent:
    if _diagnostic_agent is None:
        raise RuntimeError("DiagnosticIntelligenceAgent not initialised.")
    return _diagnostic_agent


def get_curriculum_agent() -> CurriculumArchitectAgent:
    if _curriculum_agent is None:
        raise RuntimeError("CurriculumArchitectAgent not initialised.")
    return _curriculum_agent


def get_quiz_agent() -> QuizAgent:
    if _quiz_agent is None:
        raise RuntimeError("QuizAgent not initialised.")
    return _quiz_agent


def get_diagnosis_agent() -> DiagnosisAgent:
    if _diagnosis_agent is None:
        raise RuntimeError("DiagnosisAgent not initialised.")
    return _diagnosis_agent


def get_teaching_agent() -> TeachingAgent:
    if _teaching_agent is None:
        raise RuntimeError("TeachingAgent not initialised.")
    return _teaching_agent


def get_step_recorder() -> StepRecorderRegistry:
    return StepRecorderRegistry()


def get_session_memory() -> dict:
    if _session_memory is None:
        raise RuntimeError("Session memory not initialised.")
    return _session_memory


def get_emotional_tracker() -> EmotionalStateTracker:
    if _emotional_tracker is None:
        raise RuntimeError("EmotionalStateTracker not initialised.")
    return _emotional_tracker


def get_meta_agent() -> MetaCognitiveAgent:
    if _meta_agent is None:
        raise RuntimeError("MetaCognitiveAgent not initialised.")
    return _meta_agent



def get_pipeline() -> OperationPipeline:
    pipeline = OperationPipeline()
    pipeline.add_handler(get_tree_agent())
    pipeline.add_handler(get_validation_agent())
    pipeline.add_handler(
        get_diagnosis_agent(),
        condition=lambda ctx: ctx.has_violations,
    )
    pipeline.add_handler(
        get_teaching_agent(),
        condition=lambda ctx: ctx.has_violations,
    )
    pipeline.add_handler(get_concept_agent())

    pipeline.on("agent.ValidationAgent.complete", lambda ctx, data: (
        ctx.store("last_validation_time", data.get("duration_ms", 0))
    ))

    return pipeline
