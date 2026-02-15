#!/usr/bin/env python3
"""
Test script to verify data extraction functionality
"""
import json
from main import (
    extract_prescription_data_from_message,
    build_info_request_prompt,
    PrescriptionData,
    llm
)

def test_extraction():
    """Test extraction with real LLM"""
    if llm is None:
        print("ERROR: Model not loaded!")
        return

    print("=" * 60)
    print("Testing Prescription Data Extraction")
    print("=" * 60)
    print()

    # Test 1: Patient name and age
    print("[Test 1] Extracting patient name and age")
    print("-" * 60)
    data1 = PrescriptionData()
    message1 = "Je m'appelle Jean Dupont et j'ai 45 ans"
    print(f"Input: {message1}")
    result1 = extract_prescription_data_from_message(message1, data1)
    print(f"Result:")
    print(f"  - patientName: {result1.patientName}")
    print(f"  - patientAge: {result1.patientAge}")
    print()

    # Test 2: Diagnosis and medication
    print("[Test 2] Extracting diagnosis and medication")
    print("-" * 60)
    data2 = PrescriptionData(patientName="Jean Dupont", patientAge="45 ans")
    message2 = "Le patient a une hypertension artérielle. Prescrire du Lisinopril 10mg"
    print(f"Input: {message2}")
    result2 = extract_prescription_data_from_message(message2, data2)
    print(f"Result:")
    print(f"  - diagnosis: {result2.diagnosis}")
    print(f"  - medication: {result2.medication}")
    print()

    # Test 3: Dosage and duration
    print("[Test 3] Extracting dosage and duration")
    print("-" * 60)
    data3 = PrescriptionData(
        patientName="Jean Dupont",
        patientAge="45 ans",
        diagnosis="Hypertension",
        medication="Lisinopril"
    )
    message3 = "Une fois par jour, le matin, pour 3 mois"
    print(f"Input: {message3}")
    result3 = extract_prescription_data_from_message(message3, data3)
    print(f"Result:")
    print(f"  - dosage: {result3.dosage}")
    print(f"  - duration: {result3.duration}")
    print()

    # Test 4: Complete data
    print("[Test 4] Complete data extraction")
    print("-" * 60)
    data4 = PrescriptionData()
    message4 = "Patient: Marie Dupont, 50 ans, diabète type 2, Metformine 500mg, deux fois par jour avec les repas, 6 mois, signaler tout symptôme"
    print(f"Input: {message4}")
    result4 = extract_prescription_data_from_message(message4, data4)
    print(f"Result:")
    print(f"  - patientName: {result4.patientName}")
    print(f"  - patientAge: {result4.patientAge}")
    print(f"  - diagnosis: {result4.diagnosis}")
    print(f"  - medication: {result4.medication}")
    print(f"  - dosage: {result4.dosage}")
    print(f"  - duration: {result4.duration}")
    print(f"  - specialInstructions: {result4.specialInstructions}")
    print()

    # Test 5: Missing fields check
    print("[Test 5] Missing fields validation")
    print("-" * 60)
    print(f"Is complete: {result4.is_complete()}")
    print(f"Missing fields: {result4.get_missing_required_fields()}")
    print()

    # Test 6: Build guidance prompt
    print("[Test 6] Building guidance prompt")
    print("-" * 60)
    data5 = PrescriptionData(patientName="Jean")
    prompt = build_info_request_prompt(data5, "Je m'appelle Jean")
    print("Prompt preview (first 200 chars):")
    print(prompt[:200])
    print()

    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_extraction()
