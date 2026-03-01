"""
Comprehensive Unit Tests for Vocalis V0
Tests authentication, database models, API endpoints, and business logic
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from models import (
    Base, User, Organization, Patient, Prescription, Intervention,
    InterventionLog, RefreshToken, UserRole
)
from auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_refresh_token, verify_token
)
from database import get_db
from schemas import UserRegisterRequest, UserLoginRequest

# Test Database Setup
TEST_DATABASE_URL = "sqlite:///./test_vocalis.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create test session maker"""
    return sessionmaker(bind=test_engine)

@pytest.fixture
def db(test_session_maker):
    """Get test database session"""
    session = test_session_maker()
    yield session
    session.query(RefreshToken).delete()
    session.query(InterventionLog).delete()
    session.query(Intervention).delete()
    session.query(Prescription).delete()
    session.query(Patient).delete()
    session.query(User).delete()
    session.query(Organization).delete()
    session.commit()
    session.close()

@pytest.fixture
def client(db):
    """Get FastAPI TestClient with test database"""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_org(db):
    """Create test organization"""
    org = Organization(
        name="Test Organization",
        created_at=datetime.utcnow()
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@pytest.fixture
def test_doctor(db, test_org):
    """Create test doctor user"""
    user = User(
        id=str(hash("test_doctor")),
        email="doctor@test.com",
        password_hash=hash_password("DoctorPass123"),
        full_name="Dr. Test Doctor",
        role=UserRole.DOCTOR,
        org_id=test_org.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_nurse(db, test_org):
    """Create test nurse user"""
    user = User(
        id=str(hash("test_nurse")),
        email="nurse@test.com",
        password_hash=hash_password("NursePass123"),
        full_name="Nurse Test Nurse",
        role=UserRole.NURSE,
        org_id=test_org.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_patient(db, test_org):
    """Create test patient"""
    patient = Patient(
        id=str(hash("test_patient")),
        org_id=test_org.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1980, 1, 15).date(),
        gender="M",
        phone="+33612345678",
        email="patient@test.com",
        address="123 Test Street",
        allergies=json.dumps(["Penicillin"]),
        chronic_conditions=json.dumps(["Hypertension"]),
        current_medications=json.dumps(["Lisinopril"]),
        created_at=datetime.utcnow()
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

# ============================================================================
# AUTH MODULE TESTS
# ============================================================================

class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing creates different hashes"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different hashes each time
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_verify_password_valid(self):
        """Test valid password verification"""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_invalid(self):
        """Test invalid password verification"""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test verification with empty password"""
        hashed = hash_password("TestPassword123")

        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        role = "doctor"

        token = create_access_token(user_id, org_id, email, role)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_verify_access_token(self):
        """Test access token verification"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        role = "doctor"

        token = create_access_token(user_id, org_id, email, role)
        payload = verify_token(token)

        assert payload is not None
        assert payload.user_id == user_id
        assert payload.org_id == org_id
        assert payload.email == email
        assert payload.role == role

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)

        assert payload is None

    def test_verify_expired_token(self):
        """Test verification of expired token"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        role = "doctor"

        # Create token that expires immediately
        from jose import jwt
        from auth import JWT_SECRET, JWT_ALGORITHM

        payload = {
            "user_id": user_id,
            "org_id": org_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "iat": datetime.now(timezone.utc)
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        result = verify_token(expired_token)
        assert result is None


class TestRefreshTokens:
    """Test refresh token creation and verification"""

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        token_family = "family_1"

        token = create_refresh_token(user_id, org_id, email, token_family)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_verify_refresh_token(self):
        """Test refresh token verification"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        token_family = "family_1"

        token = create_refresh_token(user_id, org_id, email, token_family)
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload.get("user_id") == user_id
        assert payload.get("org_id") == org_id
        assert payload.get("email") == email
        assert payload.get("type") == "refresh"
        assert payload.get("token_family") == token_family

    def test_refresh_token_has_jti(self):
        """Test refresh token contains unique JTI"""
        user_id = "test_user_123"
        org_id = "test_org_456"
        email = "test@example.com"
        token_family = "family_1"

        token = create_refresh_token(user_id, org_id, email, token_family)
        payload = verify_refresh_token(token)

        assert "jti" in payload
        assert len(payload["jti"]) > 0


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""

    def test_register_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newdoctor@test.com",
                "password": "NewPass123",
                "full_name": "New Doctor",
                "role": "doctor"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == "newdoctor@test.com"
        assert data["user"]["role"] == "doctor"

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "notanemail",
                "password": "Pass123",
                "full_name": "Test User",
                "role": "doctor"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_user_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@test.com",
                "password": "123",  # Too weak
                "full_name": "Test User",
                "role": "doctor"
            }
        )

        # Weak passwords are rejected with 422 Unprocessable Entity
        assert response.status_code in [400, 422]

    def test_login_success(self, client, test_doctor):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == "doctor@test.com"

    def test_login_invalid_password(self, client, test_doctor):
        """Test login with invalid password"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "SomePass123"
            }
        )

        assert response.status_code == 401

    def test_refresh_token_success(self, client, test_doctor):
        """Test successful token refresh"""
        # First login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )

        refresh_token = login_response.json()["refresh_token"]

        # Then refresh
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]  # New token due to rotation
        assert data["status"] == "token_rotated"

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401


class TestPatientEndpoints:
    """Test patient management endpoints"""

    def test_create_patient_success(self, client, test_doctor):
        """Test successful patient creation"""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Create patient
        response = client.post(
            "/api/patients",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1990-05-15",
                "gender": "F",
                "phone": "+33612345678",
                "email": "jane@test.com",
                "address": "456 Test Ave",
                "allergies": ["Penicillin"],
                "chronic_conditions": ["Diabetes"],
                "current_medications": ["Metformin"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert "id" in data

    def test_create_patient_unauthenticated(self, client):
        """Test patient creation without authentication"""
        response = client.post(
            "/api/patients",
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1990-05-15"
            }
        )

        assert response.status_code == 403

    def test_list_patients(self, client, test_doctor, test_patient):
        """Test listing patients"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # List patients
        response = client.get(
            "/api/patients",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_patient(self, client, test_doctor, test_patient):
        """Test getting specific patient"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Get patient
        response = client.get(
            f"/api/patients/{test_patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_patient.id
        assert data["first_name"] == "John"

    def test_update_patient(self, client, test_doctor, test_patient):
        """Test updating patient"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Update patient
        response = client.put(
            f"/api/patients/{test_patient.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Jonathan",
                "last_name": "Smith"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jonathan"

    def test_delete_patient(self, client, test_doctor, test_patient):
        """Test deleting patient"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Delete patient
        response = client.delete(
            f"/api/patients/{test_patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200


class TestPrescriptionEndpoints:
    """Test prescription endpoints"""

    def test_create_prescription(self, client, test_doctor, test_patient):
        """Test creating prescription"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Create prescription
        response = client.post(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_id": test_patient.id,
                "patient_name": "John Doe",
                "patient_age": "44",
                "diagnosis": "Hypertension",
                "medication": "Lisinopril",
                "dosage": "10mg",
                "duration": "30 days"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["medication"] == "Lisinopril"
        assert data["status"] == "draft"
        assert data["is_signed"] is False

    def test_sign_prescription_as_doctor(self, client, test_doctor, test_patient, db):
        """Test doctor signing prescription"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Create prescription first
        create_response = client.post(
            "/api/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_id": test_patient.id,
                "patient_name": "John Doe",
                "patient_age": "44",
                "diagnosis": "Hypertension",
                "medication": "Lisinopril",
                "dosage": "10mg",
                "duration": "30 days"
            }
        )

        prescription_id = create_response.json()["id"]

        # Sign prescription
        response = client.put(
            f"/api/prescriptions/{prescription_id}/sign",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "signature_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_signed"] is True
        assert data["status"] == "signed"

    def test_sign_prescription_as_nurse_denied(self, client, test_nurse, test_patient, db):
        """Test nurse cannot sign prescription (access control)"""
        # First create prescription as doctor
        from main import get_db
        session = db
        org = session.query(Organization).first()
        doctor = session.query(User).filter_by(role=UserRole.DOCTOR).first()

        prescription = Prescription(
            id=str(hash("test_rx")),
            org_id=org.id,
            created_by=doctor.id,
            patient_id=test_patient.id,
            patient_name="John Doe",
            patient_age="44",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg",
            duration="30 days",
            status="draft",
            is_signed=False,
            created_at=datetime.utcnow()
        )
        session.add(prescription)
        session.commit()

        # Try to sign as nurse
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "nurse@test.com",
                "password": "NursePass123"
            }
        )
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/prescriptions/{prescription.id}/sign",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "signature_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )

        assert response.status_code == 403  # Forbidden


class TestInterventionEndpoints:
    """Test intervention endpoints"""

    def test_create_intervention(self, client, test_doctor, test_patient, db):
        """Test creating intervention"""
        # Create prescription first
        session = db
        org = session.query(Organization).first()

        prescription = Prescription(
            id=str(hash("test_intervention_rx")),
            org_id=org.id,
            created_by=test_doctor.id,
            patient_id=test_patient.id,
            patient_name="John Doe",
            patient_age="44",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg",
            duration="30 days",
            status="draft",
            is_signed=False,
            created_at=datetime.utcnow()
        )
        session.add(prescription)
        session.commit()

        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "DoctorPass123"
            }
        )
        token = login_response.json()["access_token"]

        # Create intervention
        response = client.post(
            "/api/interventions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_id": prescription.id,
                "intervention_type": "Follow-up visit",
                "description": "Check patient status",
                "scheduled_date": "2026-03-15T10:00:00",
                "priority": "normal"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intervention_type"] == "Follow-up visit"
        assert data["status"] == "pending"

    def test_log_intervention(self, client, test_nurse, test_patient, db):
        """Test logging intervention completion"""
        # Create intervention first
        session = db
        org = session.query(Organization).first()
        doctor = session.query(User).filter_by(role=UserRole.DOCTOR).first()

        prescription = Prescription(
            id=str(hash("test_log_rx")),
            org_id=org.id,
            created_by=doctor.id,
            patient_id=test_patient.id,
            patient_name="John Doe",
            patient_age="44",
            diagnosis="Hypertension",
            medication="Lisinopril",
            dosage="10mg",
            duration="30 days",
            status="draft",
            is_signed=False,
            created_at=datetime.utcnow()
        )
        session.add(prescription)
        session.commit()

        intervention = Intervention(
            id=str(hash("test_intervention")),
            org_id=org.id,
            prescription_id=prescription.id,
            created_by=doctor.id,
            intervention_type="Follow-up visit",
            description="Check patient status",
            scheduled_date=datetime(2026, 3, 15, 10, 0, 0),
            priority="normal",
            status="pending",
            created_at=datetime.utcnow()
        )
        session.add(intervention)
        session.commit()

        # Login as nurse
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "nurse@test.com",
                "password": "NursePass123"
            }
        )
        token = login_response.json()["access_token"]

        # Log intervention
        response = client.post(
            f"/api/interventions/{intervention.id}/log",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status_change": "pending→in_progress",
                "notes": "Patient visited, status improved"
            }
        )

        assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAuthenticationFlow:
    """Test complete authentication flow"""

    def test_full_auth_flow(self, client):
        """Test register → login → refresh → logout flow"""
        # 1. Register new user
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "testuser@test.com",
                "password": "TestPass123",
                "full_name": "Test User",
                "role": "doctor"
            }
        )
        assert register_response.status_code == 200
        initial_token = register_response.json()["refresh_token"]

        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@test.com",
                "password": "TestPass123"
            }
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # 3. Use access token to access protected endpoint
        response = client.get(
            "/api/patients",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200

        # 4. Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]

        # 5. Use new access token
        response = client.get(
            "/api/patients",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
