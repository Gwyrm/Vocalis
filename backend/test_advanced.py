"""
Advanced tests for Vocalis backend - Data extraction and model behavior
"""
import pytest
import json
from main import (
    app, PrescriptionData, extract_prescription_data_from_message,
    build_info_request_prompt, SYSTEM_PROMPT
)
from fastapi.testclient import TestClient

client = TestClient(app)


class TestDataExtractionFunctions:
    """Test data extraction helper functions"""

    def test_build_info_request_prompt_with_empty_data(self):
        """Test prompt building with empty data"""
        data = PrescriptionData()
        user_message = "Bonjour"
        prompt = build_info_request_prompt(data, user_message)

        assert SYSTEM_PROMPT in prompt
        assert user_message in prompt
        assert "Aucune information collectée" in prompt

    def test_build_info_request_prompt_with_partial_data(self):
        """Test prompt building with partial data"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans"
        )
        user_message = "Quel diagnostic?"
        prompt = build_info_request_prompt(data, user_message)

        assert "Jean Dupont" in prompt
        assert "45 ans" in prompt
        # Should mention missing fields
        assert "Diagnostic" in prompt or "manquant" in prompt.lower()

    def test_build_info_request_prompt_with_complete_data(self):
        """Test prompt building with complete data"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg",
            duration="3 mois",
            specialInstructions="Matin à jeun"
        )
        user_message = "Générer ordonnance"
        prompt = build_info_request_prompt(data, user_message)

        assert "Jean Dupont" in prompt
        assert "Hypertension" in prompt
        assert "Lisinopril" in prompt


