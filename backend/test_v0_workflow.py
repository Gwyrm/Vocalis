#!/usr/bin/env python3
"""
V0 End-to-End Workflow Test
Tests the core prescription + signature + intervention workflow
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api"

# Test data - use timestamps to ensure unique emails
TIMESTAMP = int(time.time())
DOCTOR_EMAIL = f"doctor_v0_{TIMESTAMP}@example.com"
NURSE_EMAIL = f"nurse_v0_{TIMESTAMP}@example.com"
PASSWORD = "TestPass123"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step, description):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}STEP {step}: {description}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_ok(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_registration():
    """Register doctor and nurse users"""
    print_step(1, "User Registration")

    # Register doctor
    doctor_data = {
        "email": DOCTOR_EMAIL,
        "password": PASSWORD,
        "full_name": "Dr. Sarah Johnson",
        "role": "doctor"
    }

    print_info(f"Registering doctor: {DOCTOR_EMAIL}")
    response = requests.post(f"{API_BASE}/auth/register", json=doctor_data)

    if response.status_code != 200:
        print_error(f"Doctor registration failed: {response.status_code}")
        print(response.text)
        return None, None

    doctor_response = response.json()
    doctor_token = doctor_response["access_token"]
    doctor_id = doctor_response["user"]["id"]
    print_ok(f"Doctor registered: {doctor_id}")

    # Register nurse
    nurse_data = {
        "email": NURSE_EMAIL,
        "password": PASSWORD,
        "full_name": "Nurse Marie Durand",
        "role": "nurse"
    }

    print_info(f"Registering nurse: {NURSE_EMAIL}")
    response = requests.post(f"{API_BASE}/auth/register", json=nurse_data)

    if response.status_code != 200:
        print_error(f"Nurse registration failed: {response.status_code}")
        print(response.text)
        return doctor_token, None

    nurse_response = response.json()
    nurse_token = nurse_response["access_token"]
    print_ok(f"Nurse registered")

    return doctor_token, nurse_token

def test_patient_creation(doctor_token):
    """Create a patient"""
    print_step(2, "Patient Creation")

    patient_data = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "date_of_birth": "1980-01-15",
        "gender": "M",
        "phone": "+33612345678",
        "email": "patient@example.com",
        "address": "123 Rue de Paris, Paris 75001",
        "allergies": ["Penicillin"],
        "chronic_conditions": ["Hypertension"],
        "current_medications": ["Lisinopril 10mg daily"]
    }

    print_info("Creating patient...")
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = requests.post(f"{API_BASE}/patients", json=patient_data, headers=headers)

    if response.status_code != 200:
        print_error(f"Patient creation failed: {response.status_code}")
        print(response.text)
        return None

    patient = response.json()
    patient_id = patient["id"]
    print_ok(f"Patient created: {patient_id}")
    print_info(f"Patient: {patient['first_name']} {patient['last_name']}, {patient['date_of_birth']}")

    return patient_id

def test_prescription_creation(doctor_token, patient_id):
    """Create a prescription"""
    print_step(3, "Prescription Creation (AI-Generated)")

    prescription_data = {
        "patient_id": patient_id,
        "patient_name": "Jean Dupont",
        "patient_age": "44",
        "diagnosis": "Type 2 Diabetes Mellitus",
        "medication": "Metformin",
        "dosage": "500mg",
        "duration": "30 days",
        "special_instructions": "Take with meals, monitor blood glucose"
    }

    print_info("Creating prescription...")
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = requests.post(f"{API_BASE}/prescriptions", json=prescription_data, headers=headers)

    if response.status_code != 200:
        print_error(f"Prescription creation failed: {response.status_code}")
        print(response.text)
        return None

    prescription = response.json()
    prescription_id = prescription["id"]
    print_ok(f"Prescription created: {prescription_id}")
    print_info(f"Status: {prescription['status']}, Signed: {prescription.get('is_signed', False)}")

    return prescription_id

def test_prescription_signing(doctor_token, prescription_id):
    """Sign the prescription (doctor only)"""
    print_step(4, "Prescription Signature (Doctor-Only)")

    # Simple Base64 encoded PNG (1x1 pixel transparent PNG)
    signature_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    sign_data = {
        "signature_base64": signature_b64
    }

    print_info("Signing prescription with doctor signature...")
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = requests.put(
        f"{API_BASE}/prescriptions/{prescription_id}/sign",
        json=sign_data,
        headers=headers
    )

    if response.status_code != 200:
        print_error(f"Prescription signing failed: {response.status_code}")
        print(response.text)
        return False

    prescription = response.json()
    print_ok(f"Prescription signed successfully")
    print_info(f"Status: {prescription['status']}, Signed: {prescription.get('is_signed')}, Time: {prescription.get('doctor_signed_at')}")

    return True

def test_nurse_cannot_sign(nurse_token, prescription_id):
    """Verify nurse cannot sign prescription"""
    print_step(5, "Access Control Test - Nurse Cannot Sign")

    signature_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    sign_data = {
        "signature_base64": signature_b64
    }

    print_info("Attempting to sign as nurse (should fail)...")
    headers = {"Authorization": f"Bearer {nurse_token}"}
    response = requests.put(
        f"{API_BASE}/prescriptions/{prescription_id}/sign",
        json=sign_data,
        headers=headers
    )

    if response.status_code == 403:
        print_ok("Correctly rejected - Nurse cannot sign (403 Forbidden)")
        return True
    else:
        print_error(f"Access control failed - Expected 403, got {response.status_code}")
        print(response.text)
        return False

def test_intervention_creation(doctor_token, prescription_id):
    """Create an intervention for the prescription"""
    print_step(6, "Intervention Creation (Follow-up Task)")

    intervention_data = {
        "prescription_id": prescription_id,
        "intervention_type": "Blood glucose check",
        "description": "Check blood glucose levels and review medication effectiveness",
        "scheduled_date": "2026-03-15T10:00:00",
        "priority": "normal"
    }

    print_info("Creating intervention...")
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = requests.post(f"{API_BASE}/interventions", json=intervention_data, headers=headers)

    if response.status_code != 200:
        print_error(f"Intervention creation failed: {response.status_code}")
        print(response.text)
        return None

    intervention = response.json()
    intervention_id = intervention["id"]
    print_ok(f"Intervention created: {intervention_id}")
    print_info(f"Type: {intervention['intervention_type']}, Status: {intervention['status']}, Priority: {intervention['priority']}")

    return intervention_id

def test_intervention_logging(nurse_token, intervention_id):
    """Log an intervention completion"""
    print_step(7, "Intervention Status Update (Nurse)")

    log_data = {
        "status_change": "scheduled→in_progress",
        "notes": "Patient contacted and visit scheduled for March 15"
    }

    print_info("Logging intervention status update...")
    headers = {"Authorization": f"Bearer {nurse_token}"}
    response = requests.post(
        f"{API_BASE}/interventions/{intervention_id}/log",
        json=log_data,
        headers=headers
    )

    if response.status_code != 200:
        print_error(f"Intervention logging failed: {response.status_code}")
        print(response.text)
        return False

    log = response.json()
    print_ok(f"Intervention logged successfully")
    print_info(f"Notes: {log.get('notes')}")

    return True

def test_list_prescriptions(doctor_token):
    """List all prescriptions"""
    print_step(8, "List Prescriptions")

    print_info("Fetching prescriptions...")
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = requests.get(f"{API_BASE}/prescriptions", headers=headers)

    if response.status_code != 200:
        print_error(f"Failed to list prescriptions: {response.status_code}")
        return

    prescriptions = response.json()
    print_ok(f"Found {len(prescriptions)} prescription(s)")
    for p in prescriptions:
        status_icon = "✓" if p.get("is_signed") else "○"
        print_info(f"{status_icon} {p['patient_name']} - {p['medication']} ({p['status']})")

def main():
    """Run the complete V0 workflow test"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}VOCALIS V0 END-TO-END WORKFLOW TEST{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print_error("Backend health check failed")
            return
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend at {BASE_URL}")
        print_info("Please start the backend: python main.py")
        return

    print_ok("Backend is running")

    # Run tests
    doctor_token, nurse_token = test_registration()
    if not doctor_token or not nurse_token:
        print_error("Registration failed - stopping test")
        return

    patient_id = test_patient_creation(doctor_token)
    if not patient_id:
        print_error("Patient creation failed - stopping test")
        return

    prescription_id = test_prescription_creation(doctor_token, patient_id)
    if not prescription_id:
        print_error("Prescription creation failed - stopping test")
        return

    if not test_prescription_signing(doctor_token, prescription_id):
        print_error("Prescription signing failed - stopping test")
        return

    if not test_nurse_cannot_sign(nurse_token, prescription_id):
        print_error("Access control test failed")
        return

    intervention_id = test_intervention_creation(doctor_token, prescription_id)
    if not intervention_id:
        print_error("Intervention creation failed - stopping test")
        return

    if not test_intervention_logging(nurse_token, intervention_id):
        print_error("Intervention logging failed - stopping test")
        return

    test_list_prescriptions(doctor_token)

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}✓ ALL TESTS PASSED - V0 WORKFLOW IS COMPLETE{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"""
{GREEN}Summary:{RESET}
  • Doctor registered and authenticated
  • Nurse registered and authenticated
  • Patient created in system
  • Prescription generated
  • Prescription signed by doctor (access control verified)
  • Intervention scheduled as follow-up
  • Intervention logged by nurse

{GREEN}Core V0 Features Validated:{RESET}
  ✓ User authentication (doctor + nurse roles)
  ✓ Patient management (simple CRUD)
  ✓ Prescription workflow
  ✓ Doctor-only signature restriction
  ✓ Intervention scheduling & tracking
  ✓ Role-based access control
    """)

if __name__ == "__main__":
    main()
