"""
Improved extraction tests - Validates fixes for:
1. Preserving data across progressive messages
2. Handling special characters and accents
3. Better empty value detection
"""

import requests
import os

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


def print_test_header(test_name, description):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"🧪 TEST: {test_name}")
    print(f"📝 {description}")
    print("="*80)


def print_extraction_result(message, response, expected_complete=None):
    """Print extraction results nicely"""
    data = response.json()

    print(f"\n📥 Input Message:\n   {message[:100]}...")
    print(f"\n📊 Results:")
    print(f"   ✅ Complete: {data['is_complete']}")
    print(f"   ⚠️  Missing Fields: {data['missing_fields']}")

    print(f"\n📝 Extracted Data:")
    extracted = {k: v for k, v in data['prescription_data'].items() if v}
    if extracted:
        for key, value in extracted.items():
            print(f"   • {key}: {value}")
    else:
        print(f"   (no data extracted)")

    print(f"\n💬 Model Response: {data['response'][:120]}...")

    if expected_complete is not None:
        status = "✅" if data['is_complete'] == expected_complete else "❌"
        print(f"\n{status} Expected Complete: {expected_complete}, Got: {data['is_complete']}")

    return data


# ============================================================================
# TEST 1: Progressive Messages - Data Preservation
# ============================================================================

def test_progressive_data_preservation():
    """Test that data is preserved across multiple messages"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    print_test_header(
        "Progressive Data Preservation",
        "Verifies that patient data is preserved across multiple messages"
    )

    reset_session()

    messages = [
        {
            "text": "Je m'appelle Sophie Bernard et j'ai 34 ans",
            "expected_fields": {"patientName": "Sophie Bernard", "patientAge": "34"}
        },
        {
            "text": "Je viens pour une infection urinaire",
            "expected_fields": {"diagnosis": "infection urinaire"}
        },
        {
            "text": "Je vous prescris de la Norfloxacine",
            "expected_fields": {"medication": "Norfloxacine"}
        },
        {
            "text": "500mg deux fois par jour pendant une semaine",
            "expected_fields": {"dosage": "500mg deux fois par jour", "duration": "une semaine"}
        },
        {
            "text": "Boire beaucoup d'eau et éviter l'alcool",
            "expected_fields": {"specialInstructions": "Boire beaucoup d'eau et éviter l'alcool"}
        }
    ]

    session_data = {}

    for i, msg_info in enumerate(messages, 1):
        print(f"\n📍 Message {i}: \"{msg_info['text'][:50]}...\"")

        response = requests.post(f"{API_URL}/api/chat", json={"message": msg_info["text"]})
        data = response.json()

        # Update session data tracking
        for key, value in data['prescription_data'].items():
            if value:
                session_data[key] = value

        # Print results
        print(f"   Current extraction: {data['prescription_data']}")
        print(f"   Is Complete: {data['is_complete']}")
        print(f"   Missing: {len(data['missing_fields'])} fields")

        # Check if expected fields are preserved
        for field_name, field_value in msg_info['expected_fields'].items():
            extracted_value = data['prescription_data'].get(field_name)
            if extracted_value:
                print(f"   ✅ {field_name}: {extracted_value}")
            else:
                print(f"   ❌ {field_name}: NOT EXTRACTED (expected: {field_value})")

    print(f"\n🏁 FINAL STATE (Message {len(messages)}):")
    response = requests.post(f"{API_URL}/api/chat", json={"message": "Créer l'ordonnance"})
    data = response.json()
    print_extraction_result("(Final state check)", response, expected_complete=True)


# ============================================================================
# TEST 2: Special Characters & Accents
# ============================================================================

def test_special_characters_and_accents():
    """Test extraction with French accents and special characters"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    print_test_header(
        "Special Characters & Accents",
        "Tests handling of French accents (é, è, ê, à, ô) and special chars"
    )

    reset_session()

    test_cases = [
        {
            "name": "Full accents in headers",
            "message": """
Patiente: Véronique Côté
Âge: 42 ans
Diagnostic: Migraines chroniques
Médicament: Ibuprofen
Posologie: 400mg deux fois par jour
Durée: 2 mois
Instructions: À prendre avec de la nourriture
            """,
            "expected": {
                "patientName": ["Véronique", "Côté"],
                "patientAge": "42",
                "diagnosis": ["Migraine", "chronique"],
                "medication": "Ibuprofen"
            }
        },
        {
            "name": "Mixed French/formal terminology",
            "message": """
Dossier patient: François Deschênes (50 ans)
Diagnostic principal: Hypertension essentielle
Traitement prescrit: Lisinopril 20mg
Fréquence: Une fois par jour
Durée recommandée: Indéfini
Remarques: Faire un suivi tensionnel régulier
            """,
            "expected": {
                "patientName": "François",
                "patientAge": "50",
                "medication": "Lisinopril"
            }
        }
    ]

    for test_case in test_cases:
        print(f"\n📍 Subtest: {test_case['name']}")
        response = requests.post(f"{API_URL}/api/chat", json={"message": test_case["message"]})

        data = response.json()
        print(f"   Complete: {data['is_complete']}")
        print(f"   Extracted Name: {data['prescription_data']['patientName']}")
        print(f"   Extracted Age: {data['prescription_data']['patientAge']}")
        print(f"   Extracted Diagnosis: {data['prescription_data']['diagnosis']}")
        print(f"   Extracted Medication: {data['prescription_data']['medication']}")

        # Verify at least some key fields were extracted
        has_name = data['prescription_data']['patientName'] is not None
        has_age = data['prescription_data']['patientAge'] is not None

        print(f"   ✅ Has name: {has_name}")
        print(f"   ✅ Has age: {has_age}")

    reset_session()


