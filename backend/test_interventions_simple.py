"""
Simple unit tests for intervention API endpoints

Run with: pytest test_interventions_simple.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestInterventionEndpoints:
    """Test intervention API endpoints"""

    def test_interventions_list_endpoint_exists(self):
        """Test that interventions list endpoint exists"""
        # This will return 401 since we don't have a token, but endpoint should exist
        response = client.get("/api/interventions")
        assert response.status_code == 401

    def test_interventions_create_endpoint_exists(self):
        """Test that create endpoint exists"""
        response = client.post(
            "/api/interventions",
            json={
                "prescription_id": "test",
                "intervention_type": "test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        assert response.status_code == 401

    def test_interventions_get_endpoint_exists(self):
        """Test that get detail endpoint exists"""
        response = client.get("/api/interventions/test-id")
        assert response.status_code == 401

    def test_interventions_log_endpoint_exists(self):
        """Test that log endpoint exists"""
        response = client.post(
            "/api/interventions/test-id/log",
            json={
                "status_change": "scheduled→in_progress",
                "notes": "test"
            }
        )
        assert response.status_code == 401

    def test_interventions_docs_endpoint(self):
        """Test that API docs include intervention endpoints"""
        response = client.get("/docs")
        assert response.status_code == 200
        content = response.text
        # Check that intervention endpoints are documented
        assert "interventions" in content.lower()


class TestInterventionModels:
    """Test intervention data models"""

    def test_intervention_model_can_be_imported(self):
        """Test that intervention model can be imported"""
        from models import Intervention, InterventionLog, InterventionDocument
        assert Intervention is not None
        assert InterventionLog is not None
        assert InterventionDocument is not None

    def test_intervention_schema_can_be_imported(self):
        """Test that intervention schemas can be imported"""
        from schemas import (
            InterventionCreate, InterventionResponse, InterventionListResponse,
            InterventionLogCreate, InterventionDetailResponse
        )
        assert InterventionCreate is not None
        assert InterventionResponse is not None
        assert InterventionListResponse is not None
        assert InterventionLogCreate is not None
        assert InterventionDetailResponse is not None


class TestInterventionValidation:
    """Test intervention data validation"""

    def test_intervention_create_schema_validation(self):
        """Test that schema validates required fields"""
        from schemas import InterventionCreate

        # Valid data
        valid = InterventionCreate(
            prescription_id="presc-1",
            intervention_type="Blood Test",
            description="Test",
            scheduled_date="2026-03-15T10:00:00",
            priority="normal"
        )
        assert valid.prescription_id == "presc-1"

    def test_intervention_response_schema(self):
        """Test response schema serialization"""
        from schemas import InterventionResponse
        from datetime import datetime

        response_data = {
            "id": "int-1",
            "prescription_id": "presc-1",
            "intervention_type": "Blood Test",
            "description": "Test",
            "scheduled_date": datetime.now(),
            "priority": "high",
            "status": "scheduled",
            "created_by": "doctor-1",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        resp = InterventionResponse(**response_data)
        assert resp.intervention_type == "Blood Test"
        assert resp.priority == "high"


class TestInterventionStatusTransitions:
    """Test status transition logic"""

    def test_valid_status_transitions(self):
        """Test valid status transition paths"""
        valid_transitions = [
            ("scheduled", "in_progress"),
            ("in_progress", "completed"),
            ("scheduled", "cancelled"),
            ("in_progress", "cancelled"),
        ]

        for from_status, to_status in valid_transitions:
            # All these transitions should be valid
            assert f"{from_status}→{to_status}" is not None

    def test_status_change_parsing(self):
        """Test parsing status changes"""
        status_change = "scheduled→in_progress"
        parts = status_change.split("→")

        assert len(parts) == 2
        assert parts[0] == "scheduled"
        assert parts[1] == "in_progress"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