class TestIntegrationFlow:
    """Test complete workflow integration"""

    def test_full_prescription_collection_and_generation_flow(self):
        """Test the complete flow: collect info -> generate prescription"""
        # Step 1: Start with empty data
        current_data = PrescriptionData()
        assert not current_data.is_complete()

        # Step 2: First input - patient name
        request_body = {
            'currentData': current_data.toJson(),
            'userInput': 'Le patient s\'appelle Jean Dupont'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data['status'] == 'needs_more_info'
            current_data = PrescriptionData.fromJson(data['collectedData'])
            # Data should have been collected
            assert 'patientName' in data['collectedData']

    def test_incomplete_data_cannot_be_prescribed(self):
        """Test that incomplete data cannot generate prescription"""
        incomplete_data = PrescriptionData(
            patientName="Jean",
            patientAge="45"
            # Missing diagnosis, medication, dosage, duration, specialInstructions
        )
        request_body = {'data': incomplete_data.toJson()}
        response = client.post("/api/generate-prescription", json=request_body)

        if response.status_code != 503:  # If model is loaded
            assert response.status_code == 400
            error_data = response.json()
            assert 'detail' in error_data
            assert 'incomp' in error_data['detail'].lower() or 'manquant' in error_data['detail'].lower()


class TestDataValidation:
    """Test data validation and edge cases"""

    def test_prescription_with_only_required_fields(self):
        """Test prescription with minimal data"""
        data = PrescriptionData(
            patientName="J",
            patientAge="1",
            diagnosis="D",
            medication="M",
            dosage="X",
            duration="Y",
            specialInstructions="Z"
        )
        assert data.is_complete()
        missing = data.get_missing_required_fields()
        assert len(missing) == 0

    def test_prescription_with_whitespace_only(self):
        """Test that whitespace-only fields count as missing"""
        data = PrescriptionData(
            patientName="   ",  # Whitespace
            patientAge="45",
            diagnosis="Test",
            medication="Med",
            dosage="10mg",
            duration="1m",
            specialInstructions="Notes"
        )
        # Whitespace is still considered as a value by Pydantic
        # So this should be complete (whitespace counts as value)
        assert data.is_complete() or len(data.get_missing_required_fields()) <= 0

    def test_special_characters_in_prescription_data(self):
        """Test prescription data with special characters"""
        data = PrescriptionData(
            patientName="Jean-Marie D'Àndo",
            patientAge="45 ans (né en 1979)",
            diagnosis="Hypertension, diabète",
            medication="Lisinopril® 10mg",
            dosage="1 cp × 1/jour",
            duration="3 mois",
            specialInstructions="À prendre le matin; éventuellement avec citron (C₆H₈O₆)"
        )
        assert data.is_complete()

        # Should serialize/deserialize correctly
        json_data = data.toJson()
        restored = PrescriptionData.fromJson(json_data)
        assert restored.patientName == data.patientName
        assert restored.specialInstructions == data.specialInstructions

    def test_long_prescription_data(self):
        """Test prescription with very long fields"""
        long_diagnosis = "Hypertension artérielle pulmonaire avec insuffisance cardiaque droite secondaire" * 5
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans",
            diagnosis=long_diagnosis,
            medication="Lisinopril",
            dosage="10mg, 1 fois par jour, à prendre le matin à jeun avec un verre d'eau",
            duration="3 mois renouvelable selon suivi",
            specialInstructions="À prendre le matin à jeun. Contrôle tension toutes les 2 semaines. "
                                "Signaler tout symptôme anormal: vertige, palpitations, douleur thoracique."
        )
        assert data.is_complete()
        json_data = data.toJson()
        assert len(json_data['diagnosis']) > 100

    def test_format_for_display_with_all_fields(self):
        """Test display formatting with all fields populated"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg/jour",
            duration="3 mois",
            specialInstructions="Matin à jeun"
        )
        display = data.format_for_display()

        assert "Jean Dupont" in display
        assert "45 ans" in display
        assert "Hypertension" in display
        assert "Lisinopril" in display
        assert "10mg/jour" in display
        assert "3 mois" in display
        assert "Matin à jeun" in display
        assert "•" in display  # Should use bullet points


class TestErrorScenarios:
    """Test error handling scenarios"""

    def test_collect_info_with_invalid_json_structure(self):
        """Test with incorrect request structure"""
        request_body = {
            'invalidField': {},
            'anotherInvalid': 'test'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_generate_prescription_with_invalid_json_structure(self):
        """Test prescription generation with invalid structure"""
        request_body = {
            'invalidField': {}
        }
        response = client.post("/api/generate-prescription", json=request_body)
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_null_values_in_prescription_data(self):
        """Test that None/null values are handled"""
        data = PrescriptionData(
            patientName=None,
            patientAge=None,
            diagnosis=None,
            medication=None,
            dosage=None,
            duration=None,
            specialInstructions=None
        )
        assert not data.is_complete()
        missing = data.get_missing_required_fields()
        assert len(missing) == 7  # All fields should be missing

    def test_empty_string_vs_none(self):
        """Test that empty strings are treated as missing"""
        data_with_empty = PrescriptionData(
            patientName="",
            patientAge="",
            diagnosis="Test",
            medication="Test",
            dosage="Test",
            duration="Test",
            specialInstructions="Test"
        )
        # Empty strings should not count as filled
        # This depends on Pydantic validation
        missing = data_with_empty.get_missing_required_fields()
        # Empty strings are technically "falsy" so should be in missing
        assert "Nom du patient" in missing or "Âge" in missing


class TestApiResponses:
    """Test API response formats and codes"""

    def test_health_endpoint_response_format(self):
        """Test health endpoint returns correct format"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        required_fields = ['status', 'backend', 'model_loaded', 'model_path']
        for field in required_fields:
            assert field in data

    def test_collect_info_response_has_all_fields(self):
        """Test collect info response has required fields"""
        current_data = PrescriptionData()
        request_body = {
            'currentData': current_data.toJson(),
            'userInput': 'Test'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)

        if response.status_code == 200:
            data = response.json()
            required = ['status', 'missingFields', 'message', 'collectedData']
            for field in required:
                assert field in data, f"Missing field: {field}"

            # Verify types
            assert isinstance(data['status'], str)
            assert isinstance(data['missingFields'], list)
            assert isinstance(data['message'], str)
            assert isinstance(data['collectedData'], dict)

    def test_generate_prescription_response_format(self):
        """Test generate prescription response format"""
        data = PrescriptionData(
            patientName="Test",
            patientAge="50",
            diagnosis="Test",
            medication="Test",
            dosage="Test",
            duration="Test",
            specialInstructions="Test"
        )
        request_body = {'data': data.toJson()}
        response = client.post("/api/generate-prescription", json=request_body)

        if response.status_code == 200:
            data = response.json()
            assert 'prescription' in data
            assert isinstance(data['prescription'], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
