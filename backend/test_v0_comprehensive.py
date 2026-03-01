"""
Comprehensive Route Testing for Vocalis V0
Tests all major API endpoints with various scenarios
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from database import Base, prod_engine, ProdSessionLocal
from models import User, Organization, UserRole, Patient, Prescription, Intervention, Device

# Create tables
Base.metadata.create_all(bind=prod_engine)

client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def db():
    """Fresh database for each test"""
    Base.metadata.drop_all(bind=prod_engine)
    Base.metadata.create_all(bind=prod_engine)
    db = ProdSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def setup_org_and_users(db):
    """Create organization and test users"""
    # Create org
    org = Organization(name="Test Hospital", address="123 Main St", phone="555-0123")
    db.add(org)
    db.commit()
    
    # Create doctor
    doctor = User(
        email="doctor@test.com",
        full_name="Dr. Test",
        password_hash="hashed_password",
        role=UserRole.DOCTOR,
        org_id=org.id
    )
    db.add(doctor)
    
    # Create nurse
    nurse = User(
        email="nurse@test.com",
        full_name="Nurse Test",
        password_hash="hashed_password",
        role=UserRole.NURSE,
        org_id=org.id
    )
    db.add(nurse)
    db.commit()
    
    return {"org": org, "doctor": doctor, "nurse": nurse}


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_success(self):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "TestPassword123",
                "full_name": "New User",
                "role": "doctor"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@test.com"
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid_email",
                "password": "TestPassword123",
                "full_name": "Test",
                "role": "doctor"
            }
        )
        assert response.status_code == 422
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@test.com",
                "password": "weak",
                "full_name": "Test",
                "role": "doctor"
            }
        )
        assert response.status_code == 400
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@test.com",
                "password": "TestPassword123",
                "full_name": "User 1",
                "role": "doctor"
            }
        )
        
        # Try to register same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@test.com",
                "password": "TestPassword456",
                "full_name": "User 2",
                "role": "nurse"
            }
        )
        assert response.status_code == 400
    
    def test_login_success(self):
        """Test successful login"""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": "login@test.com",
                "password": "TestPassword123",
                "full_name": "Login Test",
                "role": "doctor"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={"email": "login@test.com", "password": "TestPassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "WrongPassword"}
        )
        assert response.status_code == 401
    
    def test_refresh_token(self):
        """Test token refresh"""
        # Register and login
        reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "refresh@test.com",
                "password": "TestPassword123",
                "full_name": "Refresh Test",
                "role": "doctor"
            }
        )
        refresh_token = reg_response.json()["refresh_token"]
        
        # Refresh
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self):
        """Test logout"""
        # Register and get tokens
        reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "logout@test.com",
                "password": "TestPassword123",
                "full_name": "Logout Test",
                "role": "doctor"
            }
        )
        token = reg_response.json()["access_token"]
        refresh_token = reg_response.json()["refresh_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_get_current_user(self):
        """Test get current user"""
        # Register
        reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "currentuser@test.com",
                "password": "TestPassword123",
                "full_name": "Current User",
                "role": "doctor"
            }
        )
        token = reg_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "currentuser@test.com"
        assert data["role"] == "doctor"


# ============================================================================
# PATIENT MANAGEMENT TESTS
# ============================================================================

class TestPatients:
    """Test patient management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for patient tests"""
        # Register a doctor
        self.reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "doctor_patient@test.com",
                "password": "TestPassword123",
                "full_name": "Doctor for Patients",
                "role": "doctor"
            }
        )
        self.token = self.reg_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_patient(self):
        """Test creating a patient"""
        response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "gender": "M",
                "phone": "555-0123",
                "email": "john@test.com",
                "address": "123 Main St",
                "allergies": ["Penicillin"],
                "chronic_conditions": ["Hypertension"],
                "current_medications": ["Lisinopril"],
                "medical_notes": "Test patient"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["allergies"] == ["Penicillin"]
    
    def test_list_patients(self):
        """Test listing patients"""
        # Create a patient first
        client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1985-05-20",
                "gender": "F",
                "allergies": ["Aspirin"],
            }
        )
        
        # List patients
        response = client.get(
            "/api/patients",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["first_name"] == "Jane" for p in data)
    
    def test_get_patient(self):
        """Test getting a patient by ID"""
        # Create patient
        create_response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Bob",
                "last_name": "Johnson",
                "date_of_birth": "1995-12-10",
            }
        )
        patient_id = create_response.json()["id"]
        
        # Get patient
        response = client.get(
            f"/api/patients/{patient_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["first_name"] == "Bob"
    
    def test_update_patient(self):
        """Test updating a patient"""
        # Create patient
        create_response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Alice",
                "last_name": "Williams",
                "date_of_birth": "1988-03-22",
                "allergies": ["Pollen"],
            }
        )
        patient_id = create_response.json()["id"]
        
        # Update patient
        response = client.put(
            f"/api/patients/{patient_id}",
            headers=self.headers,
            json={
                "first_name": "Alice",
                "last_name": "Williams-Johnson",
                "allergies": ["Pollen", "Dust"],
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == "Williams-Johnson"
        assert len(data["allergies"]) == 2
    
    def test_delete_patient(self):
        """Test deleting a patient"""
        # Create patient
        create_response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Charlie",
                "last_name": "Brown",
                "date_of_birth": "1992-07-15",
            }
        )
        patient_id = create_response.json()["id"]
        
        # Delete patient
        response = client.delete(
            f"/api/patients/{patient_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get(
            f"/api/patients/{patient_id}",
            headers=self.headers
        )
        assert response.status_code == 404


# ============================================================================
# PRESCRIPTION TESTS
# ============================================================================

class TestPrescriptions:
    """Test prescription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for prescription tests"""
        # Register doctor
        self.reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "doctor_rx@test.com",
                "password": "TestPassword123",
                "full_name": "Doctor for Rx",
                "role": "doctor"
            }
        )
        self.token = self.reg_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a patient
        self.patient_response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Patient",
                "last_name": "ForRx",
                "date_of_birth": "1990-01-01",
            }
        )
        self.patient_id = self.patient_response.json()["id"]
    
    def test_create_prescription(self):
        """Test creating a prescription"""
        response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRx",
                "patient_age": "34",
                "diagnosis": "Type 2 Diabetes",
                "medication": "Metformin",
                "dosage": "500mg",
                "duration": "30 days",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
        assert data["medication"] == "Metformin"
    
    def test_get_prescription(self):
        """Test getting a prescription"""
        # Create prescription
        create_response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRx",
                "patient_age": "34",
                "diagnosis": "Hypertension",
                "medication": "Lisinopril",
                "dosage": "10mg",
                "duration": "60 days",
            }
        )
        rx_id = create_response.json()["id"]
        
        # Get prescription
        response = client.get(
            f"/api/prescriptions/{rx_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["medication"] == "Lisinopril"
    
    def test_list_prescriptions(self):
        """Test listing prescriptions"""
        # Create multiple prescriptions
        for i in range(2):
            client.post(
                "/api/prescriptions",
                headers=self.headers,
                json={
                    "patient_id": self.patient_id,
                    "patient_name": "Patient ForRx",
                    "patient_age": "34",
                    "diagnosis": f"Condition {i}",
                    "medication": f"Med {i}",
                    "dosage": "100mg",
                    "duration": "30 days",
                }
            )
        
        # List
        response = client.get(
            "/api/prescriptions",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_update_prescription(self):
        """Test updating a prescription"""
        # Create
        create_response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRx",
                "patient_age": "34",
                "diagnosis": "Initial",
                "medication": "InitialMed",
                "dosage": "100mg",
                "duration": "30 days",
            }
        )
        rx_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/api/prescriptions/{rx_id}",
            headers=self.headers,
            json={
                "diagnosis": "Updated",
                "medication": "UpdatedMed",
                "dosage": "200mg",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["medication"] == "UpdatedMed"
        assert data["dosage"] == "200mg"
    
    def test_sign_prescription(self):
        """Test doctor signing a prescription"""
        # Create
        create_response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient ForRx",
                "patient_age": "34",
                "diagnosis": "To Sign",
                "medication": "SignMe",
                "dosage": "50mg",
                "duration": "30 days",
            }
        )
        rx_id = create_response.json()["id"]
        
        # Sign with a signature
        response = client.put(
            f"/api/prescriptions/{rx_id}/sign",
            headers=self.headers,
            json={
                "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_signed"] == True
        assert data["status"] == "signed"


# ============================================================================
# INTERVENTION TESTS
# ============================================================================

class TestInterventions:
    """Test intervention endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for intervention tests"""
        # Register doctor
        self.reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "doctor_int@test.com",
                "password": "TestPassword123",
                "full_name": "Doctor for Interventions",
                "role": "doctor"
            }
        )
        self.token = self.reg_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create patient
        patient_response = client.post(
            "/api/patients",
            headers=self.headers,
            json={
                "first_name": "Patient",
                "last_name": "Int",
                "date_of_birth": "1990-01-01",
            }
        )
        self.patient_id = patient_response.json()["id"]
        
        # Create prescription
        rx_response = client.post(
            "/api/prescriptions",
            headers=self.headers,
            json={
                "patient_id": self.patient_id,
                "patient_name": "Patient Int",
                "patient_age": "34",
                "diagnosis": "Test",
                "medication": "Med",
                "dosage": "100mg",
                "duration": "30 days",
            }
        )
        self.rx_id = rx_response.json()["id"]
    
    def test_create_intervention(self):
        """Test creating an intervention"""
        response = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Blood test",
                "description": "Routine blood work",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "Blood test"
        assert data["status"] == "scheduled"
    
    def test_get_intervention(self):
        """Test getting an intervention"""
        # Create
        create_response = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Follow-up call",
                "description": "Check status",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "high",
            }
        )
        int_id = create_response.json()["id"]
        
        # Get
        response = client.get(
            f"/api/interventions/{int_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "Follow-up call"
    
    def test_list_interventions(self):
        """Test listing interventions"""
        # Create
        client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Test 1",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        
        # List
        response = client.get(
            "/api/interventions",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_update_intervention(self):
        """Test updating an intervention"""
        # Create
        create_response = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "Original",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "low",
            }
        )
        int_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/api/interventions/{int_id}",
            headers=self.headers,
            json={
                "intervention_type": "Updated",
                "priority": "high",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "Updated"
        assert data["priority"] == "high"
    
    def test_log_intervention(self):
        """Test logging an intervention"""
        # Create
        create_response = client.post(
            "/api/interventions",
            headers=self.headers,
            json={
                "prescription_id": self.rx_id,
                "intervention_type": "To Log",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "normal",
            }
        )
        int_id = create_response.json()["id"]
        
        # Log
        response = client.post(
            f"/api/interventions/{int_id}/log",
            headers=self.headers,
            json={
                "status_change": "scheduled→in_progress",
                "notes": "Started intervention",
            }
        )
        assert response.status_code == 200


# ============================================================================
# HEALTH & GENERAL TESTS
# ============================================================================

class TestGeneral:
    """Test general endpoints"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["backend"] == "running"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
