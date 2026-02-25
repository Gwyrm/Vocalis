"""SQLAlchemy models for Vocalis"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum, Boolean
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
    patient_visits = relationship("PatientVisit", back_populates="assigned_nurse")

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
    status = Column(String(50), default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="prescriptions")
    created_by_user = relationship("User", back_populates="prescriptions")
    patient_visits = relationship("PatientVisit", back_populates="prescription")


class Device(Base):
    """Medical device/equipment"""
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)

    name = Column(String(255), nullable=False)
    model = Column(String(255))
    serial_number = Column(String(255), unique=True)

    status = Column(String(50), default="available")  # available, assigned, in_use, maintenance
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="devices")
    visit_details = relationship("VisitDetail", back_populates="device")


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
