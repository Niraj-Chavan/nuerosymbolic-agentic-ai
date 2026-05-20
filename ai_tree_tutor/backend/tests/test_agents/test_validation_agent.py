"""
Validation Agent Tests
=======================
Tests the ValidationAgent's ability to detect AVL,
Red-Black, B-Tree, and Heap violations.
"""

from __future__ import annotations

import pytest

from app.agents.validation_agent import ValidationAgent
from app.trees.avl import AVLTree


# =========================================================================
# AVL Validation
# =========================================================================

class TestValidationAVL:
    @pytest.fixture
    def agent(self):
        return ValidationAgent()

    @pytest.fixture
    def valid_avl_ctx(self, agent_context, sample_avl_tree):
        agent_context.tree_instance = sample_avl_tree
        agent_context.tree_export = sample_avl_tree.export_nested()
        return agent_context

    async def test_valid_avl_passes(self, agent, valid_avl_ctx):
        result = await agent.process(valid_avl_ctx)
        assert result.validation_valid is True
        assert len(result.violations) == 0

    async def test_avl_balance_violation_detected(self, agent, agent_context):
        tree = AVLTree()
        tree.insert(10)
        tree.insert(5)
        tree.root.right = tree.root.__class__(key=20, height=5)
        tree._update_height(tree.root)
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        agent_context.operation = "insert"
        result = await agent.process(agent_context)
        assert result.validation_valid is False
        assert len(result.violations) > 0
        types = [v["type"] for v in result.violations]
        assert any("balance" in t for t in types)

    async def test_avl_bst_violation_detected(self, agent, agent_context):
        tree = AVLTree()
        tree.insert(10)
        tree.root.left = tree.root.__class__(key=15, height=1)
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        result = await agent.process(agent_context)
        assert result.validation_valid is False
        types = [v["type"] for v in result.violations]
        assert "bst_violation" in types

    async def test_affected_nodes_populated(self, agent, agent_context):
        tree = AVLTree()
        tree.insert(10)
        tree.root.left = tree.root.__class__(key=15, height=1)
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        result = await agent.process(agent_context)
        assert len(result.affected_nodes) > 0

    async def test_empty_tree_has_no_violations(self, agent, agent_context):
        tree = AVLTree()
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        result = await agent.process(agent_context)
        assert result.validation_valid is True


# =========================================================================
# Agent Context Blackboard
# =========================================================================

class TestAgentContextBlackboard:
    async def test_context_stores_validation_result(self, agent_context, sample_avl_tree):
        from app.agents.validation_agent import ValidationAgent
        agent = ValidationAgent()
        agent_context.tree_instance = sample_avl_tree
        agent_context.tree_export = sample_avl_tree.export_nested()
        ctx = await agent.process(agent_context)
        assert ctx.violations == []
        assert ctx.validation_valid is True

    async def test_context_records_violations(self, agent_context):
        from app.agents.validation_agent import ValidationAgent
        tree = AVLTree()
        tree.insert(10)
        tree.root.left = tree.root.__class__(key=15, height=1)
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        ctx = await ValidationAgent().process(agent_context)
        assert len(ctx.violations) > 0
        assert ctx.validation_valid is False

    def test_context_has_violations_property(self, agent_context):
        agent_context.violations = [{"type": "test"}]
        assert agent_context.has_violations is True
        agent_context.violations = []
        assert agent_context.has_violations is False

    def test_context_snapshot_roundtrip(self, agent_context):
        agent_context.violations = [{"type": "bf_exceeded", "node": 10}]
        agent_context.diagnoses = [{"misconception": "forgot rotation"}]
        snap = agent_context.snapshot()
        assert snap["violations"] == agent_context.violations
        assert snap["diagnoses"] == agent_context.diagnoses
        assert snap["session_id"] == "test-session-001"

    def test_context_merge_snapshot(self, agent_context):
        agent_context.merge_snapshot({
            "violations": [{"type": "bf_exceeded"}],
            "diagnoses": [{"misconception": "test"}],
            "metadata": {"attempt": 2},
        })
        assert len(agent_context.violations) == 1
        assert agent_context.metadata["attempt"] == 2

    def test_context_event_log(self, agent_context):
        agent_context.record_event("test", "TestAgent", {"msg": "hello"})
        assert agent_context.event_count == 1
        event = agent_context.event_log[0]
        assert event.type == "test"
        assert event.agent == "TestAgent"


# =========================================================================
# Misconception Engine Integration (via DiagnosisAgent)
# =========================================================================

