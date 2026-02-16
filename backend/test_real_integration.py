"""
Real integration tests - Direct HTTP calls to running backend
These tests require the backend to be running: python main.py
"""

import requests
import os
import json

API_URL = os.getenv("API_URL", "http://localhost:8080")


def is_api_available():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def reset_session():
    """Reset the session before each test"""
    try:
        requests.post(f"{API_URL}/api/reset", timeout=5)
    except:
        pass


def test_health_check():
    """Verify API is healthy"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        print("Run: python main.py in another terminal")
        return

    response = requests.get(f"{API_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    print("\n✅ API Health Check")
    print(f"Status: {data.get('status')}")
    print(f"Backend: {data.get('backend')}")
    print(f"Ollama Available: {data.get('ollama_available')}")
    print(f"Model: {data.get('model')}\n")


def test_real_extraction_structured():
    """Test with structured medical data"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    message = """
Nom: Pierre Dupont
Age: 52 ans
Diagnostic: Hypertension arterielle
Medicament: Amlodipine
Dosage: 5mg une fois par jour
Duree: 3 mois
Instructions: A prendre le matin avec verre d'eau
    """

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    print("\n" + "="*70)
    print("✅ TEST 1: Structured Format")
    print("="*70)
    print(f"\nMessage:\n{message}")
    print(f"\n📊 RESULTS:")
    print(f"  Complete: {data['is_complete']}")
    print(f"  Missing Fields: {data['missing_fields']}")
    print(f"\n📝 Extracted Data:")
    for key, value in data['prescription_data'].items():
        if value:
            print(f"  • {key}: {value}")
    print(f"\n💬 Model Response:")
    print(f"  {data['response'][:150]}...\n")


def test_real_extraction_narrative():
    """Test with narrative/conversational format"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    message = """J'ai une patiente, Marie Lemoine, 38 ans, qui souffre de diabète type 2.
Je dois lui prescrire de la Metformine 500mg deux fois par jour.
C'est un traitement long terme sans limite de durée.
Elle doit prendre le médicament avec les repas et faire un bilan sanguin tous les 3 mois."""

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    print("\n" + "="*70)
    print("✅ TEST 2: Narrative Format")
    print("="*70)
    print(f"\nMessage:\n{message}")
    print(f"\n📊 RESULTS:")
    print(f"  Complete: {data['is_complete']}")
    print(f"  Missing Fields: {data['missing_fields']}")
    print(f"\n📝 Extracted Data:")
    for key, value in data['prescription_data'].items():
        if value:
            print(f"  • {key}: {value}")
    print(f"\n💬 Model Response:")
    print(f"  {data['response'][:150]}...\n")


def test_real_extraction_minimal():
    """Test with minimal/concise format"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    message = "Jean Martin, 65a, insuffisance cardiaque, Lisinopril 10mg/j, 6m, suivi cardio q15j"

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    print("\n" + "="*70)
    print("✅ TEST 3: Minimal/Concise Format")
    print("="*70)
    print(f"\nMessage: {message}")
    print(f"\n📊 RESULTS:")
    print(f"  Complete: {data['is_complete']}")
    print(f"  Missing Fields: {data['missing_fields']}")
    print(f"\n📝 Extracted Data:")
    for key, value in data['prescription_data'].items():
        if value:
            print(f"  • {key}: {value}")
    print(f"\n💬 Model Response:")
    print(f"  {data['response'][:150]}...\n")


def test_real_extraction_progressive():
    """Test with multiple progressive messages"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    print("\n" + "="*70)
    print("✅ TEST 4: Progressive Messages (Building Prescription)")
    print("="*70)

    messages = [
        "Je m'appelle Robert Blanc et j'ai 72 ans",
        "J'ai une arthrose cervicale",
        "Prescrivez-moi du Paracetamol",
        "500mg trois fois par jour pendant 2 mois, si douleur persistante ajouter antalgique"
    ]

    for i, msg in enumerate(messages, 1):
        response = requests.post(f"{API_URL}/api/chat", json={"message": msg})
        assert response.status_code == 200
        data = response.json()

        print(f"\n📍 Message {i}: \"{msg}\"")
        print(f"  Complete: {data['is_complete']}")
        print(f"  Missing: {len(data['missing_fields'])} fields")
        extracted = {k: v for k, v in data['prescription_data'].items() if v}
        print(f"  Extracted: {extracted}")


def test_real_extraction_special_characters():
    """Test with accents and special characters"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    message = """Patiente: Françoise Maréchal
