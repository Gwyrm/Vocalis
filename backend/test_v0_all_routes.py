"""
Comprehensive Route Testing for Vocalis V0
Tests all major API endpoints with proper test isolation
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app

client = TestClient(app)


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthenticationRoutes:
    """Test all authentication endpoints"""
    
    def test_1_register(self):
        """POST /api/auth/register"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:8]}@test.com",
                "password": "TestPassword123",
                "full_name": "Test User",
                "role": "doctor"
            }
        )
        assert response.status_code in [200, 201]
        assert "access_token" in response.json()
    
    def test_2_login(self):
        """POST /api/auth/login"""
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "Login Test",
                "role": "doctor"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "TestPassword123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_3_health_check(self):
        """GET /api/health"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_4_root(self):
        """GET /"""
        response = client.get("/")
        assert response.status_code == 200


# ============================================================================
# PATIENT ROUTES TEST
# ============================================================================

class TestPatientRoutes:
    """Test patient management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        email = f"patient_doc_{uuid.uuid4().hex[:8]}@test.com"
        reg = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "Patient Doctor",
                "role": "doctor"
            }
        )
        self.token = reg.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_1_create_patient(self):
        """POST /api/patients"""
        response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "allergies": ["Penicillin"],
            }
        )
        assert response.status_code == 200
        self.patient_id = response.json()["id"]
    
    def test_2_list_patients(self):
        """GET /api/patients"""
        response = client.get("/api/patients", headers=self.headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_3_get_patient(self):
        """GET /api/patients/{id}"""
        # Create a patient first
        create_resp = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1985-05-20",
            }
        )
        patient_id = create_resp.json()["id"]
        
        # Get patient
        response = client.get(f"/api/patients/{patient_id}", headers=self.headers)
        assert response.status_code == 200
        assert response.json()["id"] == patient_id
    
    def test_4_update_patient(self):
        """PUT /api/patients/{id}"""
        # Create
        create_resp = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Bob",
                "last_name": "Johnson",
                "date_of_birth": "1992-07-10",
            }
        )
        patient_id = create_resp.json()["id"]
        
        # Update
        response = client.put(
            f"/api/patients/{patient_id}",
            headers=self.headers,
            json={"phone": "555-1234"}
        )
        assert response.status_code == 200
    
    def test_5_delete_patient(self):
        """DELETE /api/patients/{id}"""
        # Create
        create_resp = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Charlie",
                "last_name": "Brown",
                "date_of_birth": "1995-03-15",
            }
        )
        patient_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/patients/{patient_id}", headers=self.headers)
        assert response.status_code == 200


# ============================================================================
# PRESCRIPTION ROUTES TEST
# ============================================================================

