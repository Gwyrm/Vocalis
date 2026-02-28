"""SQLAlchemy models for Vocalis"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base
import enum


class Organization(Base):
    """Healthcare organization (clinic, hospital, etc.)"""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization")
    prescriptions = relationship("Prescription", back_populates="organization")
    devices = relationship("Device", back_populates="organization")


class UserRole(str, enum.Enum):
    """User role enum"""
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"


class User(Base):
    """User (doctor or nurse)"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    prescriptions = relationship("Prescription", back_populates="created_by_user")
    patient_visits = relationship("PatientVisit", back_populates="nurse")

    # Unique constraint on email per organization
    __table_args__ = (
        # We'll add unique constraint via index: (org_id, email)
    )


class Prescription(Base):
    """Medical prescription for device delivery"""
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=True)

    # Patient information
    patient_name = Column(String(255), nullable=False)
    patient_age = Column(String(50), nullable=False)
    diagnosis = Column(Text)

    # Device/medication information
    medication = Column(String(255), nullable=False)
    dosage = Column(String(255), nullable=False)
    duration = Column(String(255), nullable=False)
    special_instructions = Column(Text)

    # Status
    status = Column(String(50), default="draft")  # draft, signed, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)

    # Doctor Signature (REQUIRED for validity)
    doctor_signature = Column(Text, nullable=True)  # Base64 encoded PNG signature image
    doctor_signed_at = Column(DateTime, nullable=True)  # Timestamp when doctor signed
    is_signed = Column(Boolean, default=False)  # Quick flag for validation

    # Relationships
    organization = relationship("Organization", back_populates="prescriptions")
    created_by_user = relationship("User", back_populates="prescriptions")
    patient = relationship("Patient", back_populates="prescriptions")
    patient_visits = relationship("PatientVisit", back_populates="prescription")
    devices = relationship("PrescriptionDevice", back_populates="prescription", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionDevice(Base):
    """Link between prescriptions and devices to be delivered"""
    __tablename__ = "prescription_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id = Column(String(36), ForeignKey("prescriptions.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)

    quantity = Column(Integer, default=1)
    instructions = Column(Text, nullable=True)  # Device-specific instructions
    priority = Column(String(50), default="normal")  # normal, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prescription = relationship("Prescription", back_populates="devices")
    device = relationship("Device", back_populates="prescriptions")


class Device(Base):
    """Medical device/equipment"""
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)

    name = Column(String(255), nullable=False)
    model = Column(String(255))
    serial_number = Column(String(255), unique=True)
    description = Column(Text, nullable=True)  # Device description/instructions

    status = Column(String(50), default="available")  # available, assigned, in_use, maintenance, returned
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="devices")
    visit_details = relationship("VisitDetail", back_populates="device")
    prescriptions = relationship("PrescriptionDevice", back_populates="device", cascade="all, delete-orphan")


class PatientVisit(Base):
    """Visit to patient home for device delivery"""
    __tablename__ = "patient_visits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id"), nullable=False)
    assigned_nurse = Column(String(36), ForeignKey("users.id"), nullable=False)

    patient_address = Column(String(500), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)

    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prescription = relationship("Prescription", back_populates="patient_visits")
    nurse = relationship("User", back_populates="patient_visits")
    visit_details = relationship("VisitDetail", back_populates="patient_visit", uselist=False)


class VisitDetail(Base):
    """Details of a completed patient visit"""
    __tablename__ = "visit_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id = Column(String(36), ForeignKey("patient_visits.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"))

    # Device installation tracking
    device_serial_installed = Column(String(255), nullable=True)  # Actual serial of device installed
    installation_confirmed = Column(Boolean, default=False)  # Nurse confirmed installation
    installation_timestamp = Column(DateTime, nullable=True)

    # Visit completion details
    nurse_notes = Column(Text)
    patient_signature = Column(Text)  # Base64 encoded signature
    photos = Column(Text)  # JSON array of photo file paths

    completed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient_visit = relationship("PatientVisit", back_populates="visit_details")
    device = relationship("Device", back_populates="visit_details")


class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))

    action = Column(String(255), nullable=False)  # created, updated, deleted, viewed
    resource_type = Column(String(100), nullable=False)  # prescription, visit, device
    resource_id = Column(String(36))

    changes = Column(Text)  # JSON object of changes
    timestamp = Column(DateTime, default=datetime.utcnow)


class NurseLocation(Base):
    """GPS tracking for nurses in field"""
    __tablename__ = "nurse_locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    nurse_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)  # Accuracy radius in meters
    visit_id = Column(String(36), ForeignKey("patient_visits.id"))  # Linked visit if at patient home

    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    nurse = relationship("User")
    visit = relationship("PatientVisit")


