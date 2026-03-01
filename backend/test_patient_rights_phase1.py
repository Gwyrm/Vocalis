"""
Test cases for Phase 1 Patient Rights Implementation
Verifies role-based access control, audit logging, and soft deletes
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
import uuid

# These tests assume the FastAPI app is running on localhost:8080
BASE_URL = "http://localhost:8080"

# Test accounts
DOCTOR_EMAIL = "doctor@test.fr"
DOCTOR_PASSWORD = "SecurePass123!"
NURSE_EMAIL = "nurse@test.fr"
NURSE_PASSWORD = "SecurePass456!"
PATIENT_DATA = {
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_of_birth": "1980-01-15",
    "gender": "M",
    "phone": "+33612345678",
    "email": "patient@test.fr",
    "address": "123 Rue de Paris, 75001",
    "allergies": ["Penicillin"],
    "chronic_conditions": ["Diabetes"],
    "current_medications": ["Metformin"],
    "medical_notes": "Type 2 Diabetes, controlled"
}


class TestPatientRolesPhase1:
    """Test Phase 1: Role enforcement and audit logging"""

    @pytest.fixture(scope="class")
    def setup_users(self):
        """Create test users and get tokens"""
        import requests

        # Register doctor
        doctor_resp = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": DOCTOR_EMAIL,
                "password": DOCTOR_PASSWORD,
                "full_name": "Dr. Test",
                "role": "doctor"
            }
        )
        doctor_token = doctor_resp.json()["access_token"]

        # Register nurse
        nurse_resp = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": NURSE_EMAIL,
                "password": NURSE_PASSWORD,
                "full_name": "Nurse Test",
                "role": "nurse"
            }
        )
        nurse_token = nurse_resp.json()["access_token"]

        return {
            "doctor_token": doctor_token,
            "nurse_token": nurse_token,
            "doctor_email": DOCTOR_EMAIL,
            "nurse_email": NURSE_EMAIL
        }

    def test_01_doctor_can_create_patient(self, setup_users):
        """✅ PASS: Doctor can create patient"""
        import requests

        response = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        patient = response.json()
        assert patient["first_name"] == "Jean"
        return patient["id"]

    def test_02_nurse_cannot_create_patient(self, setup_users):
        """✅ PASS: Nurse cannot create patient (403 Forbidden)"""
        import requests

        response = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['nurse_token']}"},
            json=PATIENT_DATA
        )

        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        assert "Doctor role required" in response.text

    def test_03_access_logging_on_create(self, setup_users):
        """✅ PASS: Access logged when patient created"""
        import requests
        from database import SessionLocal
        from models import PatientAccessLog

        # Create patient
        response = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = response.json()["id"]

        # Check access log
        db = SessionLocal()
        log = db.query(PatientAccessLog).filter(
            PatientAccessLog.patient_id == patient_id,
            PatientAccessLog.action == "create"
        ).first()

        assert log is not None, "Access log not found"
        assert log.action == "create"
        db.close()

    def test_04_creator_tracked(self, setup_users):
        """✅ PASS: Patient created_by field tracks creator"""
        import requests
        from database import SessionLocal
        from models import Patient

        # Create patient
        response = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = response.json()["id"]

        # Check database
        db = SessionLocal()
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        assert patient.created_by is not None, "created_by is None"
        assert patient.created_by_user.email == DOCTOR_EMAIL
        db.close()

    def test_05_doctor_can_update_patient(self, setup_users):
        """✅ PASS: Doctor can update patient"""
        import requests

        # Create patient first
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Update patient
        update_resp = requests.put(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json={"phone": "+33698765432"}
        )

        assert update_resp.status_code == 200
        assert update_resp.json()["phone"] == "+33698765432"

    def test_06_nurse_cannot_update_patient(self, setup_users):
        """✅ PASS: Nurse cannot update patient (403 Forbidden)"""
        import requests

        # Create patient as doctor
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Try to update as nurse
        update_resp = requests.put(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['nurse_token']}"},
            json={"phone": "+33698765432"}
        )

        assert update_resp.status_code == 403
        assert "Doctor role required" in update_resp.text

    def test_07_updater_tracked(self, setup_users):
        """✅ PASS: Patient updated_by field tracks updater"""
        import requests
        from database import SessionLocal
        from models import Patient

        # Create and update patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        requests.put(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json={"phone": "+33698765432"}
        )

        # Check database
        db = SessionLocal()
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        assert patient.updated_by is not None
        assert patient.updated_by_user.email == DOCTOR_EMAIL
        db.close()

    def test_08_doctor_can_delete_patient(self, setup_users):
        """✅ PASS: Doctor can delete patient (soft delete)"""
        import requests

        # Create patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Delete patient
        delete_resp = requests.delete(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        assert delete_resp.status_code == 200

    def test_09_nurse_cannot_delete_patient(self, setup_users):
        """✅ PASS: Nurse cannot delete patient (403 Forbidden)"""
        import requests

        # Create patient as doctor
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Try to delete as nurse
        delete_resp = requests.delete(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['nurse_token']}"}
        )

        assert delete_resp.status_code == 403
        assert "Doctor role required" in delete_resp.text

    def test_10_soft_delete_preserves_data(self, setup_users):
        """✅ PASS: Soft delete preserves data in database"""
        import requests
        from database import SessionLocal
        from models import Patient

        # Create and delete patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        requests.delete(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        # Check database - data should still exist but marked deleted
        db = SessionLocal()
        patient = db.query(Patient).filter(Patient.id == patient_id).first()

        assert patient is not None, "Patient was hard-deleted (should be soft-deleted)"
        assert patient.deleted_at is not None, "deleted_at should be set"
        assert patient.deleted_by is not None, "deleted_by should be set"
        db.close()

    def test_11_deleted_patient_not_in_list(self, setup_users):
        """✅ PASS: Deleted patients excluded from list"""
        import requests

        # Create and delete patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        requests.delete(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        # List patients
        list_resp = requests.get(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        patient_ids = [p["id"] for p in list_resp.json()]
        assert patient_id not in patient_ids, "Deleted patient appeared in list"

    def test_12_access_log_on_read(self, setup_users):
        """✅ PASS: Read access logged"""
        import requests
        from database import SessionLocal
        from models import PatientAccessLog

        # Create patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Read patient
        requests.get(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        # Check access log
        db = SessionLocal()
        log = db.query(PatientAccessLog).filter(
            PatientAccessLog.patient_id == patient_id,
            PatientAccessLog.action == "read"
        ).first()

        assert log is not None, "Read access not logged"
        db.close()

    def test_13_access_log_on_delete(self, setup_users):
        """✅ PASS: Delete access logged"""
        import requests
        from database import SessionLocal
        from models import PatientAccessLog

        # Create patient
        create_resp = requests.post(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"},
            json=PATIENT_DATA
        )
        patient_id = create_resp.json()["id"]

        # Delete patient
        requests.delete(
            f"{BASE_URL}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {setup_users['doctor_token']}"}
        )

        # Check access log
        db = SessionLocal()
        log = db.query(PatientAccessLog).filter(
            PatientAccessLog.patient_id == patient_id,
            PatientAccessLog.action == "delete"
        ).first()

        assert log is not None, "Delete access not logged"
        db.close()


if __name__ == "__main__":
    # Run with: pytest test_patient_rights_phase1.py -v
    print("Run tests with: pytest test_patient_rights_phase1.py -v")
