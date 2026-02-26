"""
Live integration tests for text prescription generation
Tests against running backend instance
"""

import pytest
import requests
import json
from datetime import datetime


BASE_URL = "http://127.0.0.1:8080"


class TestTextPrescriptionLive:
    """Live tests for text prescription creation"""

    @classmethod
    def setup_class(cls):
        """Setup: Get auth token and patient data"""
        # Get demo auth token
        response = requests.post(
            f"{BASE_URL}/api/auth/demo",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        cls.token = response.json()["access_token"]
        cls.user = response.json()["user"]

        # Get list of patients
        patients_response = requests.get(
            f"{BASE_URL}/api/patients",
            headers={"Authorization": f"Bearer {cls.token}"}
        )
        assert patients_response.status_code == 200
        patients = patients_response.json()
        assert len(patients) > 0

        cls.patient_id = patients[0]["id"]
        cls.patient_name = f"{patients[0]['first_name']} {patients[0]['last_name']}"
        cls.patient = patients[0]

    def test_01_create_valid_prescription_from_text(self):
        """Test creating a valid prescription from text input"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Lisinopril
        Dosage: 10mg once daily
        Duration: 30 days
        Diagnosis: Hypertension management
        Instructions: Take in the morning with water
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "prescription" in data
        assert "validation" in data
        assert "patient_summary" in data

        # Verify prescription was created
        assert data["prescription"] is not None
        rx = data["prescription"]
        assert rx["medication"] == "lisinopril" or "lisinopril" in rx["medication"].lower()
        assert "Lisinopril" in rx["medication"] or "lisinopril" in rx["medication"].lower()
        assert rx["dosage"] == "10mg once daily"
        assert rx["patient_name"] == self.patient_name
        assert rx["status"] == "active"

        print(f"\n✓ Valid prescription created")
        print(f"  ID: {rx['id']}")
        print(f"  Medication: {rx['medication']}")
        print(f"  Dosage: {rx['dosage']}")
        print(f"  Patient: {rx['patient_name']}")

    def test_02_prescription_text_with_multiple_formats(self):
        """Test prescription text with various formatting styles"""
        prescription_text = f"Patient: {self.patient_name}\nMédication: Metformin\nPosologie: 500mg twice daily\nDurée: 90 days\nDiagnose: Type 2 Diabetes"

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle French formatting
        assert data["prescription"] is not None or data["validation"] is not None
        print(f"✓ Prescription with French formatting handled correctly")

    def test_03_prescription_with_discovered_allergies(self):
        """Test creating prescription mentioning discovered allergies in text"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Amoxicillin
        Dosage: 500mg three times daily
        Duration: 7 days
        Diagnosis: Bacterial infection
        Notes: Patient reports sensitivity to beta-lactams during appointment
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prescription"] is not None
        assert data["prescription"]["medication"] is not None

        # Verify prescription includes patient info
        assert data["patient_summary"] is not None
        allergies = data["patient_summary"].get("allergies", [])
        assert len(allergies) > 0  # Patient should have allergies in summary

        print(f"✓ Prescription with allergy mentions created")
        print(f"  Patient current allergies: {allergies}")

    def test_04_prescription_with_medical_conditions(self):
        """Test prescription that addresses existing medical conditions"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Metformin
        Dosage: 500mg twice daily
        Duration: 90 days
        Diagnosis: Type 2 Diabetes management
        Notes: Patient has multiple chronic conditions requiring monitoring
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify patient conditions are included in response
        patient_summary = data["patient_summary"]
        conditions = patient_summary.get("chronic_conditions", [])

        assert len(conditions) > 0  # Patient should have chronic conditions

        print(f"✓ Prescription for patient with chronic conditions created")
        print(f"  Patient chronic conditions: {conditions}")

    def test_05_prescription_validation_structure(self):
        """Test that validation response has correct structure"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Aspirin
        Dosage: 100mg daily
        Duration: 30 days
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify validation structure
        validation = data["validation"]
        assert isinstance(validation, dict)
        assert "valid" in validation
        assert "confidence" in validation
        assert "errors" in validation
        assert "warnings" in validation

        assert isinstance(validation["valid"], bool)
        assert isinstance(validation["confidence"], (int, float))
        assert 0 <= validation["confidence"] <= 1.0
        assert isinstance(validation["errors"], list)
        assert isinstance(validation["warnings"], list)

        print(f"✓ Validation structure correct")
        print(f"  Valid: {validation['valid']}")
        print(f"  Confidence: {validation['confidence']:.1%}")
        print(f"  Errors: {len(validation['errors'])}")
        print(f"  Warnings: {len(validation['warnings'])}")

    def test_06_prescription_includes_patient_summary(self):
        """Test that response includes complete patient summary"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Lisinopril
        Dosage: 10mg daily
        Duration: 30 days
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify patient summary
        patient_summary = data["patient_summary"]
        assert patient_summary is not None
        assert patient_summary["id"] == self.patient_id
        assert patient_summary["first_name"] == self.patient["first_name"]
        assert patient_summary["last_name"] == self.patient["last_name"]
        assert "allergies" in patient_summary

        print(f"✓ Patient summary included in response")
        print(f"  Patient: {patient_summary['first_name']} {patient_summary['last_name']}")
        print(f"  Allergies: {patient_summary.get('allergies', [])}")

    def test_07_invalid_patient_id(self):
        """Test with non-existent patient ID"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": "invalid-uuid-12345",
                "prescription_text": "Patient: X\nMedication: Y\nDosage: 100mg",
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 404
        error = response.json()
        assert "not found" in error.get("detail", "").lower()

        print(f"✓ Invalid patient correctly rejected with 404")

    def test_08_missing_authorization(self):
        """Test without authentication"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": "Patient: Test\nMedication: X\nDosage: 100mg",
            }
        )

        # Should be rejected (403 Forbidden or 500 depending on implementation)
        assert response.status_code in [403, 500]

        print(f"✓ Missing auth correctly rejected (status {response.status_code})")

    def test_09_empty_prescription_text(self):
        """Test with empty prescription text"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": "",
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        # Should either return 400 or validation error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data["validation"]["valid"] is False

        print(f"✓ Empty prescription handled correctly")

    def test_10_prescription_with_special_characters(self):
        """Test with special characters and accents"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Médication: Érythromycine
        Posologie: 250mg, 2× par jour
        Durée: 7 jours
        Diagnostic: Infection respiratoire
        Instructions: À prendre avec nourriture
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prescription"] is not None or data["validation"] is not None

        print(f"✓ Special characters and accents handled correctly")

    def test_11_multiple_prescriptions_same_patient(self):
        """Test creating multiple prescriptions for same patient"""
        created_ids = []

        for i in range(2):
            prescription_text = f"""
            Patient: {self.patient_name}
            Medication: Med{i}
            Dosage: 100mg daily
            Duration: 30 days
            """

            response = requests.post(
                f"{BASE_URL}/api/prescriptions/text",
                json={
                    "patient_id": self.patient_id,
                    "prescription_text": prescription_text,
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            assert response.status_code == 200
            created_ids.append(response.json()["prescription"]["id"])

        # Verify we created them
        assert len(created_ids) >= 2

        print(f"✓ Multiple prescriptions created successfully")
        print(f"  Created prescriptions: {len(created_ids)}")

    def test_12_prescription_fields_populated(self):
        """Test that all prescription fields are properly populated"""
        prescription_text = f"""
        Patient: {self.patient_name}
        Medication: Lisinopril
        Dosage: 10mg once daily
        Duration: 30 days
        Diagnosis: Hypertension
        Instructions: Take with water
        """

        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={
                "patient_id": self.patient_id,
                "prescription_text": prescription_text,
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        rx = response.json()["prescription"]

        # Verify all expected fields are present and populated
        required_fields = [
            "id", "patient_name", "patient_age", "medication",
            "dosage", "duration", "diagnosis", "status", "created_at"
        ]

        for field in required_fields:
            assert field in rx, f"Missing field: {field}"
            assert rx[field] is not None, f"Field is None: {field}"

        print(f"✓ All prescription fields properly populated")
        print(f"  Fields: {list(rx.keys())}")


class TestPrescriptionErrorHandling:
    """Test error handling scenarios"""

    @classmethod
    def setup_class(cls):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/demo",
            json={},
            headers={"Content-Type": "application/json"}
        )
        cls.token = response.json()["access_token"]

    def test_malformed_json_request(self):
        """Test with malformed JSON"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            data="not json",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code in [400, 422]
        print(f"✓ Malformed JSON correctly rejected")

    def test_missing_required_field(self):
        """Test with missing required field"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/text",
            json={"patient_id": "some-id"},  # Missing prescription_text
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code in [400, 422]
        print(f"✓ Missing required field correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