class TestPrescriptionRoutes:
    """Test prescription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user and patient"""
        email = f"rx_doc_{uuid.uuid4().hex[:8]}@test.com"
        reg = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "RX Doctor",
                "role": "doctor"
            }
        )
        self.token = reg.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create patient
        patient_resp = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Patient",
                "last_name": "ForRX",
                "date_of_birth": "1990-01-01",
            }
        )
        self.patient_id = patient_resp.json()["id"]
    
    def test_1_create_prescription(self):
        """POST /api/prescriptions"""
        response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRX",
                "patient_age": "34",
                "diagnosis": "Type 2 Diabetes",
                "medication": "Metformin",
                "dosage": "500mg",
                "duration": "30 days",
            }
        )
        assert response.status_code == 200
        self.rx_id = response.json()["id"]
    
    def test_2_list_prescriptions(self):
        """GET /api/prescriptions"""
        response = client.get("/api/prescriptions", headers=self.headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_3_get_prescription(self):
        """GET /api/prescriptions/{id}"""
        # Create
        create_resp = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRX",
                "patient_age": "34",
                "diagnosis": "Hypertension",
                "medication": "Lisinopril",
                "dosage": "10mg",
                "duration": "60 days",
            }
        )
        rx_id = create_resp.json()["id"]
        
        # Get
        response = client.get(f"/api/prescriptions/{rx_id}", headers=self.headers)
        assert response.status_code == 200
    
    def test_4_update_prescription(self):
        """PUT /api/prescriptions/{id}"""
        # Create
        create_resp = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRX",
                "patient_age": "34",
                "diagnosis": "Original",
                "medication": "OrigMed",
                "dosage": "100mg",
                "duration": "30 days",
            }
        )
        rx_id = create_resp.json()["id"]
        
        # Update
        response = client.put(
            f"/api/prescriptions/{rx_id}",
            headers=self.headers,
            json={"medication": "UpdatedMed"}
        )
        assert response.status_code == 200
    
    def test_5_sign_prescription(self):
        """PUT /api/prescriptions/{id}/sign"""
        # Create
        create_resp = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRX",
                "patient_age": "34",
                "diagnosis": "ToSign",
                "medication": "SignMe",
                "dosage": "50mg",
                "duration": "30 days",
            }
        )
        rx_id = create_resp.json()["id"]
        
        # Sign
        response = client.put(
            f"/api/prescriptions/{rx_id}/sign",
            headers=self.headers,
            json={
                "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )
        assert response.status_code == 200
    
    def test_6_get_patient_prescriptions(self):
        """GET /api/patients/{id}/prescriptions"""
        response = client.get(
            f"/api/patients/{self.patient_id}/prescriptions",
            headers=self.headers
        )
        assert response.status_code == 200


# ============================================================================
# INTERVENTION ROUTES TEST
# ============================================================================

class TestInterventionRoutes:
    """Test intervention endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user, patient, and prescription"""
        email = f"int_doc_{uuid.uuid4().hex[:8]}@test.com"
        reg = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "INT Doctor",
                "role": "doctor"
            }
        )
        self.token = reg.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create patient
        patient_resp = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Patient",
                "last_name": "ForINT",
                "date_of_birth": "1990-01-01",
            }
        )
        self.patient_id = patient_resp.json()["id"]
        
        # Create prescription
        rx_resp = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForINT",
                "patient_age": "34",
                "diagnosis": "Test",
                "medication": "TestMed",
                "dosage": "100mg",
                "duration": "30 days",
            }
        )
        self.rx_id = rx_resp.json()["id"]
    
    def test_1_create_intervention(self):
        """POST /api/interventions"""
        response = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Blood test",
                "description": "Routine blood work",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        assert response.status_code == 200
    
    def test_2_list_interventions(self):
        """GET /api/interventions"""
        response = client.get("/api/interventions", headers=self.headers)
        assert response.status_code == 200
    
    def test_3_get_intervention(self):
        """GET /api/interventions/{id}"""
        # Create
        create_resp = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Follow-up",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        int_id = create_resp.json()["id"]
        
        # Get
        response = client.get(f"/api/interventions/{int_id}", headers=self.headers)
        assert response.status_code == 200
    
    def test_4_update_intervention(self):
        """PUT /api/interventions/{id}"""
        # Create
        create_resp = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Original",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "low",
            }
        )
        int_id = create_resp.json()["id"]
        
        # Update
        response = client.put(
            f"/api/interventions/{int_id}",
            headers=self.headers,
            json={"priority": "high"}
        )
        assert response.status_code == 200
    
    def test_5_log_intervention(self):
        """POST /api/interventions/{id}/log"""
        # Create
        create_resp = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "ToLog",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        int_id = create_resp.json()["id"]
        
        # Log
        response = client.post(
            f"/api/interventions/{int_id}/log",
            headers=self.headers,
            json={
                "status_change": "scheduled→in_progress",
                "notes": "Started intervention",
            }
        )
        assert response.status_code == 200
    
    def test_6_delete_intervention(self):
        """DELETE /api/interventions/{id}"""
        # Create
        create_resp = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "ToDelete",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        int_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(
            f"/api/interventions/{int_id}",
            headers=self.headers
        )
        assert response.status_code == 200


# ============================================================================
# DEVICE ROUTES TEST
# ============================================================================

class TestDeviceRoutes:
    """Test device management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        email = f"device_doc_{uuid.uuid4().hex[:8]}@test.com"
        reg = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "Device Doctor",
                "role": "doctor"
            }
        )
        self.token = reg.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_1_create_device(self):
        """POST /api/devices"""
        response = client.post(
            "/api/devices",
            headers=self.headers,
            json={
                "name": "Glucometer",
                "model": "GM100",
                "serial_number": f"SN{uuid.uuid4().hex[:8]}",
                "description": "Blood glucose monitor",
            }
        )
        assert response.status_code == 200
    
    def test_2_list_devices(self):
        """GET /api/devices"""
        response = client.get("/api/devices", headers=self.headers)
        assert response.status_code == 200
    
    def test_3_update_device(self):
        """PATCH /api/devices/{id}"""
        # Create
        create_resp = client.post(
            "/api/devices",
            headers=self.headers,
            json={
                "name": "Device",
                "model": "M1",
                "serial_number": f"SN{uuid.uuid4().hex[:8]}",
            }
        )
        device_id = create_resp.json()["id"]
        
        # Update
        response = client.patch(
            f"/api/devices/{device_id}",
            headers=self.headers,
            json={"status": "maintenance"}
        )
        assert response.status_code == 200


# ============================================================================
# ANALYTICS ROUTES TEST
# ============================================================================

class TestAnalyticsRoutes:
    """Test analytics endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        email = f"analytics_doc_{uuid.uuid4().hex[:8]}@test.com"
        reg = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123",
                "full_name": "Analytics Doctor",
                "role": "doctor"
            }
        )
        self.token = reg.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_1_visit_analytics(self):
        """GET /api/analytics/visits"""
        response = client.get("/api/analytics/visits", headers=self.headers)
        assert response.status_code == 200
    
    def test_2_device_analytics(self):
        """GET /api/analytics/devices"""
        response = client.get("/api/analytics/devices", headers=self.headers)
        assert response.status_code == 200
    
    def test_3_nurse_analytics(self):
        """GET /api/analytics/nurses"""
        response = client.get("/api/analytics/nurses", headers=self.headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