class PhotoAttachment(Base):
    """Photos attached to patient visits"""
    __tablename__ = "photo_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id = Column(String(36), ForeignKey("patient_visits.id"), nullable=False)

    file_path = Column(String(500), nullable=False)  # Local file path or S3 URL
    caption = Column(String(500))  # e.g., "Before setup", "After setup"
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100), default="image/jpeg")

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    visit = relationship("PatientVisit")


class DeviceStatus(Base):
    """Track device status changes over time"""
    __tablename__ = "device_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    visit_id = Column(String(36), ForeignKey("patient_visits.id"))

    old_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"))  # Which user made change
    reason = Column(String(255))  # Why status changed

    changed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship("Device")
    visit = relationship("PatientVisit")
    user = relationship("User")


class Patient(Base):
    """Patient information"""
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)

    # Personal info
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10))  # M, F, Other
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(String(500))  # Street address, city, postal code

    # Medical info
    allergies = Column(Text)  # JSON array of allergy objects
    chronic_conditions = Column(Text)  # JSON array of conditions
    current_medications = Column(Text)  # JSON array of current meds
    medical_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    prescriptions = relationship("Prescription", back_populates="patient")


class Medication(Base):
    """Medication database"""
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Drug info
    name = Column(String(255), nullable=False, unique=True)
    generic_name = Column(String(255))
    category = Column(String(100))  # Antibiotic, Antihypertensive, etc.

    # Dosage info
    available_dosages = Column(Text)  # JSON array of available strengths
    unit = Column(String(50))  # mg, mcg, ml, etc.
    min_dosage = Column(Float)
    max_dosage = Column(Float)

    # Restrictions
    min_age = Column(Integer)  # Minimum age in years
    max_age = Column(Integer)  # Maximum age in years (null = no max)
    contraindications = Column(Text)  # JSON array of conditions to avoid

    # Clinical info
    description = Column(Text)
    side_effects = Column(Text)  # JSON array

    created_at = Column(DateTime, default=datetime.utcnow)


class MedicationInteraction(Base):
    """Drug-drug interactions"""
    __tablename__ = "medication_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    medication1_id = Column(String(255), nullable=False)  # Medication name
    medication2_id = Column(String(255), nullable=False)  # Medication name

    # Interaction severity: low, moderate, high, contraindicated
    severity = Column(String(50), nullable=False)

    # Description
    description = Column(Text)
    recommendation = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class DrugAllergy(Base):
    """Patient drug allergies"""
    __tablename__ = "drug_allergies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)

    medication_name = Column(String(255), nullable=False)
    reaction_severity = Column(String(50))  # mild, moderate, severe
    reaction_description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")


class OfflineQueue(Base):
    """Queue for offline-first mobile sync"""
    __tablename__ = "offline_queue"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    action = Column(String(50), nullable=False)  # create, update, delete
    resource_type = Column(String(100), nullable=False)  # prescription, visit, location
    resource_id = Column(String(36))

    payload = Column(Text)  # JSON payload of the action
    status = Column(String(50), default="pending")  # pending, synced, failed
    attempted_at = Column(DateTime)
    synced_at = Column(DateTime)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class Intervention(Base):
    """Planned intervention/follow-up action for a prescription"""
    __tablename__ = "interventions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Intervention details
    intervention_type = Column(String(255), nullable=False)  # e.g., "Blood test", "Follow-up call"
    description = Column(Text)  # Detailed description
    scheduled_date = Column(DateTime, nullable=False)  # When intervention should occur
    priority = Column(String(50), default="normal")  # low, normal, high

    # Status tracking
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    prescription = relationship("Prescription")
    created_by_user = relationship("User")
    logs = relationship("InterventionLog", back_populates="intervention", cascade="all, delete-orphan")


class InterventionLog(Base):
    """Log entries for intervention completion/status changes"""
    __tablename__ = "intervention_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    intervention_id = Column(String(36), ForeignKey("interventions.id"), nullable=False)
    logged_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # What changed
    status_change = Column(String(255))  # e.g., "scheduled→in_progress"
    notes = Column(Text)  # Intervention notes/findings
    logged_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    intervention = relationship("Intervention", back_populates="logs")
    logged_by_user = relationship("User")
    documents = relationship("InterventionDocument", back_populates="log", cascade="all, delete-orphan")


class InterventionDocument(Base):
    """Documents attached to intervention logs (photos, results, etc.)"""
    __tablename__ = "intervention_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    log_id = Column(String(36), ForeignKey("intervention_logs.id"), nullable=False)

    # Document details
    document_type = Column(String(50), default="note")  # note, photo, result, other
    file_path = Column(String(500), nullable=False)  # Local path or S3 URL
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100))  # e.g., "image/jpeg", "application/pdf"
    file_size = Column(Integer)  # Size in bytes
    caption = Column(String(500))  # Description of document

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    log = relationship("InterventionLog", back_populates="documents")