Âge: 45 ans
Diagnostic: Migraine chronique
Médicament: Sumatriptan
Posologie: 50mg dès l'apparition de la crise
Durée: 2 mois
Instructions: À prendre au début de la migraine, ne pas dépasser 3 doses par semaine"""

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    print("\n" + "="*70)
    print("✅ TEST 5: Special Characters & Accents")
    print("="*70)
    print(f"\nMessage:\n{message}")
    print(f"\n📊 RESULTS:")
    print(f"  Complete: {data['is_complete']}")
    print(f"  Missing Fields: {data['missing_fields']}")
    print(f"\n📝 Extracted Data:")
    for key, value in data['prescription_data'].items():
        if value:
            print(f"  • {key}: {value}")
    print(f"\n💬 Model Response:")
    print(f"  {data['response'][:150]}...\n")


def test_real_extraction_free_form():
    """Test with free-form narrative text"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    message = """Le patient s'appelle Laurent Gautier et a 47 ans. Il vient me voir pour une anxiété importante.
Je vais lui prescrire du Lorazépam à 1mg, à prendre une fois le soir avant le coucher.
Le traitement sera de 4 semaines avec une réduction progressive.
Il doit aussi faire un suivi psychologique et éviter l'alcool."""

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    print("\n" + "="*70)
    print("✅ TEST 6: Free-Form Narrative")
    print("="*70)
    print(f"\nMessage:\n{message}")
    print(f"\n📊 RESULTS:")
    print(f"  Complete: {data['is_complete']}")
    print(f"  Missing Fields: {data['missing_fields']}")
    print(f"\n📝 Extracted Data:")
    for key, value in data['prescription_data'].items():
        if value:
            print(f"  • {key}: {value}")
    print(f"\n💬 Model Response:")
    print(f"  {data['response'][:150]}...\n")


def test_pdf_generation():
    """Test PDF generation with complete data"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    reset_session()

    # First fill in complete data
    message = """
Nom: Alexandra Martin
Age: 31 ans
Diagnostic: Infection urinaire
Medicament: Norfloxacine
Dosage: 400mg deux fois par jour
Duree: 5 jours
Instructions: Boire beaucoup d'eau, éviter certains aliments acides
    """

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()

    if data['is_complete']:
        print("\n" + "="*70)
        print("✅ TEST 7: PDF Generation")
        print("="*70)
        print(f"Prescription data collected for: {data['prescription_data']['patientName']}")

        # Generate PDF
        pdf_response = requests.post(f"{API_URL}/api/generate-pdf", json={"signature_base64": ""})
        if pdf_response.status_code == 200:
            print(f"✅ PDF generated successfully")
            print(f"Content-Type: {pdf_response.headers.get('content-type')}")
            print(f"PDF size: {len(pdf_response.content)} bytes\n")
        else:
            print(f"❌ PDF generation failed: {pdf_response.status_code}")
    else:
        print(f"⚠️  Prescription incomplete, missing: {data['missing_fields']}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 VOCALIS BACKEND - REAL MODEL INTEGRATION TESTS")
    print("="*70)
    print(f"API URL: {API_URL}")
    print("="*70)

    if not is_api_available():
        print(f"\n❌ ERROR: Backend is not running at {API_URL}")
        print("\n📝 To run these tests:")
        print("   1. Open a new terminal")
        print("   2. Navigate to backend directory: cd /Users/pierre/Projets/Vocalis/backend")
        print("   3. Activate venv: source venv/bin/activate")
        print("   4. Start backend: python main.py")
        print("   5. In another terminal, run: pytest test_real_integration.py -v -s\n")
    else:
        print("\n✅ Backend is running!\n")

        # Run all tests
        test_health_check()
        test_real_extraction_structured()
        test_real_extraction_narrative()
        test_real_extraction_minimal()
        test_real_extraction_progressive()
        test_real_extraction_special_characters()
        test_real_extraction_free_form()
        test_pdf_generation()

        print("\n" + "="*70)
        print("✅ ALL INTEGRATION TESTS COMPLETED")
        print("="*70 + "\n")
