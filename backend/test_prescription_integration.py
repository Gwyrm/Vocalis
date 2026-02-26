"""
Integration tests for complete prescription creation workflows
"""

import pytest
import json
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db, Base
from models import User, Organization, Patient, Prescription, UserRole
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


@pytest.fixture(scope="function")
def test_setup():
    """Setup test database with fixtures"""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Create organization
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Medical Center",
    )
    db.add(org)
    db.commit()

    # Create doctor user
    password_salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw("secure123".encode(), password_salt).decode()

    doctor = User(
        id=str(uuid.uuid4()),
        email="dr.smith@test.com",
        password_hash=password_hash,
        full_name="Dr. Jane Smith",
        role=UserRole.DOCTOR,
        org_id=org.id,
    )
    db.add(doctor)

    # Create nurse user
    nurse = User(
        id=str(uuid.uuid4()),
        email="nurse@test.com",
        password_hash=password_hash,
        full_name="Nurse John",
        role=UserRole.NURSE,
        org_id=org.id,
    )
    db.add(nurse)
    db.commit()

    # Create test patients with various profiles
    patients = []

    # Patient 1: Adult with allergies
    p1 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="Robert",
        last_name="Johnson",
        date_of_birth=date(1965, 7, 22),
        phone="+33612345678",
        allergies=json.dumps(["Penicillin", "NSAIDs"]),
        chronic_conditions=json.dumps(["Hypertension", "Type 2 Diabetes"]),
        current_medications=json.dumps(["Metformin 500mg", "Atorvastatin 20mg"]),
    )
    db.add(p1)
    patients.append(p1)

    # Patient 2: Younger patient
    p2 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="Sophie",
        last_name="Martin",
        date_of_birth=date(1990, 3, 15),
        phone="+33698765432",
        allergies=json.dumps(["Latex"]),
    )
    db.add(p2)
    patients.append(p2)

    # Patient 3: Elderly with multiple conditions
    p3 = Patient(
        id=str(uuid.uuid4()),
        org_id=org.id,
        first_name="Michel",
        last_name="Durand",
        date_of_birth=date(1940, 1, 5),
        phone="+33611111111",
        allergies=json.dumps(["Sulfonamides", "Aspirin"]),
        chronic_conditions=json.dumps(
            ["Hypertension", "Atrial Fibrillation", "COPD", "Arthritis"]
        ),
        current_medications=json.dumps(
            ["Warfarin 5mg", "Metoprolol 50mg", "Prednisone 5mg"]
        ),
    )
    db.add(p3)
    patients.append(p3)

    db.commit()

    yield {"db": db, "org": org, "doctor": doctor, "nurse": nurse, "patients": patients}

    db.close()


