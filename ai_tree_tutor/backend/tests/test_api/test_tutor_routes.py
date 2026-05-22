from __future__ import annotations

import pytest


class TestTutorEndpoints:
    async def test_get_weak_concepts(self, async_client):
        response = await async_client.get("/api/tutor/weak-concepts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_tutor_chat(self, async_client):
        payload = {
            "message": "Explain how AVL balancing works",
            "history": [],
            "concept_id": "avl_balance_factor"
        }
        response = await async_client.post("/api/tutor/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)

    async def test_remedy_start(self, async_client):
        payload = {
            "concept_id": "avl_balance_factor"
        }
        response = await async_client.post("/api/tutor/remedy/start", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["concept_id"] == "avl_balance_factor"
        assert "message" in data

    async def test_remedy_verify(self, async_client):
        payload = {
            "concept_id": "avl_balance_factor",
            "is_correct": True
        }
        response = await async_client.post("/api/tutor/remedy/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "new_mastery" in data

    async def test_get_diagnosis(self, async_client):
        response = await async_client.get("/api/tutor/diagnosis/student123")
        assert response.status_code == 200
        data = response.json()
        assert "student_id" in data
        assert data["student_id"] == "student123"
        assert "current_state" in data
        assert "predicted_mastery" in data
        assert "knowledge_dimension" in data["current_state"]
        assert "emotional_dimension" in data["current_state"]

    async def test_get_learning_path(self, async_client):
        response = await async_client.get("/api/tutor/learning-path/student123")
        assert response.status_code == 200
        data = response.json()
        assert "student_id" in data
        assert data["student_id"] == "student123"
        assert "learning_path" in data
        assert "enriched_curriculum" in data
        assert "teaching_modalities" in data["enriched_curriculum"]
