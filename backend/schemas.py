"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from models import UserRole


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: UserRole


class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """Current user information"""
    id: str
    email: str
    full_name: str
    role: UserRole
    org_id: str


# ============================================================================
# Prescription Schemas
# ============================================================================

class PrescriptionCreate(BaseModel):
    """Create prescription request"""
    patient_name: str
    patient_age: str
    diagnosis: str
    medication: str
    dosage: str
    duration: str
    special_instructions: Optional[str] = None


class PrescriptionUpdate(BaseModel):
    """Update prescription request"""
    patient_name: Optional[str] = None
    patient_age: Optional[str] = None
    diagnosis: Optional[str] = None
    medication: Optional[str] = None
    dosage: Optional[str] = None
    duration: Optional[str] = None
    special_instructions: Optional[str] = None
    status: Optional[str] = None


class PrescriptionResponse(BaseModel):
    """Prescription response"""
    id: str
    patient_name: str
    patient_age: str
    diagnosis: str
    medication: str
    dosage: str
    duration: str
    special_instructions: Optional[str]
    status: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class PrescriptionListResponse(BaseModel):
    """Prescription list response"""
    id: str
    patient_name: str
    diagnosis: str
    medication: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Organization Schemas
# ============================================================================

class OrganizationCreate(BaseModel):
    """Create organization request"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Organization response"""
    id: str
    name: str
    address: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Device Schemas
# ============================================================================

class DeviceCreate(BaseModel):
    """Create device request"""
    name: str
    model: Optional[str] = None
    serial_number: str


class DeviceResponse(BaseModel):
    """Device response"""
    id: str
    name: str
    model: Optional[str]
    serial_number: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Patient Visit Schemas
# ============================================================================

class PatientVisitCreate(BaseModel):
    """Create patient visit (doctor assigns nurse)"""
    prescription_id: str
    assigned_nurse: str  # nurse user ID
    patient_address: str
    scheduled_date: datetime


class PatientVisitUpdate(BaseModel):
    """Update patient visit"""
    status: Optional[str] = None  # pending, in_progress, completed, cancelled
    patient_address: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class VisitCompleteRequest(BaseModel):
    """Mark visit as completed with details"""
    nurse_notes: str
    device_serial_installed: Optional[str] = None
    patient_signature: Optional[str] = None  # Base64 encoded signature


class PatientVisitListResponse(BaseModel):
    """Patient visit list response"""
    id: str
    prescription_id: str
    patient_name: str  # From linked prescription
    diagnosis: str  # From linked prescription
    patient_address: str
    scheduled_date: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PatientVisitDetailResponse(BaseModel):
    """Patient visit detail response"""
    id: str
    prescription_id: str
    assigned_nurse: str
    patient_address: str
    scheduled_date: datetime
    status: str
    created_at: datetime

    # Linked prescription data
    patient_name: str
    patient_age: str
    diagnosis: str
    medication: str
    dosage: str
    duration: str
    special_instructions: Optional[str]

    # Visit completion details (if completed)
    nurse_notes: Optional[str] = None
    device_serial_installed: Optional[str] = None
    patient_signature: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# GPS Location Schemas
# ============================================================================

class NurseLocationCreate(BaseModel):
    """Record nurse GPS location"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    visit_id: Optional[str] = None


class NurseLocationResponse(BaseModel):
    """Nurse location response"""
    id: str
    nurse_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float]
    recorded_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Photo Attachment Schemas
# ============================================================================

class PhotoResponse(BaseModel):
    """Photo attachment response"""
    id: str
    file_path: str
    caption: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Device Inventory Schemas
# ============================================================================

class DeviceCreate(BaseModel):
    """Create device (already defined above, reusing)"""
    name: str
    model: Optional[str] = None
    serial_number: str


class DeviceUpdateStatus(BaseModel):
    """Update device status"""
    status: str  # available, assigned, in_use, maintenance, returned
    reason: Optional[str] = None
    visit_id: Optional[str] = None


class DeviceListResponse(BaseModel):
    """Device with status info"""
    id: str
    name: str
    model: Optional[str]
    serial_number: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Analytics Schemas
# ============================================================================

class VisitAnalytics(BaseModel):
    """Visit completion analytics"""
    total_visits: int
    completed_visits: int
    pending_visits: int
    in_progress_visits: int
    completion_rate: float  # percentage
    average_visit_duration_minutes: float


class DeviceAnalytics(BaseModel):
    """Device usage analytics"""
    total_devices: int
    available_devices: int
    in_use_devices: int
    maintenance_devices: int
    device_utilization_rate: float  # percentage


class NurseAnalytics(BaseModel):
    """Nurse performance analytics"""
    nurse_id: str
    nurse_name: str
    total_visits: int
    completed_visits: int
    average_visit_duration_minutes: float
    completion_rate: float


# ============================================================================
# Offline Sync Schemas
# ============================================================================

class OfflineQueueItem(BaseModel):
    """Item in offline sync queue"""
    id: str
    action: str  # create, update, delete
    resource_type: str  # prescription, visit, device, location, photo
    resource_id: Optional[str]
    payload: dict
    status: str  # pending, syncing, synced, failed
    created_at: datetime
    synced_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class OfflineSyncPush(BaseModel):
    """Push queued offline changes to server"""
    queue_items: list[dict]  # List of actions from mobile


class OfflineSyncStatus(BaseModel):
    """Sync status response"""
    pending_count: int
    synced_count: int
    failed_count: int
    last_sync_time: Optional[datetime]
    next_retry_time: Optional[datetime]


class OfflineDataPackage(BaseModel):
    """Data package for offline use"""
    user: dict
    organization: dict
    prescriptions: list[dict]
    patient_visits: list[dict]
    devices: list[dict]
    photos: list[dict]
    last_sync: datetime
    package_version: str = "1.0"


class SyncConflict(BaseModel):
    """Conflict detected during sync"""
    resource_type: str
    resource_id: str
    local_version: dict
    server_version: dict
    local_updated_at: datetime
    server_updated_at: datetime
    resolution: str  # local_wins, server_wins, merge


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    code: Optional[str] = None