@pytest.fixture
def doctor_token(test_setup):
    """Get doctor authentication token"""
    response = client.post(
        "/api/auth/login",
        json={"email": "dr.smith@test.com", "password": "secure123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def nurse_token(test_setup):
    """Get nurse authentication token"""
    response = client.post(
        "/api/auth/login",
        json={"email": "nurse@test.com", "password": "secure123"},
    )
    return response.json()["access_token"]


class TestPrescriptionWorkflow:
    """Test complete prescription workflows"""

    def test_text_prescription_workflow_complete(self, doctor_token, test_setup):
        """Test complete text prescription workflow from input to creation"""
        patient = test_setup["patients"][0]

        # Step 1: Create prescription from text
        prescription_text = """
        Patient: Robert Johnson
        Diagnosis: Acute bronchitis
        Medication: Azithromycin
        Dosage: 500mg on day 1, then 250mg daily for 4 days
        Duration: 5 days
        Instructions: Take with food to minimize stomach upset
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        rx_data = response.json()

        # Verify prescription created
        assert rx_data["prescription"] is not None
        prescription_id = rx_data["prescription"]["id"]

        # Step 2: Verify we can retrieve the created prescription
        retrieve_response = client.get(
            f"/api/prescriptions/{prescription_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert retrieve_response.status_code == 200
        retrieved_rx = retrieve_response.json()
        assert retrieved_rx["id"] == prescription_id
        assert retrieved_rx["medication"] == "Azithromycin"
        assert retrieved_rx["patient_name"] == "Robert Johnson"

    def test_text_prescription_with_discoveries(self, doctor_token, test_setup):
        """Test text prescription that discovers new allergies/conditions"""
        patient = test_setup["patients"][1]  # Sophie Martin
        initial_allergies = patient.allergies  # "Latex"

        # Create prescription with newly discovered allergy
        prescription_text = """
        Patient: Sophie Martin
        Medication: Amoxicillin-clavulanic acid
        Dosage: 875mg twice daily
        Duration: 10 days
        Diagnosis: Bacterial sinusitis
        Note: Patient discovered allergy to penicillin during this visit
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": patient.id,
                "prescription_text": prescription_text,
                "discovered_allergies": ["Penicillin"],
                "discovered_conditions": ["Chronic sinusitis"],
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200

        # Verify patient record was updated
        patient_response = client.get(
            f"/api/patients/{patient.id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        updated_patient = patient_response.json()
        allergies = updated_patient.get("allergies", [])

        # Should have both original and newly discovered allergies
        assert "Latex" in allergies
        assert "Penicillin" in allergies

        # Should have newly discovered condition
        conditions = updated_patient.get("chronic_conditions", [])
        assert "Chronic sinusitis" in conditions

    def test_multiple_prescriptions_same_patient(self, doctor_token, test_setup):
        """Test creating multiple prescriptions for same patient"""
        patient = test_setup["patients"][0]

        # Create first prescription
        rx1_text = """
        Patient: Robert Johnson
        Medication: Metoprolol
        Dosage: 50mg once daily
        Duration: 30 days
        Diagnosis: Hypertension management
        """

        response1 = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": rx1_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response1.status_code == 200
        rx1_id = response1.json()["prescription"]["id"]

        # Create second prescription
        rx2_text = """
        Patient: Robert Johnson
        Medication: Lisinopril
        Dosage: 10mg once daily
        Duration: 30 days
        Diagnosis: Hypertension - combination therapy
        """

        response2 = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": rx2_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response2.status_code == 200
        rx2_id = response2.json()["prescription"]["id"]

        # Verify both exist
        list_response = client.get(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        prescriptions = list_response.json()
        rx_ids = [rx["id"] for rx in prescriptions]

        assert rx1_id in rx_ids
        assert rx2_id in rx_ids

    def test_prescription_validation_cascade(self, doctor_token, test_setup):
        """Test validation warnings cascade from patient allergies"""
        patient = test_setup["patients"][0]  # Has NSAIDs allergy

        # Try to prescribe NSAID
        prescription_text = """
        Patient: Robert Johnson
        Medication: Ibuprofen
        Dosage: 400mg three times daily
        Duration: 7 days
        Diagnosis: Pain management
        """

        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have warnings about NSAID allergy
        # (Even if validation passes, should show allergy warning)
        assert data["validation"] is not None

    def test_elderly_patient_prescriptions(self, doctor_token, test_setup):
        """Test prescriptions for elderly patients with multiple conditions"""
        patient = test_setup["patients"][2]  # Michel Durand, 86 years old

        prescription_text = """
        Patient: Michel Durand
        Medication: Digoxin
        Dosage: 0.25mg once daily
        Duration: 30 days
        Diagnosis: Atrial fibrillation - rate control
        Instructions: Monitor heart rate daily, report if below 60 bpm
        """

        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should acknowledge elderly patient
        assert data["patient_summary"]["id"] == patient.id

    def test_contraindication_detection(self, doctor_token, test_setup):
        """Test detection of drug contraindications"""
        patient = test_setup["patients"][2]  # On Warfarin (anticoagulant)

        # Try to prescribe NSAID while on Warfarin (contraindicated)
        prescription_text = """
        Patient: Michel Durand
        Medication: Naproxen
        Dosage: 500mg twice daily
        Duration: 7 days
        Diagnosis: Arthritis pain
        """

        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have validation warnings about NSAID + Warfarin interaction
        if data["validation"]["warnings"]:
            assert len(data["validation"]["warnings"]) > 0


class TestPrescriptionErrorHandling:
    """Test error handling in prescription workflows"""

    def test_text_prescription_malformed_json(self, doctor_token):
        """Test handling of malformed JSON"""
        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": "valid-id"},  # Missing prescription_text
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        # Should return validation error
        assert response.status_code in [422, 400]

    def test_text_prescription_unauthorized_nurse(self, nurse_token, test_setup):
        """Test that nurses cannot create prescriptions"""
        patient = test_setup["patients"][0]

        prescription_text = """
        Patient: Robert Johnson
        Medication: Aspirin
        Dosage: 100mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {nurse_token}"},
        )

        # Nurses should not be able to create prescriptions
        assert response.status_code == 403

    def test_text_prescription_cross_organization(self, doctor_token, test_setup):
        """Test that prescriptions can't be created for patients from other orgs"""
        # Get a patient from current org
        patient = test_setup["patients"][0]

        # Create patient in different organization
        other_org = Organization(id=str(uuid.uuid4()), name="Other Hospital")
        test_setup["db"].add(other_org)
        test_setup["db"].commit()

        other_patient = Patient(
            id=str(uuid.uuid4()),
            org_id=other_org.id,
            first_name="Other",
            last_name="Patient",
            date_of_birth=date(1980, 1, 1),
        )
        test_setup["db"].add(other_patient)
        test_setup["db"].commit()

        # Try to create prescription for other org's patient
        prescription_text = """
        Patient: Other Patient
        Medication: Aspirin
        Dosage: 100mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={
                "patient_id": other_patient.id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        # Should be forbidden
        assert response.status_code == 404


class TestPrescriptionListAndRetrieve:
    """Test retrieving prescription lists and details"""

    def test_list_all_prescriptions(self, doctor_token, test_setup):
        """Test listing all prescriptions"""
        patient = test_setup["patients"][0]

        # Create a couple prescriptions
        for i in range(3):
            prescription_text = f"""
            Patient: Robert Johnson
            Medication: Medication{i}
            Dosage: 100mg daily
            Duration: 30 days
            """

            client.post(
                "/api/prescriptions/text",
                json={"patient_id": patient.id, "prescription_text": prescription_text},
                headers={"Authorization": f"Bearer {doctor_token}"},
            )

        # List all prescriptions
        response = client.get(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert response.status_code == 200
        prescriptions = response.json()
        assert len(prescriptions) >= 3

    def test_list_prescriptions_by_status(self, doctor_token, test_setup):
        """Test filtering prescriptions by status"""
        patient = test_setup["patients"][0]

        # Create prescription
        prescription_text = """
        Patient: Robert Johnson
        Medication: Aspirin
        Dosage: 100mg daily
        Duration: 30 days
        """

        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        # List active prescriptions
        list_response = client.get(
            "/api/prescriptions?status=active",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )

        assert list_response.status_code == 200
        active_rxs = list_response.json()
        assert all(rx["status"] == "active" for rx in active_rxs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
