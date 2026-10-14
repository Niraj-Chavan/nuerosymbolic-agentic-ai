"""
Tree API Route Tests
=====================
Tests /api/tree/* endpoints using the async test client.
Mocks all LLM dependencies to avoid API calls.
"""

from __future__ import annotations

import pytest


class TestTreeListEndpoint:
    async def test_list_trees(self, async_client):
        response = await async_client.get("/api/tree")
        assert response.status_code == 200
        data = response.json()
        assert "trees" in data
        assert "operations" in data
        assert "avl" in data["trees"]
        assert "insert" in data["operations"]

    async def test_list_trees_returns_all_supported(self, async_client):
        response = await async_client.get("/api/tree")
        data = response.json()
        expected = {"avl", "red_black", "heap", "segment_tree", "btree", "bplus_tree"}
        assert expected.issubset(set(data["trees"]))


class TestTreeOperateEndpoint:
    async def test_insert_operation(self, async_client):
        payload = {
            "tree_type": "avl",
            "operation": "insert",
            "key": 10,
            "session_id": "test-insert",
        }
        response = await async_client.post("/api/tree/operate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "insert"
        assert data["key"] == 10
        assert data["tree"] is not None
        assert data["tree"]["key"] == 10

    async def test_multiple_inserts(self, async_client):
        sid = "test-multi-insert"
        for key in [30, 20, 10]:
            resp = await async_client.post("/api/tree/operate", json={
                "tree_type": "avl", "operation": "insert", "key": key,
                "session_id": sid,
            })
            assert resp.status_code == 200
        # After 30,20,10 the root should be 20
        resp = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "search", "key": 999,
            "session_id": sid,
        })
        tree = resp.json()["tree"]
        assert tree["key"] == 20

    async def test_delete_operation(self, async_client):
        sid = "test-delete"
        for key in [10, 20, 5]:
            await async_client.post("/api/tree/operate", json={
                "tree_type": "avl", "operation": "insert", "key": key,
                "session_id": sid,
            })
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "delete", "key": 5,
            "session_id": sid,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "delete"

    async def test_search_found(self, async_client):
        sid = "test-search-found"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 42,
            "session_id": sid,
        })
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "search", "key": 42,
            "session_id": sid,
        })
        assert response.status_code == 200

    async def test_search_not_found(self, async_client):
        sid = "test-search-miss"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": sid,
        })
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "search", "key": 999,
            "session_id": sid,
        })
        assert response.status_code == 200

    async def test_operation_returns_validation(self, async_client):
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": "test-validation",
        })
        data = response.json()
        assert "validation" in data
        assert "valid" in data["validation"]
        assert data["validation"]["valid"] is True

    async def test_operation_returns_log(self, async_client):
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": "test-log",
        })
        data = response.json()
        assert "log" in data
        assert isinstance(data["log"], list)

    async def test_invalid_tree_type_returns_error(self, async_client):
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "nonexistent_tree",
            "operation": "insert",
            "key": 10,
        })
        assert response.status_code == 500
        assert "Unknown tree type" in response.text

    async def test_invalid_operation_returns_error(self, async_client):
        response = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl",
            "operation": "fly",
            "key": 10,
        })
        assert response.status_code == 500
        assert "Unknown operation" in response.text

    async def test_operate_with_validation_response_shape(self, async_client):
        sid = "test-shape"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 50,
            "session_id": sid,
        })
        resp = await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 30,
            "session_id": sid,
        })
        data = resp.json()
        assert "tree" in data
        assert "log" in data
        assert "validation" in data
        assert data["validation"]["valid"] in (True, False)


class TestTreeResetEndpoint:
    async def test_reset_tree(self, async_client):
        sid = "test-reset"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": sid,
        })
        reset_resp = await async_client.post("/api/tree/reset", json={
            "tree_type": "avl", "session_id": sid,
        })
        assert reset_resp.status_code == 200
        assert reset_resp.json()["status"] == "reset"

    async def test_reset_clears_tree(self, async_client):
        sid = "test-reset-clear"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": sid,
        })
        await async_client.post("/api/tree/reset", json={
            "tree_type": "avl", "session_id": sid,
        })
        resp = await async_client.get(f"/api/tree/export/avl?session_id={sid}")
        assert resp.json()["tree"] is None


class TestTreeExportEndpoint:
    async def test_export_empty_tree(self, async_client):
        response = await async_client.get("/api/tree/export/avl?session_id=test-export-empty")
        assert response.status_code == 200
        data = response.json()
        assert "tree" in data

    async def test_export_after_insert(self, async_client):
        sid = "test-export-populated"
        await async_client.post("/api/tree/operate", json={
            "tree_type": "avl", "operation": "insert", "key": 42,
            "session_id": sid,
        })
        response = await async_client.get(f"/api/tree/export/avl?session_id={sid}")
        data = response.json()
        assert data["tree"] is not None
        assert data["tree"]["key"] == 42


class TestTreeOperateStepsEndpoint:
    async def test_operate_steps_returns_animation_data(self, async_client):
        response = await async_client.post("/api/tree/operate-steps", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": "test-steps",
        })
        assert response.status_code == 200
        data = response.json()
        assert "animation_steps" in data
        assert "log" in data

    async def test_operate_steps_with_rotation(self, async_client):
        sid = "test-steps-rotation"
        await async_client.post("/api/tree/operate-steps", json={
            "tree_type": "avl", "operation": "insert", "key": 30,
            "session_id": sid,
        })
        await async_client.post("/api/tree/operate-steps", json={
            "tree_type": "avl", "operation": "insert", "key": 20,
            "session_id": sid,
        })
        # Third insert triggers a rotation
        resp = await async_client.post("/api/tree/operate-steps", json={
            "tree_type": "avl", "operation": "insert", "key": 10,
            "session_id": sid,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data.get("animation_steps", [])) > 0
        descriptions = [s.get("description", "") for s in data.get("animation_steps", [])]
        assert any("rotation" in d.lower() for d in descriptions)


class TestHealthEndpoint:
    async def test_health_returns_status(self, async_client):
        response = await async_client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    async def test_health_endpoint(self, async_client):
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["llm_provider"] == "mock"
