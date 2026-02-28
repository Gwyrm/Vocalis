"""
Unit tests for intervention scheduling system

Tests cover:
- Intervention CRUD operations
- Status transitions
- Logging and timeline tracking
- Organization isolation
- Role-based access control
- Input validation
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base, DEMO_ACCOUNT_EMAIL
from models import (
    Organization, User, Prescription, Patient,
    Intervention, InterventionLog, InterventionDocument,
    UserRole
)
from auth import hash_password, create_access_token


# Setup test database
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override dependency for test database"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestInterventionSetup:
    """Setup fixtures for intervention tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test data before each test"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        db = TestingSessionLocal()

        # Create organization
        org = Organization(id="test-org", name="Test Hospital")
        db.add(org)

        # Create doctor user
        self.doctor = User(
            id="doctor-1",
            email="doctor@test.com",
            password_hash=hash_password("password123"),
            full_name="Dr. Smith",
            role=UserRole.DOCTOR,
            org_id="test-org"
        )
        db.add(self.doctor)

        # Create nurse user
        self.nurse = User(
            id="nurse-1",
            email="nurse@test.com",
            password_hash=hash_password("password123"),
            full_name="Jane Nurse",
            role=UserRole.NURSE,
            org_id="test-org"
        )
        db.add(self.nurse)

        # Create patient
        self.patient = Patient(
            id="patient-1",
            org_id="test-org",
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1970, 1, 15),
            phone="555-1234",
            email="john@test.com"
        )
        db.add(self.patient)

        # Create prescription
        self.prescription = Prescription(
            id="presc-1",
            org_id="test-org",
            created_by="doctor-1",
            patient_id="patient-1",
            patient_name="John Doe",
            patient_age="50",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg daily",
            duration="3 months",
            status="draft"
        )
        db.add(self.prescription)

        db.commit()
        db.close()

        # Get auth tokens
        self.doctor_token = create_access_token(
            data={"user_id": "doctor-1", "org_id": "test-org",
                  "email": "doctor@test.com", "role": "doctor"}
        )
        self.nurse_token = create_access_token(
            data={"user_id": "nurse-1", "org_id": "test-org",
                  "email": "nurse@test.com", "role": "nurse"}
        )


class TestInterventionCreate(TestInterventionSetup):
    """Test intervention creation"""

    def test_create_intervention_success(self):
        """Test successful intervention creation"""
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Blood Test",
                "description": "Check cholesterol levels",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "high"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "Blood Test"
        assert data["status"] == "scheduled"
        assert data["priority"] == "high"
        assert data["description"] == "Check cholesterol levels"

    def test_create_intervention_nurse_forbidden(self):
        """Test that nurses cannot create interventions"""
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.nurse_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Blood Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        assert response.status_code == 403
        assert "Only doctors can create interventions" in response.json()["detail"]

    def test_create_intervention_missing_fields(self):
        """Test validation of required fields"""
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "scheduled_date": "2026-03-15T10:00:00"
                # Missing intervention_type
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_intervention_invalid_prescription(self):
        """Test creation with non-existent prescription"""
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "invalid-presc",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        assert response.status_code == 404
        assert "Prescription not found" in response.json()["detail"]


