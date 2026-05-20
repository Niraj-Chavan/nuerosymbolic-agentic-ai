"""
Diagnosis Agent v2 — Neuro-Symbolic Misconception Detection
=============================================================
Integrates the MisconceptionEngine v2 into the agent pipeline.
Provides both synchronous (symbolic) and neural-augmented (LLM) paths.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.agents.misconception_engine import (
    MisconceptionEngine,
    MisconceptionDiagnosis,
    RemediationPlan,
    SeverityLevel,
    StudentProfile,
)
from app.context.agent_context import AgentContext
from app.llm.base_llm import LLMInterface


class DiagnosisAgent(BaseAgent):
    """
    Diagnoses misconceptions using the MisconceptionEngine v2.
    
    Dual path:
      1. Symbolic: MisconceptionEngine taxonomy + prerequisite inference
      2. Neural: LLM augmentation for nuanced explanations
    
    The symbolic path runs synchronously in the request pipeline.
    The neural path is dispatched asynchronously for enrichment.
    """

    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.engine = MisconceptionEngine()
        # Per-session student profiles
        self._profiles: Dict[str, StudentProfile] = {}

    def _get_profile(self, session_id: str) -> StudentProfile:
        if session_id not in self._profiles:
            self._profiles[session_id] = self.engine.create_profile()
        return self._profiles[session_id]

    async def process(self, ctx: AgentContext) -> AgentContext:
        if not ctx.has_violations:
            return ctx

        profile = self._get_profile(ctx.session_id)
        tree_type = ctx.tree_type
        operation = ctx.operation

        # Phase 1: Symbolic diagnosis via MisconceptionEngine
        diagnoses = self.engine.analyze(profile, tree_type, operation, ctx.violations)
        plan = self.engine.remediate(profile, diagnoses, tree_type, operation)

        # Phase 2: Neural enrichment (optional, non-blocking)
        enriched = []
        for d in diagnoses:
            entry = self._diagnosis_to_dict(d)
            if self.llm.available:
                try:
                    ai_insight = self.llm.diagnose_misconception(
                        tree_type, operation, self._violation_for(d, ctx.violations),
                    )
                    if ai_insight and "misconception" in ai_insight:
                        entry["ai_insight"] = ai_insight["misconception"]
                        entry["source"] = "neuro_symbolic"
                except Exception:
                    pass
            enriched.append(entry)

        # Phase 3: Build pipeline output
        ctx.diagnoses = enriched
        ctx.metadata["remediation_plan"] = self._plan_to_dict(plan)
        ctx.metadata["severity"] = plan.overall_severity.name.lower()
        ctx.metadata["profile_summary"] = self.engine.get_profile_summary(profile)

        return ctx

    # ------------------------------------------------------------------
    # Profile access for other agents
    # ------------------------------------------------------------------

    def get_mastery_summary(self, session_id: str, tree_type: str) -> Dict[str, Any]:
        profile = self._get_profile(session_id)
        return self.engine.get_mastery_summary(profile, tree_type)

    def get_profile_summary(self, session_id: str) -> Dict[str, Any]:
        profile = self._get_profile(session_id)
        return self.engine.get_profile_summary(profile)

    def get_remediation(self, session_id: str, tree_type: str, operation: str,
                        violations: List[Dict]) -> Dict[str, Any]:
        profile = self._get_profile(session_id)
        diagnoses = self.engine.analyze(profile, tree_type, operation, violations)
        plan = self.engine.remediate(profile, diagnoses, tree_type, operation)
        return self._plan_to_dict(plan)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _diagnosis_to_dict(d: MisconceptionDiagnosis) -> Dict[str, Any]:
        return {
            "concept_id": d.concept_id,
            "concept_name": d.concept_name,
            "pattern": d.pattern.value,
            "root_cause": d.root_cause,
            "description": d.description,
            "false_belief": d.false_belief,
            "severity": d.severity.name.lower(),
            "confidence": round(d.confidence, 2),
            "prerequisite_gaps": d.prerequisite_gaps,
            "affected_operations": d.affected_operations,
            "source": "symbolic",
        }

    @staticmethod
    def _plan_to_dict(plan: RemediationPlan) -> Dict[str, Any]:
        return {
            "overall_severity": plan.overall_severity.name.lower(),
            "critical_gaps": plan.critical_gaps,
            "recommended_focus": plan.recommended_focus,
            "estimated_sessions": plan.estimated_sessions,
            "learning_path": [
                {
                    "step_type": p.step_type,
                    "description": p.description,
                    "prerequisites_met": p.prerequisites_met,
                    "estimated_mastery_gain": p.estimated_mastery_gain,
                }
                for p in plan.learning_path[:10]
            ],
        }

    @staticmethod
    def _violation_for(d: MisconceptionDiagnosis, violations: List[Dict]) -> Dict:
        """Find the first violation that maps to this diagnosis."""
        for v in violations:
            vtype = v.get("type", v.get("rule_id", ""))
            if d.concept_id in str(vtype) or d.concept_name.lower() in str(v.get("message", "")).lower():
                return v
        return violations[0] if violations else {}
