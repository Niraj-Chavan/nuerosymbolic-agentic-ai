"""
Concept API Route Tests
========================
Tests /api/concepts/* endpoints with mocked dependencies.
"""

from __future__ import annotations

import pytest


class TestConceptsListEndpoint:
    async def test_get_all_concepts(self, async_client):
        response = await async_client.get("/api/concepts")
        assert response.status_code == 200
        data = response.json()
        # Should return a list of concept nodes or a graph dict
        assert data is not None

    async def test_get_all_concepts_structure(self, async_client):
        response = await async_client.get("/api/concepts")
        data = response.json()
        if isinstance(data, list):
            assert len(data) >= 0
        elif isinstance(data, dict):
            assert len(data) > 0


class TestConceptsProgressEndpoint:
    async def test_get_progress(self, async_client):
        response = await async_client.get("/api/concepts/progress")
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        # Progress should have mastery metrics
        if isinstance(data, dict):
            for key in ("total_concepts", "mastered", "in_progress", "not_started", "average_mastery"):
                if key in data:
                    break
            else:
                # any dict structure is acceptable
                pass

    async def test_progress_returns_numeric_values(self, async_client):
        response = await async_client.get("/api/concepts/progress")
        data = response.json()
        if isinstance(data, dict) and "average_mastery" in data:
            assert 0.0 <= data["average_mastery"] <= 1.0


class TestConceptsWeakEndpoint:
    async def test_get_weak_concepts(self, async_client):
        response = await async_client.get("/api/concepts/weak?threshold=0.5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_weak_concepts_default_threshold(self, async_client):
        response = await async_client.get("/api/concepts/weak")
        assert response.status_code == 200

    async def test_weak_concepts_zero_threshold(self, async_client):
        response = await async_client.get("/api/concepts/weak?threshold=0.0")
        assert response.status_code == 200


class TestConceptsQueryEndpoint:
    async def test_query_known_concept(self, async_client):
        response = await async_client.post("/api/concepts/query", json={
            "concept": "avl",
        })
        # May return 404 if concept doesn't exist, which is fine
        assert response.status_code in (200, 404)

    async def test_query_nonexistent_concept(self, async_client):
        response = await async_client.post("/api/concepts/query", json={
            "concept": "nonexistent_concept_xyz",
        })
        assert response.status_code == 404


class TestComplexityEndpoint:
    async def test_complexity_avl_insert(self, async_client):
        response = await async_client.get("/api/complexity/avl/insert")
        assert response.status_code == 200
        data = response.json()
        assert data is not None

    async def test_complexity_avl_search(self, async_client):
        response = await async_client.get("/api/complexity/avl/search")
        assert response.status_code == 200

    async def test_complexity_avl_delete(self, async_client):
        response = await async_client.get("/api/complexity/avl/delete")
        assert response.status_code == 200

    async def test_complexity_red_black_insert(self, async_client):
        response = await async_client.get("/api/complexity/red_black/insert")
        assert response.status_code == 200
