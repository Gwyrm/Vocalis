"""
Tests for Vocalis Backend endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import main
from main import app, PrescriptionData

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session():
    """Reset session data before each test"""
    main.session_data = {}
    yield
    main.session_data = {}


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "backend" in data
        assert "ollama_available" in data
        assert data["status"] == "ok"
        assert data["backend"] == "running"


class TestRootEndpoint:
    """Tests for / endpoint"""

    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data


class TestChatEndpoint:
    """Tests for /api/chat endpoint"""

    def test_chat_ollama_unavailable(self):
        """Test chat when Ollama is not available"""
        with patch("main.ollama_available", False):
            response = client.post("/api/chat", json={"message": "Test message"})
            assert response.status_code == 503
            assert "Ollama n'est pas disponible" in response.json()["detail"]

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_chat_extraction(self, mock_call_ollama):
        """Test chat with message extraction"""
        # Mock Ollama responses
        mock_call_ollama.side_effect = [
            # First call: extraction
            "Nom: John Doe\nAge: 45\nDiagnostic: Hypertension\nMedicament: Lisinopril\nDosage: 10mg/jour\nDuree: 30 jours\nInstructions: Prendre le matin",
            # Second call: response generation
            "J'ai bien reçu les informations pour John Doe. Ordonnance complète!"
        ]

        response = client.post("/api/chat", json={"message": "Patient John Doe 45 ans, hypertension, Lisinopril 10mg/jour, 30 jours"})

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "is_complete" in data
        assert "missing_fields" in data
        assert "prescription_data" in data
        assert data["is_complete"] == True

        # Check extracted data
        prescription = data["prescription_data"]
        assert prescription["patientName"] == "John Doe"
        assert prescription["patientAge"] == "45"
        assert prescription["diagnosis"] == "Hypertension"
        assert prescription["medication"] == "Lisinopril"
        assert prescription["dosage"] == "10mg/jour"
        assert prescription["duration"] == "30 jours"
        assert prescription["specialInstructions"] == "Prendre le matin"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_chat_partial_extraction(self, mock_call_ollama):
        """Test chat with partial information"""
        mock_call_ollama.side_effect = [
            # First call: extraction (incomplete)
            "Nom: Jane Smith\nAge: 30",
            # Second call: response
            "Merci Jane. Il me manque encore le diagnostic, le médicament, la posologie, la durée et les instructions."
        ]

        response = client.post("/api/chat", json={"message": "Je m'appelle Jane Smith et j'ai 30 ans"})

        assert response.status_code == 200
        data = response.json()
        # With only name and age, should be incomplete
        assert data["is_complete"] == False, f"Expected incomplete but got {data}"
        assert len(data["missing_fields"]) > 0

        prescription = data["prescription_data"]
        assert prescription["patientName"] == "Jane Smith"
        assert prescription["patientAge"] == "30"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_chat_empty_message(self, mock_call_ollama):
        """Test chat with empty message"""
        mock_call_ollama.return_value = ""

        response = client.post("/api/chat", json={"message": ""})

        assert response.status_code == 200

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_chat_conversation_flow(self, mock_call_ollama):
        """Test multiple messages in conversation"""
        mock_call_ollama.side_effect = [
            # Message 1: First info
            "Nom: Alice\nAge: ",
            "OK, j'ai enregistré Alice. Quel est votre âge?",
            # Message 2: Age
            "Nom: Alice\nAge: 28",
            "Merci Alice. Quel est votre diagnostic?",
            # Message 3: Remaining info
            "Nom: Alice\nAge: 28\nDiagnostic: Diabete\nMedicament: Metformine\nDosage: 500mg x2/jour\nDuree: 90 jours\nInstructions: Avec nourriture",
            "Ordonnance complète pour Alice!"
        ]

        # Message 1
        resp1 = client.post("/api/chat", json={"message": "Je m'appelle Alice"})
        assert resp1.status_code == 200

        # Message 2
        resp2 = client.post("/api/chat", json={"message": "J'ai 28 ans"})
        assert resp2.status_code == 200

        # Message 3
        resp3 = client.post("/api/chat", json={"message": "Diabete, Metformine 500mg x2/jour pendant 90 jours avec nourriture"})
        assert resp3.status_code == 200
        assert resp3.json()["is_complete"] == True


class TestGeneratePDFEndpoint:
    """Tests for /api/generate-pdf endpoint"""

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_generate_pdf_complete_data(self, mock_call_ollama):
        """Test PDF generation with complete data"""
        # First set up complete data via chat
        mock_call_ollama.side_effect = [
            "Nom: John Doe\nAge: 45\nDiagnostic: Hypertension\nMedicament: Lisinopril\nDosage: 10mg/jour\nDuree: 30 jours\nInstructions: Prendre le matin",
            "Ordonnance ok"
        ]

        # Send chat message to populate data
        client.post("/api/chat", json={"message": "John Doe 45 ans, Hypertension, Lisinopril 10mg/jour, 30 jours, matin"})

        # Generate PDF
        response = client.post("/api/generate-pdf", json={"signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generate_pdf_incomplete_data(self):
        """Test PDF generation with incomplete data"""
        # Verify session is empty
        assert main.session_data == {}, f"Session should be empty but got {main.session_data}"

        response = client.post("/api/generate-pdf", json={"signature_base64": ""})

        assert response.status_code == 400, f"Expected 400 but got {response.status_code}: {response.json()}"
        assert "Donnees incomples" in response.json()["detail"]

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_generate_pdf_without_signature(self, mock_call_ollama):
        """Test PDF generation without signature"""
        # Set up complete data
        mock_call_ollama.side_effect = [
            "Nom: John Doe\nAge: 45\nDiagnostic: Hypertension\nMedicament: Lisinopril\nDosage: 10mg/jour\nDuree: 30 jours\nInstructions: Prendre le matin",
            "OK"
        ]

        client.post("/api/chat", json={"message": "John Doe 45 ans, Hypertension, Lisinopril 10mg/jour, 30 jours, matin"})

        # Generate PDF without signature
        response = client.post("/api/generate-pdf", json={"signature_base64": ""})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestResetEndpoint:
    """Tests for /api/reset endpoint"""

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_reset_clears_session(self, mock_call_ollama):
        """Test that reset clears session data"""
        # Set up data
        mock_call_ollama.side_effect = [
            "Nom: John Doe\nAge: 45",
            "OK"
        ]

        # Add some data
        resp1 = client.post("/api/chat", json={"message": "John Doe 45 ans"})
        assert resp1.json()["prescription_data"]["patientName"] == "John Doe"

        # Reset
        resp2 = client.post("/api/reset")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"

        # Verify data is cleared - next chat should have no previous data
        mock_call_ollama.side_effect = [
            "Nom: Alice",
            "Bonjour Alice"
        ]

        resp3 = client.post("/api/chat", json={"message": "Je m'appelle Alice"})
        data = resp3.json()["prescription_data"]
        # Should only have Alice, not John Doe
        assert data["patientName"] == "Alice"


class TestPrescriptionDataModel:
    """Tests for PrescriptionData model"""

    def test_get_missing_fields(self):
        """Test missing fields detection"""
        data = PrescriptionData(patientName="John")
        missing = data.get_missing_fields()

        assert len(missing) == 6
        assert "Age/Date de naissance" in missing
        assert "Diagnostic" in missing

    def test_is_complete(self):
        """Test completion check"""
        incomplete = PrescriptionData(patientName="John")
        assert incomplete.is_complete() == False

        complete = PrescriptionData(
            patientName="John",
            patientAge="45",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg/jour",
            duration="30 jours",
            specialInstructions="Matin"
        )
        assert complete.is_complete() == True

    def test_format_display(self):
        """Test display formatting"""
        data = PrescriptionData(
            patientName="John",
            patientAge="45",
            diagnosis="Hypertension"
        )
        display = data.format_display()

        assert "Nom: John" in display
        assert "Age: 45" in display
        assert "Diagnostic: Hypertension" in display


class TestErrorHandling:
    """Tests for error handling"""

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_chat_error_in_generation(self, mock_call_ollama):
        """Test chat handles Ollama errors gracefully"""
        # When Ollama fails, extraction returns unchanged data
        # and response generation returns an error message
        mock_call_ollama.side_effect = Exception("Ollama API Error")

        response = client.post("/api/chat", json={"message": "Test"})

        # Should still return 200 but with error message in response
        assert response.status_code == 200
        data = response.json()
        assert "Erreur" in data["response"] or "response" in data

    def test_invalid_json(self):
        """Test invalid JSON handling"""
        response = client.post("/api/chat", json={"invalid_field": "value"})

        # FastAPI should return 422 for validation error
        assert response.status_code == 422


class TestExtractionWithDifferentPrompts:
    """Tests extraction with different message formats and styles"""

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_structured_format(self, mock_call_ollama):
        """Test extraction with structured/labeled format"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Pierre Dupont\nAge: 52\nDiagnostic: Hypertension arterielle\nMedicament: Amlodipine\nDosage: 5mg une fois par jour\nDuree: 3 mois\nInstructions: A prendre le matin avec verre d'eau",
            # Response generation
            "Prescription enregistrée pour Pierre Dupont. Ordonnance complète!"
        ]

        message = """
        Nom: Pierre Dupont
        Age: 52 ans
        Diagnostic: Hypertension arterielle
        Medicament: Amlodipine
        Dosage: 5mg une fois par jour
        Duree: 3 mois
        Instructions: A prendre le matin avec verre d'eau
        """

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["patientName"] == "Pierre Dupont"
        assert data["prescription_data"]["patientAge"] == "52"
        assert data["prescription_data"]["diagnosis"] == "Hypertension arterielle"
        assert data["prescription_data"]["medication"] == "Amlodipine"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_narrative_format(self, mock_call_ollama):
        """Test extraction with narrative/conversational format"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Marie Lemoine\nAge: 38\nDiagnostic: Diabete type 2\nMedicament: Metformine\nDosage: 500mg deux fois par jour\nDuree: Indefini\nInstructions: Prendre avec les repas, faire bilan sanguin tous les 3 mois",
            # Response generation
            "J'ai bien enregistré les infos pour Marie. Prescription prête!"
        ]

        message = """J'ai une patiente, Marie Lemoine, 38 ans, qui souffre de diabète type 2.
        Je dois lui prescrire de la Metformine 500mg deux fois par jour.
        C'est un traitement long terme sans limite de durée.
        Elle doit prendre le médicament avec les repas et faire un bilan sanguin tous les 3 mois."""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["patientName"] == "Marie Lemoine"
        assert data["prescription_data"]["diagnosis"] == "Diabete type 2"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_minimal_format(self, mock_call_ollama):
        """Test extraction with minimal/concise format"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Jean Martin\nAge: 65\nDiagnostic: Insuffisance cardiaque\nMedicament: Lisinopril\nDosage: 10mg par jour\nDuree: 6 mois\nInstructions: Surveillance cardiaque tous les 15 jours",
            # Response generation
            "Ordonnance enregistrée pour Jean Martin."
        ]

        message = "Jean Martin, 65a, insuffisance cardiaque, Lisinopril 10mg/j, 6m, suivi cardio q15j"

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["patientName"] == "Jean Martin"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_with_special_characters(self, mock_call_ollama):
        """Test extraction with accents and special characters"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Francoise Marechal\nAge: 45\nDiagnostic: Migraine chronique\nMedicament: Sumatriptan\nDosage: 50mg des l'apparition de la crise\nDuree: 2 mois\nInstructions: A prendre au debut de la migraine, ne pas depasser 3 doses par semaine",
            # Response generation
            "Prescription validée pour Francoise."
        ]

        message = """Patiente: Françoise Maréchal
        Âge: 45 ans
        Diagnostic: Migraine chronique
        Médicament: Sumatriptan
        Posologie: 50mg dès l'apparition de la crise
        Durée: 2 mois
        Instructions: À prendre au début de la migraine, ne pas dépasser 3 doses par semaine"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert "Francoise" in data["prescription_data"]["patientName"] or "Franç" in data["prescription_data"]["patientName"]

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_with_dosage_variations(self, mock_call_ollama):
        """Test extraction with different dosage formats"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Laurent Petit\nAge: 33\nDiagnostic: Infection bacterienne\nMedicament: Amoxicilline\nDosage: 500mg trois fois par jour (matin, midi, soir)\nDuree: 7 jours\nInstructions: Terminer le traitement completement, eviter alcool",
            # Response generation
            "Prescription enregistrée."
        ]

        message = """Laurent Petit, 33 ans
        Diagnostic: infection bactérienne
        Prescription: Amoxicilline 500mg × 3/jour (matin-midi-soir)
        Durée: 7 jours
        Notes: Compléter le traitement, pas d'alcool"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["medication"] == "Amoxicilline"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_with_age_variations(self, mock_call_ollama):
        """Test extraction with different age formats"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Sophie Renard\nAge: 28\nDiagnostic: Depression legere\nMedicament: Sertraline\nDosage: 50mg par jour\nDuree: 3 mois\nInstructions: Suivi psychologique recommande",
            # Response generation
            "Prescription validée."
        ]

        message = """Sophie Renard née le 15/03/1996 (28 ans)
        Diagnostic: dépression légère
        Médicament: Sertraline 50mg/jour
        Durée du traitement: 3 mois
        Suivi: consultation psychologique recommandée"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["patientAge"] in ["28", "1996"]

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_progressive_filling(self, mock_call_ollama):
        """Test filling prescription info progressively across multiple messages"""
        mock_call_ollama.side_effect = [
            # Message 1: Basic patient info
            "Nom: Robert Blanc\nAge: 72",
            "Merci. J'ai enregistré Robert Blanc, 72 ans. Quel est le diagnostic?",

            # Message 2: Diagnosis
            "Nom: Robert Blanc\nAge: 72\nDiagnostic: Arthrose cervicale",
            "OK. Arthrose cervicale enregistrée. Quel médicament?",

            # Message 3: Medication
            "Nom: Robert Blanc\nAge: 72\nDiagnostic: Arthrose cervicale\nMedicament: Paracetamol",
            "Quel dosage et pour combien de temps?",

            # Message 4: Complete data
            "Nom: Robert Blanc\nAge: 72\nDiagnostic: Arthrose cervicale\nMedicament: Paracetamol\nDosage: 500mg trois fois par jour\nDuree: 2 mois\nInstructions: Si douleur persistante, ajouter antalgique supplementaire",
            "Ordonnance complète pour Robert!"
        ]

        # Message 1
        resp1 = client.post("/api/chat", json={"message": "Je m'appelle Robert Blanc et j'ai 72 ans"})
        assert resp1.status_code == 200
        assert resp1.json()["is_complete"] == False

        # Message 2
        resp2 = client.post("/api/chat", json={"message": "J'ai une arthrose cervicale"})
        assert resp2.status_code == 200
        assert resp2.json()["is_complete"] == False

        # Message 3
        resp3 = client.post("/api/chat", json={"message": "Prescrivez-moi du Paracetamol"})
        assert resp3.status_code == 200
        assert resp3.json()["is_complete"] == False

        # Message 4
        resp4 = client.post("/api/chat", json={"message": "500mg trois fois par jour pendant 2 mois, si douleur persistante ajouter antalgique"})
        assert resp4.status_code == 200
        data = resp4.json()
        assert data["is_complete"] == True
        assert data["prescription_data"]["patientName"] == "Robert Blanc"
        assert data["prescription_data"]["patientAge"] == "72"

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_with_medical_abbreviations(self, mock_call_ollama):
        """Test extraction with medical abbreviations and terminology"""
        mock_call_ollama.side_effect = [
            # Extraction response
            "Nom: Thomas Mercier\nAge: 41\nDiagnostic: Sinusite chronique\nMedicament: Amoxicilline-clavulanate\nDosage: 875mg deux fois par jour (matin et soir)\nDuree: 10 jours\nInstructions: Traitement ORL, repose et humidification recommandees",
            # Response generation
            "Prescription enregistrée pour Thomas."
        ]

        message = """Dossier: Thomas Mercier, 41 ans
        Diagnostic: sinusitis chronique (CIM-10: J32.9)
        Rx: Amoxicilline-clavulanate 875mg × 2/j
        Durée: 10 j
        Instructions: Suivi ORL, humidification nasale, repos"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True

    @patch("main.ollama_available", True)
    @patch("main.call_ollama")
    def test_prompt_with_extra_information(self, mock_call_ollama):
        """Test extraction ignoring irrelevant information"""
        mock_call_ollama.side_effect = [
            # Extraction response - should extract only relevant fields
            "Nom: Claire Fontaine\nAge: 29\nDiagnostic: Asthme intermittent\nMedicament: Salbutamol\nDosage: 2 bouffees au besoin\nDuree: Continu\nInstructions: Utiliser inhalateur en cas de crise, toujours avoir avec soi",
            # Response generation
            "Prescription validée pour Claire."
        ]

        message = """Consultation du 16/02/2026
        Patiente: Claire Fontaine (ID: 45782)
        DOB: 15/06/1997 (29 ans)
        Antécédents: allergie à la pénicilline
        Diagnostic: Asthme intermittent, bien contrôlé
        Examen: SpO2 97%, pas de sifflement actuellement
        Prescription:
        - Salbutamol 2 bouffées au besoin lors des crises
        Durée: traitement continu
        Note: Patient éduqué sur technique d'inhalation
        Instructions: Toujours avoir l'inhalateur avec soi"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        assert data["is_complete"] == True
        assert data["prescription_data"]["patientName"] == "Claire Fontaine"
        assert data["prescription_data"]["medication"] == "Salbutamol"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
