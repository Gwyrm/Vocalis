"""
Real model extraction tests - Tests without mocks, directly with Ollama/Mistral
Run these to verify the actual model performance
"""

import pytest
from fastapi.testclient import TestClient
import main
from main import app
import requests
import os

# Create test client
client = TestClient(app)


def is_ollama_available():
    """Check if Ollama is actually available"""
    try:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(autouse=True)
def reset_session():
    """Reset session data before each test"""
    main.session_data = {}
    yield
    main.session_data = {}


class TestRealModelExtraction:
    """Tests with actual model - no mocks"""

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_structured_format(self):
        """Test real extraction with structured format"""
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

        print("\n✅ TEST: Structured Format")
        print(f"Message: {message[:50]}...")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

        # Verify critical fields
        assert data['prescription_data']['patientName'] is not None
        assert data['prescription_data']['patientAge'] is not None

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_narrative_format(self):
        """Test real extraction with narrative format"""
        message = """J'ai une patiente, Marie Lemoine, 38 ans, qui souffre de diabète type 2.
        Je dois lui prescrire de la Metformine 500mg deux fois par jour.
        C'est un traitement long terme sans limite de durée.
        Elle doit prendre le médicament avec les repas et faire un bilan sanguin tous les 3 mois."""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Narrative Format")
        print(f"Message: {message[:50]}...")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

        # Check extraction
        assert data['prescription_data']['patientName'] is not None
        assert data['prescription_data']['diagnosis'] is not None

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_minimal_format(self):
        """Test real extraction with minimal format"""
        message = "Jean Martin, 65a, insuffisance cardiaque, Lisinopril 10mg/j, 6m, suivi cardio q15j"

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Minimal Format")
        print(f"Message: {message}")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_progressive_messages(self):
        """Test real extraction across multiple messages"""
        print("\n✅ TEST: Progressive Filling")

        # Message 1
        resp1 = client.post("/api/chat", json={"message": "Je m'appelle Robert Blanc et j'ai 72 ans"})
        assert resp1.status_code == 200
        data1 = resp1.json()
        print(f"Message 1: 'Je m'appelle Robert Blanc et j'ai 72 ans'")
        print(f"  Extracted: Name={data1['prescription_data']['patientName']}, Age={data1['prescription_data']['patientAge']}")
        print(f"  Complete: {data1['is_complete']}, Missing: {len(data1['missing_fields'])} fields")

        # Message 2
        resp2 = client.post("/api/chat", json={"message": "J'ai une arthrose cervicale"})
        assert resp2.status_code == 200
        data2 = resp2.json()
        print(f"Message 2: 'J'ai une arthrose cervicale'")
        print(f"  Diagnosis={data2['prescription_data']['diagnosis']}")
        print(f"  Complete: {data2['is_complete']}, Missing: {len(data2['missing_fields'])} fields")

        # Message 3
        resp3 = client.post("/api/chat", json={"message": "Prescrivez-moi du Paracetamol"})
        assert resp3.status_code == 200
        data3 = resp3.json()
        print(f"Message 3: 'Prescrivez-moi du Paracetamol'")
        print(f"  Medication={data3['prescription_data']['medication']}")
        print(f"  Complete: {data3['is_complete']}, Missing: {len(data3['missing_fields'])} fields")

        # Message 4
        resp4 = client.post("/api/chat", json={"message": "500mg trois fois par jour pendant 2 mois, si douleur persistante ajouter antalgique"})
        assert resp4.status_code == 200
        data4 = resp4.json()
        print(f"Message 4: '500mg trois fois par jour pendant 2 mois...'")
        print(f"  Dosage={data4['prescription_data']['dosage']}")
        print(f"  Duration={data4['prescription_data']['duration']}")
        print(f"  Instructions={data4['prescription_data']['specialInstructions']}")
        print(f"  Complete: {data4['is_complete']}, Missing: {len(data4['missing_fields'])} fields\n")

        # Final state
        assert data4['prescription_data']['patientName'] is not None
        assert data4['prescription_data']['patientAge'] is not None
        assert data4['prescription_data']['medication'] is not None

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_special_characters(self):
        """Test real extraction with special characters and accents"""
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

        print("\n✅ TEST: Special Characters & Accents")
        print(f"Message: {message[:50]}...")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_medical_abbreviations(self):
        """Test real extraction with medical abbreviations"""
        message = """Dossier: Thomas Mercier, 41 ans
        Diagnostic: sinusitis chronique
        Rx: Amoxicilline-clavulanate 875mg × 2/j
        Durée: 10 j
        Instructions: Suivi ORL, humidification nasale, repos"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Medical Abbreviations")
        print(f"Message: {message[:50]}...")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_complex_scenario(self):
        """Test real extraction with complex medical scenario"""
        message = """Consultation du 16/02/2026
        Patiente: Claire Fontaine (29 ans)
        Antécédents: allergie à la pénicilline
        Diagnostic: Asthme intermittent, bien contrôlé
        Examen: SpO2 97%, pas de sifflement actuellement
        Prescription:
        - Salbutamol 2 bouffées au besoin lors des crises
        Durée: traitement continu
        Instructions: Patient éduqué sur technique d'inhalation, toujours avoir l'inhalateur avec soi"""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Complex Scenario (Medical Record)")
        print(f"Message length: {len(message)} chars")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Missing Fields: {data['missing_fields']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Response: {data['response'][:100]}...\n")

        # Key assertions
        assert data['prescription_data']['patientName'] is not None
        assert data['prescription_data']['medication'] is not None


class TestRealModelRobustness:
    """Tests for model robustness and error handling"""

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_typos_and_informal(self):
        """Test extraction with typos and informal language"""
        message = "nom: jean dupont, age: 55, maladie: tension elevee, med: amlodipine, dose: 5 par jour, duree: 3 mois, notes: le matin"

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Typos & Informal Language")
        print(f"Message: {message}")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Extracted Name: {data['prescription_data']['patientName']}")
        print(f"Extracted Diagnosis: {data['prescription_data']['diagnosis']}")
        print(f"Response: {data['response'][:100]}...\n")

    @pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
    def test_real_extraction_no_structure(self):
        """Test extraction from free-form text without structure"""
        message = """Le patient s'appelle Sophie Renard et a 28 ans. Elle vient me voir pour une dépression légère.
        Je vais lui prescrire de la Sertraline, 50mg par jour. Elle devra prendre ça pendant 3 mois et faire un suivi psychologique."""

        response = client.post("/api/chat", json={"message": message})
        assert response.status_code == 200
        data = response.json()

        print("\n✅ TEST: Free-form Text")
        print(f"Message: {message[:60]}...")
        print(f"Is Complete: {data['is_complete']}")
        print(f"Extracted Data:")
        for key, value in data['prescription_data'].items():
            if value:
                print(f"  - {key}: {value}")
        print(f"Missing Fields: {data['missing_fields']}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
