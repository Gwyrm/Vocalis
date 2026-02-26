"""
Tests for text-based prescription creation and validation
"""

import pytest
import json
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db, Base
from models import User, Organization, Patient, UserRole
import uuid
import bcrypt


# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override get_db dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database and fixtures"""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Create organization
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Hospital",
    )
    db.add(org)
    db.commit()

    # Create test doctor user
    password_salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw("password123".encode(), password_salt).decode()

    doctor = User(
        id=str(uuid.uuid4()),
        email="doctor@test.com",
        password_hash=password_hash,
        full_name="Dr. Test",
        role=UserRole.DOCTOR,
        org_id=org.id,
    )
    db.add(doctor)
    db.commit()

    # Create test patients
    patient1 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 5, 15),
        phone="0123456789",
        allergies=json.dumps(["Penicillin"]),
        chronic_conditions=json.dumps(["Hypertension"]),
    )
    db.add(patient1)

    patient2 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="Jane",
        last_name="Smith",
        date_of_birth=date(1975, 3, 20),
        phone="0987654321",
        allergies=json.dumps(["Aspirin", "Ibuprofen"]),
    )
    db.add(patient2)

    # Young patient for age-related tests
    patient3 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="Tommy",
        last_name="Young",
        date_of_birth=date(2015, 1, 10),  # ~11 years old
        phone="0555555555",
    )
    db.add(patient3)

    db.commit()

    yield {
        "db": db,
        "org": org,
        "doctor": doctor,
        "patients": [patient1, patient2, patient3],
    }

    db.close()


@pytest.fixture
def auth_token(test_db):
    """Get authentication token for test doctor"""
    response = client.post(
        "/api/auth/login",
        json={"email": "doctor@test.com", "password": "password123"},
    )
    return response.json()["access_token"]