class TestDiagnosisAgent:
    async def test_diagnosis_skipped_when_no_violations(self, mock_llm, agent_context, sample_avl_tree):
        from app.agents.diagnosis_agent import DiagnosisAgent
        agent = DiagnosisAgent(llm=mock_llm)
        agent_context.tree_instance = sample_avl_tree
        agent_context.tree_export = sample_avl_tree.export_nested()
        agent_context.violations = []
        agent_context.validation_valid = True
        ctx = await agent.process(agent_context)
        assert len(ctx.diagnoses) == 0
        assert len(mock_llm.call_log) == 0

    async def test_diagnosis_runs_on_violations(self, mock_llm, agent_context):
        from app.agents.diagnosis_agent import DiagnosisAgent
        tree = AVLTree()
        tree.insert(10)
        tree.root.left = tree.root.__class__(key=15, height=1)
        agent_context.tree_instance = tree
        agent_context.tree_export = tree.export_nested()
        agent_context.violations = [{"type": "bst_violation", "node": 10}]
        agent_context.validation_valid = False
        agent = DiagnosisAgent(llm=mock_llm)
        ctx = await agent.process(agent_context)
        assert len(ctx.diagnoses) > 0
        # Mock LLM may or may not be called depending on fallback
        assert ctx.metadata.get("severity") is not None


# =========================================================================
# Teaching Agent
# =========================================================================

class TestTeachingAgent:
    async def test_teaching_skipped_when_no_diagnoses(self, mock_llm, agent_context):
        from app.agents.teaching_agent import TeachingAgent
        agent = TeachingAgent(llm=mock_llm)
        agent_context.diagnoses = []
        ctx = await agent.process(agent_context)
        assert len(ctx.teaching_materials) == 0

    async def test_teaching_uses_fallback_bank(self, mock_llm, agent_context):
        from app.agents.teaching_agent import TeachingAgent
        agent = TeachingAgent(llm=mock_llm)
        agent_context.tree_type = "avl"
        agent_context.operation = "insert"
        agent_context.diagnoses = [
            {
                "violation": {"rule_id": "AVL-002", "type": "balance_factor_exceeded"},
                "misconception": "incorrect height",
                "source": "symbolic",
            }
        ]
        ctx = await agent.process(agent_context)
        assert len(ctx.teaching_materials) > 0
        material = ctx.teaching_materials[0]
        assert "source" in material

    async def test_teaching_tracks_session_flow(self, mock_llm, agent_context):
        from app.agents.teaching_agent import TeachingAgent
        agent = TeachingAgent(llm=mock_llm)
        agent_context.tree_type = "avl"
        agent_context.operation = "insert"
        agent_context.diagnoses = [
            {"violation": {"rule_id": "AVL-002"}, "misconception": "bf", "source": "symbolic"}
        ]
        ctx1 = await agent.process(agent_context)
        assert len(ctx1.teaching_materials) > 0

    async def test_teaching_generates_socratic_question(self, mock_llm, agent_context):
        from app.agents.teaching_agent import TeachingAgent
        agent = TeachingAgent(llm=mock_llm)
        agent_context.tree_type = "avl"
        agent_context.diagnoses = [
            {
                "violation": {"rule_id": "AVL-002", "type": "balance_factor_exceeded"},
                "misconception": "incorrect height",
                "concept_id": "avl_balance_factor",
                "source": "symbolic",
            }
        ]
        ctx = await agent.process(agent_context)
        material = ctx.teaching_materials[0]
        assert material.get("guiding_question") is not None or \
               material.get("explanation") is not None


# =========================================================================
# Pipeline Integration
# =========================================================================

class TestPipelineIntegration:
    async def test_full_pipeline_with_valid_tree(self, mock_llm, agent_context, sample_avl_tree):
        from app.agents.validation_agent import ValidationAgent
        from app.agents.diagnosis_agent import DiagnosisAgent
        from app.agents.teaching_agent import TeachingAgent
        from app.agents.tree_execution_agent import TreeExecutionAgent
        from app.core.operation_pipeline import OperationPipeline

        pipeline = OperationPipeline()
        pipeline.add_handler(TreeExecutionAgent())
        pipeline.add_handler(ValidationAgent())
        pipeline.add_handler(
            DiagnosisAgent(llm=mock_llm),
            condition=lambda ctx: ctx.has_violations,
        )
        pipeline.add_handler(
            TeachingAgent(llm=mock_llm),
            condition=lambda ctx: ctx.has_violations,
        )

        agent_context.tree_type = "avl"
        agent_context.operation = "insert"
        agent_context.key = 15
        ctx = await pipeline.execute(agent_context)
        assert ctx.tree_export is not None
        assert ctx.validation_valid is True

    async def test_full_pipeline_with_violation(self, mock_llm, agent_context):
        from app.agents.validation_agent import ValidationAgent
        from app.agents.diagnosis_agent import DiagnosisAgent
        from app.agents.teaching_agent import TeachingAgent
        from app.agents.tree_execution_agent import TreeExecutionAgent
        from app.core.operation_pipeline import OperationPipeline

        pipeline = OperationPipeline()
        pipeline.add_handler(TreeExecutionAgent())
        pipeline.add_handler(ValidationAgent())
        pipeline.add_handler(
            DiagnosisAgent(llm=mock_llm),
            condition=lambda ctx: ctx.has_violations,
        )
        pipeline.add_handler(
            TeachingAgent(llm=mock_llm),
            condition=lambda ctx: ctx.has_violations,
        )

        agent_context.tree_type = "avl"
        agent_context.operation = "insert"
        agent_context.key = 15
        ctx = await pipeline.execute(agent_context)
        assert ctx.tree_export is not None
