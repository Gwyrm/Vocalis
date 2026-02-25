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
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    code: Optional[str] = None