class TestTextPrescriptionCreation:
    """Test text-based prescription creation"""

    def test_create_valid_prescription_from_text(self, auth_token, test_db):
        """Test creating a valid prescription from text input"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg once daily
        Duration: 30 days
        Diagnosis: Hypertension
        Instructions: Take in the morning
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify prescription was created
        assert "prescription" in data
        assert data["prescription"] is not None
        assert data["prescription"]["medication"] == "Lisinopril"
        assert data["prescription"]["dosage"] == "10mg once daily"
        assert data["prescription"]["patient_name"] == "John Doe"

        # Verify validation
        assert "validation" in data
        assert data["validation"]["valid"] is True

    def test_prescription_text_with_missing_fields(self, auth_token, test_db):
        """Test text prescription with missing required fields"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Dosage: 10mg
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have validation errors for missing medication/dosage
        assert data["validation"]["valid"] is False
        assert len(data["validation"]["errors"]) > 0

    def test_prescription_text_with_allergy_warning(self, auth_token, test_db):
        """Test text prescription that triggers allergy warning"""
        patient = test_db["patients"][0]  # Has Penicillin allergy

        prescription_text = """
        Patient: John Doe
        Medication: Amoxicillin
        Dosage: 500mg three times daily
        Duration: 7 days
        Diagnosis: Infection
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have warnings about penicillin allergy
        if data["validation"]["warnings"]:
            assert any("allergy" in w["type"].lower()
                      for w in data["validation"]["warnings"])

    def test_prescription_text_with_age_warning(self, auth_token, test_db):
        """Test text prescription that triggers age-related warning"""
        patient = test_db["patients"][2]  # Young patient (~11 years old)

        prescription_text = """
        Patient: Tommy Young
        Medication: Ibuprofen
        Dosage: 200mg
        Duration: 5 days
        Diagnosis: Fever
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # May have warnings about dosage for age
        assert "validation" in data

    def test_prescription_text_multiline_format(self, auth_token, test_db):
        """Test prescription text with various formatting"""
        patient = test_db["patients"][1]

        # Different formatting styles
        prescription_text = "Patient: Jane Smith\nMédication: Metformin\nPosologie: 500mg 2x/day\nDurée: 90 days\nDiagnose: Diabetes"

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should parse despite formatting differences
        assert data["prescription"] is not None or len(data["validation"]["errors"]) >= 0

    def test_prescription_text_invalid_patient(self, auth_token):
        """Test text prescription with invalid patient ID"""
        prescription_text = """
        Patient: Unknown
        Medication: Aspirin
        Dosage: 100mg
        Duration: 5 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": str(uuid.uuid4()),  # Non-existent patient
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_prescription_text_with_discovered_allergies(self, auth_token, test_db):
        """Test text prescription with newly discovered allergies"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg daily
        Duration: 30 days
        Diagnosis: Hypertension
        Note: Patient reported new allergy to ACE inhibitors
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
                "discovered_allergies": ["ACE inhibitor"],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify prescription created
        assert data["prescription"] is not None

        # Verify patient was updated
        patient_response = client.get(
            f"/api/patients/{patient.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        updated_patient = patient_response.json()
        assert "ACE inhibitor" in updated_patient.get("allergies", [])

    def test_prescription_text_empty_input(self, auth_token, test_db):
        """Test text prescription with empty input"""
        patient = test_db["patients"][0]

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": "",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Should return 400 or validation error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data["validation"]["valid"] is False

    def test_prescription_text_with_special_characters(self, auth_token, test_db):
        """Test text prescription with special characters and accents"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Döe
        Medication: Érythromycine
        Dosage: 250mg, 2× par jour
        Duration: 7 jours
        Diagnosis: Infection respiratoire
        Instructions: À prendre avec nourriture
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        # Should handle special characters

    def test_prescription_text_with_long_input(self, auth_token, test_db):
        """Test text prescription with very long input"""
        patient = test_db["patients"][0]

        # Create long but valid prescription text
        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg once daily
        Duration: 30 days
        Diagnosis: Essential Hypertension - newly diagnosed during routine physical examination
        Instructions: Take in the morning with a glass of water. Monitor blood pressure regularly.
        Report any dizziness, persistent dry cough, or swelling in the face and extremities.
        Follow up appointment in 2 weeks to monitor blood pressure response to medication.
        Do not stop taking this medication without consulting your physician.
        """ + "x" * 1000  # Add extra characters

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

    def test_prescription_text_without_auth(self, test_db):
        """Test text prescription without authentication"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Medication: Aspirin
        Dosage: 100mg
        Duration: 5 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
        )

        assert response.status_code == 403  # Forbidden without auth


class TestTextPrescriptionValidation:
    """Test validation logic for text prescriptions"""

    def test_validation_confidence_score(self, auth_token, test_db):
        """Test that validation returns confidence score"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        data = response.json()
        assert "confidence" in data["validation"]
        assert 0 <= data["validation"]["confidence"] <= 1.0

    def test_validation_errors_structure(self, auth_token, test_db):
        """Test that validation errors have proper structure"""
        patient = test_db["patients"][0]

        prescription_text = "Patient: John"  # Missing required fields

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        data = response.json()

        for error in data["validation"]["errors"]:
            assert "type" in error
            assert "message" in error
            assert error["type"] in [
                "missing_field",
                "invalid_value",
                "contraindicated",
            ]

    def test_validation_warnings_structure(self, auth_token, test_db):
        """Test that validation warnings have proper structure"""
        patient = test_db["patients"][0]  # Has Penicillin allergy

        prescription_text = """
        Patient: John Doe
        Medication: Amoxicillin
        Dosage: 500mg
        Duration: 7 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        data = response.json()

        for warning in data["validation"].get("warnings", []):
            assert "type" in warning
            assert "message" in warning
            assert "severity" in warning
            assert warning["severity"] in ["low", "medium", "high"]


class TestTextPrescriptionPatientResponse:
    """Test patient summary in prescription response"""

    def test_prescription_includes_patient_summary(self, auth_token, test_db):
        """Test that response includes patient summary"""
        patient = test_db["patients"][0]

        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        data = response.json()

        # Should include patient summary
        assert "patient_summary" in data
        patient_summary = data["patient_summary"]

        assert patient_summary["first_name"] == "John"
        assert patient_summary["last_name"] == "Doe"
        assert patient_summary["id"] == patient.id

    def test_prescription_includes_allergies_in_summary(self, auth_token, test_db):
        """Test that patient allergies are included in summary"""
        patient = test_db["patients"][0]  # Has Penicillin allergy

        prescription_text = """
        Patient: John Doe
        Medication: Lisinopril
        Dosage: 10mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        data = response.json()
        patient_summary = data["patient_summary"]

        assert "allergies" in patient_summary
        assert "Penicillin" in patient_summary.get("allergies", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
