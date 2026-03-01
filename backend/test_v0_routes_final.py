"""
Final Comprehensive Route Testing for Vocalis V0
Tests all major API endpoints with proper rate limit handling
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from main import app

client = TestClient(app)

# ============================================================================
# GLOBAL SETUP - Create single test user to avoid rate limiting
# ============================================================================

TEST_EMAIL = "comprehensive_test_user@vocalis.test"
TEST_PASSWORD = "TestPassword123"

def setup_module():
    """Setup test user once for all tests"""
    global TEST_TOKEN, PATIENT_ID, RX_ID, INT_ID, DEVICE_ID
    
    # Register user
    response = client.post(
        "/api/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Comprehensive Test",
            "role": "doctor"
        }
    )
    
    if response.status_code in [200, 201]:
        TEST_TOKEN = response.json()["access_token"]
    else:
        # Try login if already registered
        response = client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        TEST_TOKEN = response.json()["access_token"]


# ============================================================================
# ROUTE TESTS - All using same authenticated user
# ============================================================================

class TestAllRoutes:
    """Comprehensive test of all major API routes"""
    
    def test_01_health_check(self):
        """GET /api/health"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()
        print("✅ Health check")
    
    def test_02_root(self):
        """GET /"""
        response = client.get("/")
        assert response.status_code == 200
        print("✅ Root endpoint")
    
    def test_03_get_current_user(self):
        """GET /api/auth/me"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Get current user")
    
    def test_04_create_patient(self):
        """POST /api/patients"""
        global PATIENT_ID
        response = client.post(
            "/api/patients",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-15",
                "allergies": ["Penicillin"],
            }
        )
        assert response.status_code == 200
        PATIENT_ID = response.json()["id"]
        print("✅ Create patient")
    
    def test_05_list_patients(self):
        """GET /api/patients"""
        response = client.get(
            "/api/patients",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✅ List patients")
    
    def test_06_get_patient(self):
        """GET /api/patients/{id}"""
        response = client.get(
            f"/api/patients/{PATIENT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Get patient by ID")
    
    def test_07_update_patient(self):
        """PUT /api/patients/{id}"""
        response = client.put(
            f"/api/patients/{PATIENT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={"phone": "555-1234"}
        )
        assert response.status_code == 200
        print("✅ Update patient")
    
    def test_08_create_prescription(self):
        """POST /api/prescriptions"""
        global RX_ID
        response = client.post(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "patient_id": PATIENT_ID,
                "patient_name": "Test Patient",
                "patient_age": "34",
                "diagnosis": "Type 2 Diabetes",
                "medication": "Metformin",
                "dosage": "500mg",
                "duration": "30 days",
            }
        )
        assert response.status_code == 200
        RX_ID = response.json()["id"]
        print("✅ Create prescription")
    
    def test_09_list_prescriptions(self):
        """GET /api/prescriptions"""
        response = client.get(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ List prescriptions")
    
    def test_10_get_prescription(self):
        """GET /api/prescriptions/{id}"""
        response = client.get(
            f"/api/prescriptions/{RX_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Get prescription")
    
    def test_11_update_prescription(self):
        """PUT /api/prescriptions/{id}"""
        response = client.put(
            f"/api/prescriptions/{RX_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={"medication": "Glipizide"}
        )
        assert response.status_code == 200
        print("✅ Update prescription")
    
    def test_12_sign_prescription(self):
        """PUT /api/prescriptions/{id}/sign"""
        response = client.put(
            f"/api/prescriptions/{RX_ID}/sign",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )
        assert response.status_code == 200
        print("✅ Sign prescription")
    
    def test_13_get_patient_prescriptions(self):
        """GET /api/patients/{id}/prescriptions"""
        response = client.get(
            f"/api/patients/{PATIENT_ID}/prescriptions",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Get patient prescriptions")
    
    def test_14_create_intervention(self):
        """POST /api/interventions"""
        global INT_ID
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "prescription_id": RX_ID,
                "intervention_type": "Blood test",
                "description": "Routine blood work",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        assert response.status_code == 200
        INT_ID = response.json()["id"]
        print("✅ Create intervention")
    
    def test_15_list_interventions(self):
        """GET /api/interventions"""
        response = client.get(
            "/api/interventions",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ List interventions")
    
    def test_16_get_intervention(self):
        """GET /api/interventions/{id}"""
        response = client.get(
            f"/api/interventions/{INT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Get intervention")
    
    def test_17_update_intervention(self):
        """PUT /api/interventions/{id}"""
        response = client.put(
            f"/api/interventions/{INT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={"priority": "high"}
        )
        assert response.status_code == 200
        print("✅ Update intervention")
    
    def test_18_log_intervention(self):
        """POST /api/interventions/{id}/log"""
        response = client.post(
            f"/api/interventions/{INT_ID}/log",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "status_change": "scheduled→in_progress",
                "notes": "Started intervention",
            }
        )
        assert response.status_code == 200
        print("✅ Log intervention")
    
    def test_19_create_device(self):
        """POST /api/devices"""
        global DEVICE_ID
        response = client.post(
            "/api/devices",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "name": "Glucometer",
                "model": "GM100",
                "serial_number": "SN123456789",
                "description": "Blood glucose monitor",
            }
        )
        assert response.status_code == 200
        DEVICE_ID = response.json()["id"]
        print("✅ Create device")
    
    def test_20_list_devices(self):
        """GET /api/devices"""
        response = client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ List devices")
    
    def test_21_update_device(self):
        """PATCH /api/devices/{id}"""
        response = client.patch(
            f"/api/devices/{DEVICE_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={"status": "maintenance"}
        )
        assert response.status_code == 200
        print("✅ Update device")
    
    def test_22_visit_analytics(self):
        """GET /api/analytics/visits"""
        response = client.get(
            "/api/analytics/visits",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Visit analytics")
    
    def test_23_device_analytics(self):
        """GET /api/analytics/devices"""
        response = client.get(
            "/api/analytics/devices",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Device analytics")
    
    def test_24_nurse_analytics(self):
        """GET /api/analytics/nurses"""
        response = client.get(
            "/api/analytics/nurses",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Nurse analytics")
    
    def test_25_delete_intervention(self):
        """DELETE /api/interventions/{id}"""
        response = client.delete(
            f"/api/interventions/{INT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Delete intervention")
    
    def test_26_delete_patient(self):
        """DELETE /api/patients/{id}"""
        response = client.delete(
            f"/api/patients/{PATIENT_ID}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200
        print("✅ Delete patient")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
