"""
Unit tests for Vocalis backend endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app, PrescriptionData, CollectInfoResponse

client = TestClient(app)


class TestPrescriptionDataModel:
    """Test PrescriptionData Pydantic model"""

    def test_empty_prescription_data(self):
        """Test creating empty prescription data"""
        data = PrescriptionData()
        assert data.patientName is None
        assert data.patientAge is None
        assert not data.is_complete()

    def test_missing_required_fields(self):
        """Test identifying missing required fields"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans"
        )
        missing = data.get_missing_required_fields()
        assert len(missing) == 5  # diagnosis, medication, dosage, duration, specialInstructions
        assert "Diagnostic" in missing
        assert "Médicament" in missing

    def test_complete_prescription_data(self):
        """Test complete prescription data"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans",
            diagnosis="Hypertension artérielle",
            medication="Lisinopril",
            dosage="10mg, 1 fois par jour",
            duration="3 mois",
            specialInstructions="Prendre le matin à jeun"
        )
        assert data.is_complete()
        assert len(data.get_missing_required_fields()) == 0

    def test_prescription_data_json_serialization(self):
        """Test JSON serialization"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            patientAge="45 ans",
            diagnosis="Hypertension"
        )
        json_data = data.toJson()
        assert json_data['patientName'] == "Jean Dupont"
        assert json_data['patientAge'] == "45 ans"
        assert json_data['diagnosis'] == "Hypertension"
        assert json_data['medication'] is None

    def test_prescription_data_json_deserialization(self):
        """Test JSON deserialization"""
        json_data = {
            'patientName': 'Jane Smith',
            'patientAge': '30 ans',
            'diagnosis': 'Diabète',
            'medication': 'Metformine',
            'dosage': '500mg',
            'duration': '6 mois',
            'specialInstructions': 'Avec les repas'
        }
        data = PrescriptionData.fromJson(json_data)
        assert data.patientName == 'Jane Smith'
        assert data.is_complete()

    def test_copy_with(self):
        """Test copyWith functionality"""
        data1 = PrescriptionData(patientName="Jean")
        data2 = data1.copyWith(patientAge='50 ans')
        assert data2.patientName == "Jean"
        assert data2.patientAge == "50 ans"
        assert data1.patientAge is None  # Original unchanged

    def test_format_for_display(self):
        """Test display formatting"""
        data = PrescriptionData(
            patientName="Jean Dupont",
            diagnosis="Hypertension"
        )
        display = data.format_for_display()
        assert "Jean Dupont" in display
        assert "Hypertension" in display
        assert "Nom du patient" in display


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test /api/health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert data['backend'] == 'running'
        assert 'model_loaded' in data
        assert 'model_path' in data


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self):
        """Test / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'message' in data


class TestCollectPrescriptionInfoEndpoint:
    """Test /api/collect-prescription-info endpoint"""

    def test_collect_info_endpoint_exists(self):
        """Test endpoint is accessible"""
        current_data = PrescriptionData()
        request_body = {
            'currentData': current_data.toJson(),
            'userInput': 'Je m\'appelle Jean Dupont et j\'ai 45 ans'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)
        # Should be 200 if model is loaded, 503 if not
        assert response.status_code in [200, 503]

    def test_collect_info_response_structure(self):
        """Test response structure when model is available"""
        current_data = PrescriptionData()
        request_body = {
            'currentData': current_data.toJson(),
            'userInput': 'Patient: Marie, 30 ans'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)

        if response.status_code == 200:
            data = response.json()
            assert 'status' in data
            assert 'missingFields' in data
            assert 'message' in data
            assert 'collectedData' in data
            assert data['status'] in ['needs_more_info', 'complete']

    def test_collect_info_with_partial_data(self):
        """Test updating existing prescription data"""
        current_data = PrescriptionData(patientName="Jean Dupont")
        request_body = {
            'currentData': current_data.toJson(),
            'userInput': 'J\'ai 50 ans'
        }
        response = client.post("/api/collect-prescription-info", json=request_body)

        if response.status_code == 200:
            data = response.json()
            # Should have collected age information
            collected = data['collectedData']
            assert 'patientName' in collected
            assert 'patientAge' in collected


class TestGeneratePrescriptionEndpoint:
    """Test /api/generate-prescription endpoint"""

    def test_incomplete_data_returns_400(self):
        """Test that incomplete data returns 400"""
        incomplete_data = {
            'patientName': 'Jean Dupont',
            'patientAge': '45 ans'
            # Missing: diagnosis, medication, dosage, duration, specialInstructions
        }
        request_body = {'data': incomplete_data}
        response = client.post("/api/generate-prescription", json=request_body)

        if response.status_code != 503:  # If model is loaded
            assert response.status_code == 400
            data = response.json()
            assert 'detail' in data

    def test_complete_data_returns_200_or_503(self):
        """Test that complete data returns 200 (or 503 if model not loaded)"""
        complete_data = {
            'patientName': 'Jean Dupont',
            'patientAge': '45 ans',
            'diagnosis': 'Hypertension artérielle',
            'medication': 'Lisinopril',
            'dosage': '10mg, 1 fois par jour',
            'duration': '3 mois',
            'specialInstructions': 'Prendre le matin à jeun'
        }
        request_body = {'data': complete_data}
        response = client.post("/api/generate-prescription", json=request_body)

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert 'prescription' in data
            assert isinstance(data['prescription'], str)
            assert len(data['prescription']) > 0


class TestChatEndpoint:
    """Test /api/chat endpoint (existing functionality)"""

    def test_chat_endpoint_exists(self):
        """Test /api/chat endpoint is accessible"""
        request_body = {'message': 'Bonjour'}
        response = client.post("/api/chat", json=request_body)
        assert response.status_code in [200, 503]

    def test_chat_response_structure(self):
        """Test chat response structure"""
        request_body = {'message': 'Redige une ordonnance pour une hypertension'}
        response = client.post("/api/chat", json=request_body)

        if response.status_code == 200:
            data = response.json()
            assert 'response' in data
            assert isinstance(data['response'], str)


class TestPDFEndpoint:
    """Test /api/generate-pdf endpoint (existing functionality)"""

    def test_pdf_endpoint_missing_signature(self):
        """Test PDF generation without signature"""
        request_body = {
            'content': 'Ordonnance:\nLisinopril 10mg\n1 fois par jour\nPour 3 mois',
            'signature_base64': ''
        }
        response = client.post("/api/generate-pdf", json=request_body)

        if response.status_code == 200:
            assert response.headers['content-type'] == 'application/pdf'
            assert len(response.content) > 0


class TestErrorHandling:
    """Test error handling"""

    def test_chat_with_empty_message(self):
        """Test chat with empty message"""
        request_body = {'message': ''}
        # Empty message might be accepted by API, but let's test it
        response = client.post("/api/chat", json=request_body)
        # Should handle gracefully
        assert response.status_code in [200, 503, 422]

    def test_malformed_json(self):
        """Test with invalid JSON"""
        response = client.post(
            "/api/chat",
            json={'invalid_field': 'value'}
        )
        # FastAPI should return 422 for missing required field
        assert response.status_code in [422, 500]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
