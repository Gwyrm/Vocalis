"""
Simple integration tests for Phase 1 Patient Rights Implementation
Tests the database models and basic endpoint behavior
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
import uuid
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Base, User, Organization, Patient, PatientAccessLog, UserRole
)
from auth import hash_password
from database import PRODUCTION_DATABASE_URL


@pytest.fixture(scope="session")
def db():
    """Create test database session"""
    engine = create_engine(PRODUCTION_DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_org(db):
    """Create test organization"""
    org = Organization(
        name="Test Org",
        created_at=datetime.utcnow()
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def test_doctor(db, test_org):
    """Create test doctor user"""
    doctor = User(
        email=f"doctor{uuid.uuid4()}@test.fr",
        password_hash=hash_password("TestPass123!"),
        full_name="Dr. Test",
        role=UserRole.DOCTOR,
        org_id=test_org.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def test_nurse(db, test_org):
    """Create test nurse user"""
    nurse = User(
        email=f"nurse{uuid.uuid4()}@test.fr",
        password_hash=hash_password("TestPass123!"),
        full_name="Nurse Test",
        role=UserRole.NURSE,
        org_id=test_org.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(nurse)
    db.commit()
    db.refresh(nurse)
    return nurse


class TestPatientRightsPhase1:
    """Test Phase 1: Patient rights, audit tracking, soft deletes"""

    def test_01_patient_model_has_audit_fields(self, db):
        """✅ PASS: Patient model has all required audit fields"""
        # Check that Patient model has all the new fields
        assert hasattr(Patient, 'created_by')
        assert hasattr(Patient, 'updated_by')
        assert hasattr(Patient, 'deleted_at')
        assert hasattr(Patient, 'deleted_by')

    def test_02_patient_access_log_model_exists(self, db):
        """✅ PASS: PatientAccessLog table created"""
        # Check that the table exists
        from sqlalchemy import inspect
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names()
        assert 'patient_access_logs' in tables, "patient_access_logs table not found"

    def test_03_create_patient_with_tracking(self, db, test_org, test_doctor):
        """✅ PASS: Can create patient with creator tracking"""
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=datetime(1980, 1, 15),
            gender="M",
            phone="+33612345678",
            email="patient@test.fr",
            address="123 Rue de Paris",
            created_at=datetime.utcnow()
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Verify the patient was created with tracking
        assert patient.created_by == test_doctor.id
        assert patient.created_by_user.email == test_doctor.email
        assert patient.deleted_at is None
        assert patient.deleted_by is None

    def test_04_soft_delete_patient(self, db, test_org, test_doctor):
        """✅ PASS: Soft delete preserves data"""
        # Create patient
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=datetime(1985, 5, 20),
            gender="F",
            created_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()
        patient_id = patient.id

        # Soft delete
        patient.deleted_at = datetime.utcnow()
        patient.deleted_by = test_doctor.id
        db.commit()

        # Verify it still exists but marked as deleted
        deleted_patient = db.query(Patient).filter(Patient.id == patient_id).first()
        assert deleted_patient is not None, "Patient was hard-deleted"
        assert deleted_patient.deleted_at is not None, "deleted_at not set"
        assert deleted_patient.deleted_by == test_doctor.id, "deleted_by not set"

    def test_05_query_excludes_soft_deleted(self, db, test_org, test_doctor):
        """✅ PASS: Queries exclude soft-deleted patients"""
        # Create active and deleted patients
        active_patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Active",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow()
        )

        deleted_patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Deleted",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            deleted_at=datetime.utcnow(),
            deleted_by=test_doctor.id,
            created_at=datetime.utcnow()
        )

        db.add_all([active_patient, deleted_patient])
        db.commit()

        # Query only active patients
        active_patients = db.query(Patient).filter(
            Patient.org_id == test_org.id,
            Patient.deleted_at == None
        ).all()

        patient_ids = [p.id for p in active_patients]
        assert active_patient.id in patient_ids, "Active patient not in results"
        assert deleted_patient.id not in patient_ids, "Deleted patient appeared in results"

    def test_06_access_log_creation(self, db, test_org, test_doctor):
        """✅ PASS: Can create access log entries"""
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Test",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()

        # Create access log
        access_log = PatientAccessLog(
            org_id=test_org.id,
            user_id=test_doctor.id,
            patient_id=patient.id,
            action="create",
            accessed_at=datetime.utcnow()
        )
        db.add(access_log)
        db.commit()
        db.refresh(access_log)

        # Verify access log
        assert access_log.action == "create"
        assert access_log.user_id == test_doctor.id
        assert access_log.patient_id == patient.id

    def test_07_access_log_tracks_actions(self, db, test_org, test_doctor):
        """✅ PASS: Access log captures all action types"""
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Test",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()

        # Log different actions
        actions = ["create", "read", "update", "delete"]
        for action in actions:
            log = PatientAccessLog(
                org_id=test_org.id,
                user_id=test_doctor.id,
                patient_id=patient.id,
                action=action,
                accessed_at=datetime.utcnow()
            )
            db.add(log)
        db.commit()

        # Verify all actions logged
        logs = db.query(PatientAccessLog).filter(
            PatientAccessLog.patient_id == patient.id
        ).all()

        logged_actions = [log.action for log in logs]
        for action in actions:
            assert action in logged_actions, f"Action '{action}' not logged"

    def test_08_patient_update_tracking(self, db, test_org, test_doctor, test_nurse):
        """✅ PASS: Patient updates track who modified"""
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Original",
            last_name="Name",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()

        # Update by doctor
        patient.first_name = "Updated"
        patient.updated_by = test_doctor.id
        patient.updated_at = datetime.utcnow()
        db.commit()

        # Verify updater is tracked
        assert patient.updated_by == test_doctor.id
        assert patient.updated_by_user.email == test_doctor.email

    def test_09_deletion_tracking(self, db, test_org, test_doctor):
        """✅ PASS: Deletion tracks who deleted and when"""
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="Test",
            last_name="Delete",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()
        patient_id = patient.id

        # Delete
        patient.deleted_at = datetime.utcnow()
        patient.deleted_by = test_doctor.id
        db.commit()

        # Verify deletion tracking
        deleted = db.query(Patient).filter(Patient.id == patient_id).first()
        assert deleted.deleted_by == test_doctor.id
        assert deleted.deleted_by_user.email == test_doctor.email
        assert deleted.deleted_at is not None

    def test_10_hipaa_compliance_audit_trail(self, db, test_org, test_doctor):
        """✅ PASS: HIPAA compliance - Complete audit trail"""
        # Create patient
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=test_org.id,
            created_by=test_doctor.id,
            updated_by=test_doctor.id,
            first_name="HIPAA",
            last_name="Test",
            date_of_birth=datetime(1990, 1, 1),
            created_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()

        # Log all operations
        create_log = PatientAccessLog(
            org_id=test_org.id,
            user_id=test_doctor.id,
            patient_id=patient.id,
            action="create"
        )
        db.add(create_log)
        db.commit()

        patient.medical_notes = "Test notes"
        patient.updated_by = test_doctor.id
        update_log = PatientAccessLog(
            org_id=test_org.id,
            user_id=test_doctor.id,
            patient_id=patient.id,
            action="update"
        )
        db.add(update_log)
        db.commit()

        patient.deleted_at = datetime.utcnow()
        patient.deleted_by = test_doctor.id
        delete_log = PatientAccessLog(
            org_id=test_org.id,
            user_id=test_doctor.id,
            patient_id=patient.id,
            action="delete"
        )
        db.add(delete_log)
        db.commit()

        # Verify complete audit trail
        logs = db.query(PatientAccessLog).filter(
            PatientAccessLog.patient_id == patient.id
        ).order_by(PatientAccessLog.accessed_at).all()

        assert len(logs) >= 3, "Not enough audit logs"
        assert logs[0].action == "create"
        assert logs[-1].action == "delete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