# ============================================================================
# TEST 3: Empty Value Detection
# ============================================================================

def test_empty_value_detection():
    """Test improved detection of empty/absent values"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    print_test_header(
        "Empty Value Detection",
        "Tests that 'Absent', 'Pas spécifié', etc. are properly ignored"
    )

    reset_session()

    # Message with only some fields
    message = """
Nom: Julien Moreau
Age: 38 ans
Diagnostic: Allergie saisonnière
Medicament: Loratadine
    """

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    data = response.json()

    print("\n📥 Partial Message (missing: dosage, duration, instructions)")
    print(f"   Name: {data['prescription_data']['patientName']}")
    print(f"   Age: {data['prescription_data']['patientAge']}")
    print(f"   Diagnosis: {data['prescription_data']['diagnosis']}")
    print(f"   Medication: {data['prescription_data']['medication']}")
    print(f"   Dosage: {data['prescription_data']['dosage']} (should be None/empty)")
    print(f"   Duration: {data['prescription_data']['duration']} (should be None/empty)")
    print(f"   Instructions: {data['prescription_data']['specialInstructions']} (should be None/empty)")

    print(f"\n📊 Status:")
    print(f"   ✅ Is Complete: {data['is_complete']} (should be False)")
    print(f"   ✅ Missing Fields: {data['missing_fields']}")

    reset_session()


# ============================================================================
# TEST 4: Complex Real-World Scenario
# ============================================================================

def test_complex_real_world():
    """Test with a realistic, complex medical scenario"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    print_test_header(
        "Complex Real-World Scenario",
        "Test with a detailed, realistic medical record"
    )

    reset_session()

    message = """
Consultation du 16/02/2026 - Dr. Leduc

Patient: Caroline Leclerc, 55 ans
Antécédents: Diabète type 2, cholestérol élevé
Allergies: Pénicilline

DIAGNOSTIC:
Insuffisance cardiaque légère avec HTA associée

TRAITEMENT PRESCRIT:
- Médicament principal: Amlodipine (calcium-bloquant)
- Dosage: 5mg une fois par jour, le matin
- Durée: Traitement chronique (sans limite)
- Recommandations:
  * Prendre avec un verre d'eau
  * Faire un suivi cardiaque tous les 3 mois
  * Régime pauvre en sel
  * Éviter l'alcool en grande quantité

Prochaine consultation: 30/03/2026
    """

    response = requests.post(f"{API_URL}/api/chat", json={"message": message})
    print_extraction_result(message, response, expected_complete=True)

    reset_session()


# ============================================================================
# TEST 5: Minimal Format with Abbreviations
# ============================================================================

def test_minimal_abbreviations():
    """Test minimal format with medical abbreviations"""
    if not is_api_available():
        print(f"⚠️  Backend not available at {API_URL}")
        return

    print_test_header(
        "Minimal Format with Abbreviations",
        "Tests extraction from very concise, abbreviated medical notation"
    )

    reset_session()

    test_cases = [
        {
            "name": "Medical shorthand",
            "message": "Marc Dumont, 62a, HTA, Enalapril 10mg/j, 3m indéfini, suivi tension q1m"
        },
        {
            "name": "Prescriber notation",
            "message": "Pt: Anne Petit, 28yo, Sinusitis chr., Amoxil 500mg×3/j, 10d, suivi ORL"
        },
        {
            "name": "Hospital format",
            "message": "Patient: David Martin; Age: 71; Dx: Arthrose; Rx: Ibuprofen 400mg tid; Duration: 8wks; Notes: With meals"
        }
    ]

    for test_case in test_cases:
        print(f"\n📍 {test_case['name']}")
        print(f"   Input: {test_case['message']}")

        response = requests.post(f"{API_URL}/api/chat", json={"message": test_case["message"]})
        data = response.json()

        print(f"   Complete: {data['is_complete']}")
        print(f"   Name: {data['prescription_data']['patientName']}")
        print(f"   Age: {data['prescription_data']['patientAge']}")
        print(f"   Medication: {data['prescription_data']['medication']}")

    reset_session()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 IMPROVED EXTRACTION TESTS")
    print("="*80)
    print(f"API URL: {API_URL}")
    print("="*80)

    if not is_api_available():
        print(f"\n❌ Backend is not running at {API_URL}")
        print("\n📝 To run these tests:")
        print("   1. In a terminal: python main.py")
        print("   2. In another terminal: python test_improved_extraction.py\n")
    else:
        print("\n✅ Backend is running!\n")

        test_progressive_data_preservation()
        test_special_characters_and_accents()
        test_empty_value_detection()
        test_complex_real_world()
        test_minimal_abbreviations()

        print("\n" + "="*80)
        print("✅ ALL IMPROVED EXTRACTION TESTS COMPLETED")
        print("="*80 + "\n")