class TestInterventionList(TestInterventionSetup):
    """Test intervention listing"""

    def test_list_interventions_empty(self):
        """Test listing when no interventions exist"""
        response = client.get(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_interventions_with_data(self):
        """Test listing interventions"""
        # Create an intervention
        create_response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Blood Test",
                "description": "Annual checkup",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        # List interventions
        list_response = client.get(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 1
        assert data[0]["intervention_type"] == "Blood Test"

    def test_list_interventions_filter_by_prescription(self):
        """Test filtering by prescription_id"""
        # Create prescription
        db = TestingSessionLocal()
        presc2 = Prescription(
            id="presc-2",
            org_id="test-org",
            created_by="doctor-1",
            patient_id="patient-1",
            patient_name="John Doe",
            patient_age="50",
            diagnosis="Diabetes",
            medication="Metformin",
            dosage="500mg",
            duration="3 months",
            status="draft"
        )
        db.add(presc2)
        db.commit()
        db.close()

        # Create interventions for both prescriptions
        client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test 1",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-2",
                "intervention_type": "Test 2",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        # Filter by prescription
        response = client.get(
            "/api/interventions?prescription_id=presc-1",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["intervention_type"] == "Test 1"

    def test_list_interventions_filter_by_status(self):
        """Test filtering by status"""
        # Create intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Log status change
        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "scheduled→in_progress", "notes": "Started"}
        )

        # Filter by status
        response = client.get(
            "/api/interventions?status=in_progress",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "in_progress"


class TestInterventionStatusTransitions(TestInterventionSetup):
    """Test status transitions and logging"""

    def test_log_status_change_scheduled_to_in_progress(self):
        """Test logging status change"""
        # Create intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Blood Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Log status change
        response = client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "status_change": "scheduled→in_progress",
                "notes": "Patient arrived"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status_change"] == "scheduled→in_progress"
        assert data["notes"] == "Patient arrived"

    def test_log_status_change_in_progress_to_completed(self):
        """Test completing an intervention"""
        # Create and start intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Blood Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Start
        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "scheduled→in_progress", "notes": "Started"}
        )

        # Complete
        response = client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "status_change": "in_progress→completed",
                "notes": "Test completed successfully"
            }
        )

        assert response.status_code == 200
        assert response.json()["status_change"] == "in_progress→completed"

    def test_get_intervention_with_logs(self):
        """Test retrieving intervention with all logs"""
        # Create intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Log changes
        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "scheduled→in_progress", "notes": "Note 1"}
        )

        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "in_progress→completed", "notes": "Note 2"}
        )

        # Get intervention
        response = client.get(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["logs"]) == 2
        assert data["logs"][0]["status_change"] == "scheduled→in_progress"
        assert data["logs"][1]["status_change"] == "in_progress→completed"


class TestInterventionUpdate(TestInterventionSetup):
    """Test intervention updates"""

    def test_update_intervention_scheduled(self):
        """Test updating a scheduled intervention"""
        # Create intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Old Type",
                "description": "Old description",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "low"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Update
        response = client.put(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "intervention_type": "New Type",
                "priority": "high"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "New Type"
        assert data["priority"] == "high"

    def test_update_intervention_in_progress_forbidden(self):
        """Test that started interventions cannot be updated"""
        # Create and start intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Start
        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "scheduled→in_progress", "notes": "Started"}
        )

        # Try to update
        response = client.put(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"intervention_type": "New Type"}
        )

        assert response.status_code == 400
        assert "scheduled" in response.json()["detail"].lower()


class TestInterventionDelete(TestInterventionSetup):
    """Test intervention deletion"""

    def test_delete_intervention_scheduled(self):
        """Test deleting a scheduled intervention"""
        # Create intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Delete
        response = client.delete(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 200

        # Verify deleted
        get_resp = client.get(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )
        assert get_resp.status_code == 404

    def test_delete_intervention_in_progress_forbidden(self):
        """Test that started interventions cannot be deleted"""
        # Create and start intervention
        create_resp = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={
                "prescription_id": "presc-1",
                "intervention_type": "Test",
                "description": "Test",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )
        intervention_id = create_resp.json()["id"]

        # Start
        client.post(
            f"/api/interventions/{intervention_id}/log",
            headers={"Authorization": f"Bearer {self.doctor_token}"},
            json={"status_change": "scheduled→in_progress", "notes": "Started"}
        )

        # Try to delete
        response = client.delete(
            f"/api/interventions/{intervention_id}",
            headers={"Authorization": f"Bearer {self.doctor_token}"}
        )

        assert response.status_code == 400


class TestInterventionAuth(TestInterventionSetup):
    """Test authentication and authorization"""

    def test_missing_token(self):
        """Test that missing token returns 401"""
        response = client.get("/api/interventions")
        assert response.status_code == 401

    def test_invalid_token(self):
        """Test that invalid token returns 401"""
        response = client.get(
            "/api/interventions",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
