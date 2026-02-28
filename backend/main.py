"""
Vocalis Backend - Healthcare Device Delivery Platform
Multi-user system with authentication, prescriptions, and LLM-powered assistance
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, UploadFile, File, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
import logging
import asyncio
import tempfile
import uuid
import uvicorn
import json
from datetime import datetime, timedelta
from haversine import haversine, Unit

# Local imports
from database import get_db, get_db_for_user, init_db, prod_engine, Base, DEMO_ACCOUNT_EMAIL, DemoSessionLocal
from models import (
    User, Prescription, Organization, UserRole, PatientVisit, Device, VisitDetail,
    NurseLocation, PhotoAttachment, DeviceStatus, OfflineQueue,
    Patient, Medication, MedicationInteraction, DrugAllergy, PrescriptionDevice,
    Intervention, InterventionLog, InterventionDocument
)
from schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, CurrentUserResponse,
    UserProfileUpdate, ChangePasswordRequest, PasswordChangeResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionSignRequest, PrescriptionResponse, PrescriptionListResponse,
    PrescriptionDeviceCreate, PrescriptionDeviceResponse, DeviceResponse,
    PatientVisitCreate, PatientVisitUpdate, PatientVisitListResponse, PatientVisitDetailResponse,
    VisitCompleteRequest,
    NurseLocationCreate, NurseLocationResponse, PhotoResponse,
    DeviceCreate, DeviceUpdateStatus, DeviceListResponse,
    VisitAnalytics, DeviceAnalytics, NurseAnalytics,
    OfflineQueueItem, OfflineSyncPush, OfflineSyncStatus, OfflineDataPackage, SyncConflict,
    PatientCreate, PatientUpdate, PatientResponse, MedicationResponse,
    VoicePrescriptionRequest, TextPrescriptionRequest, PrescriptionValidationResponse,
    TranscriptionResponse,
    InterventionCreate, InterventionUpdate, InterventionResponse, InterventionListResponse,
    InterventionLogCreate, InterventionLogResponse, InterventionDocumentCreate, InterventionDocumentResponse,
    InterventionDetailResponse
)
from auth import (
    hash_password, verify_password, create_access_token, verify_token, TokenData
)
from voice_utils import (
    transcribe_audio, validate_medication, parse_prescription_text, structure_prescription_data
)

# Keep existing security and LLM functions
from llm_utils import (
    sanitize_input, validate_signature_image, SYSTEM_PROMPT,
    is_empty_response, normalize_key, call_ollama, extract_data_from_message,
    generate_response, cleanup_temp_file, PrescriptionData, ChatRequest, ChatResponse,
    GeneratePDFRequest, format_chat_prompt
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vocalis-backend")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
ollama_available = False

# Session storage for LLM interaction (per user, per session)
session_data = {}
session_lock = asyncio.Lock()


# ============================================================================
# DEDUPLICATION HELPERS
# ============================================================================

def normalize_item(item: str) -> str:
    """
    Normalize allergy/condition/medication string.
    Removes prefixes like "allergie aux", "allergie à", etc.
    Returns only the allergen/condition/medication name.
    """
    import re
    if not item:
        return ""

    normalized = item.strip()

    # Remove "allergie aux", "allergie à", "allergie à la", etc.
    normalized = re.sub(r'^allergie\s+(aux?|à\s+la?)\s+', '', normalized, flags=re.IGNORECASE)

    # Remove "condition", "condition chronique", etc. prefixes
    normalized = re.sub(r'^condition\s+(chronique\s+)?', '', normalized, flags=re.IGNORECASE)

    # Remove extra whitespace and normalize case
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Capitalize first letter for consistency
    if normalized:
        normalized = normalized[0].upper() + normalized[1:].lower()

    return normalized


def deduplicate_items(items: list) -> list:
    """
    Remove duplicates from a list of items (allergies, conditions, medications).
    Normalizes items by removing prefixes (e.g., "allergie aux orthies" -> "Orthies").
    Returns deduplicated list with normalized names only.
    """
    if not items:
        return []

    # Map normalized -> normalized items (only unique normalized values)
    seen = {}
    for item in items:
        if not item or not item.strip():
            continue
        norm = normalize_item(item)
        if norm and norm not in seen:
            seen[norm] = norm

    return list(seen.values())


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup, cleanup on shutdown"""
    global ollama_available

    # Initialize database tables
    logger.info("Initializing databases...")
    init_db()
    logger.info("Databases initialized")

    # Check Ollama availability
    logger.info(f"Checking Ollama at {OLLAMA_BASE_URL} with model {OLLAMA_MODEL}...")
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_available = True
            logger.info("Ollama is available!")
        else:
            logger.warning(f"Ollama returned status {response.status_code}")
    except Exception as e:
        logger.error(f"Ollama not available: {e}")

    yield

    logger.info("Shutting down...")
    ollama_available = False


# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Vocalis",
    description="Healthcare Device Delivery Platform",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

# Add FastAPI CORS middleware for proper CORS handling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
)

logger.info("CORS middleware configured - all origins allowed (development mode)")


# ============================================================================
# DEPENDENCIES
# ============================================================================

def _extract_email_from_token(authorization: str) -> str:
    """Extract email from JWT token without database access"""
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
        token_data = verify_token(token)
        if not token_data:
            return None
        return token_data.email
    except Exception:
        return None


async def get_db_for_request(authorization: str = Header(None)) -> Session:
    """Get database session based on Authorization header email

    Automatically routes to demo.db for demo account, vocalis.db for others
    """
    email = _extract_email_from_token(authorization)
    if email and email.lower() == DEMO_ACCOUNT_EMAIL.lower():
        db_generator = get_db_for_user(email)
        db = next(db_generator)
    else:
        db = next(get_db())

    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db_for_request)
) -> User:
    """Get current authenticated user from JWT token

    Uses demo.db for demo account, vocalis.db for others
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Use appropriate database based on email
    if token_data.email.lower() == DEMO_ACCOUNT_EMAIL.lower():
        db.close()  # Close the default production db session
        db_generator = get_db_for_user(token_data.email)
        db = next(db_generator)

    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.org_id == token_data.org_id
    ).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


async def get_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a doctor"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Doctor role required")
    return current_user


async def get_nurse(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a nurse"""
    if current_user.role != UserRole.NURSE:
        raise HTTPException(status_code=403, detail="Nurse role required")
    return current_user


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (first user can register without org, creates org)"""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # For Phase 1, create a default organization for new users
    # In production, this would be done by an admin
    org = db.query(Organization).first()
    if not org:
        org = Organization(
            name="Default Organization",
            created_at=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        logger.info(f"Created default organization: {org.id}")

    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
        org_id=org.id,
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered: {user.email} ({user.role})")

    # Create token
    token = create_access_token(user.id, user.org_id, user.email, user.role.value)

    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "org_id": user.org_id,
            "full_name": user.full_name
        }
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token

    Demo account uses demo.db, other accounts use vocalis.db
    """
    # Use correct database based on email
    if request.email.lower() == DEMO_ACCOUNT_EMAIL.lower():
        db.close()
        db = DemoSessionLocal()

    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"User logged in: {user.email}")

    # Create token
    token = create_access_token(user.id, user.org_id, user.email, user.role.value)

    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "org_id": user.org_id,
        }
    )


@app.get("/api/auth/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        org_id=current_user.org_id
    )


@app.put("/api/users/profile", response_model=CurrentUserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Update authenticated user's profile (email and full_name)"""

    # Validate inputs
    if profile_update.email:
        # Check email uniqueness
        existing = db.query(User).filter(
            User.email == profile_update.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        current_user.email = profile_update.email

    if profile_update.full_name:
        if not profile_update.full_name.strip():
            raise HTTPException(status_code=422, detail="Full name cannot be empty")
        current_user.full_name = profile_update.full_name

    db.commit()
    db.refresh(current_user)

    logger.info(f"User profile updated: {current_user.email}")

    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        org_id=current_user.org_id
    )


@app.post("/api/users/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_change: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Change authenticated user's password"""

    # Verify current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Verify new password is different from current
    if password_change.current_password == password_change.new_password:
        raise HTTPException(status_code=422, detail="New password must be different from current password")

    # Hash and update new password
    current_user.password_hash = hash_password(password_change.new_password)
    db.commit()

    logger.info(f"Password changed for user: {current_user.email}")

    return PasswordChangeResponse(
        message="Password changed successfully",
        success=True
    )


# ============================================================================
# PRESCRIPTION ENDPOINTS
# ============================================================================

@app.post("/api/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(
    request: PrescriptionCreate,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Create a new prescription (doctor only)"""

    # Fetch patient data to auto-populate name and age
    patient = db.query(Patient).filter(
        Patient.id == request.patient_id,
        Patient.org_id == current_user.org_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Calculate patient age
    patient_age = (datetime.utcnow().date() - patient.date_of_birth.date()).days // 365

    prescription = Prescription(
        org_id=current_user.org_id,
        created_by=current_user.id,
        patient_id=patient.id,
        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_age=str(patient_age),
        diagnosis=sanitize_input(request.diagnosis, 500),
        medication=sanitize_input(request.medication, 200),
        dosage=sanitize_input(request.dosage, 200),
        duration=sanitize_input(request.duration, 200),
        special_instructions=sanitize_input(request.special_instructions or "", 500),
        created_at=datetime.utcnow()
    )

    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    # Update patient record with discovered medical information if provided
    if request.discovered_allergies or request.discovered_conditions or request.discovered_medications:
        patient_allergies = json.loads(patient.allergies) if patient.allergies else []
        patient_conditions = json.loads(patient.chronic_conditions) if patient.chronic_conditions else []
        patient_medications = json.loads(patient.current_medications) if patient.current_medications else []

        # Add new discoveries (avoid duplicates)
        if request.discovered_allergies:
            for allergy in request.discovered_allergies:
                if allergy not in patient_allergies:
                    patient_allergies.append(allergy)

        if request.discovered_conditions:
            for condition in request.discovered_conditions:
                if condition not in patient_conditions:
                    patient_conditions.append(condition)

        if request.discovered_medications:
            for medication in request.discovered_medications:
                if medication not in patient_medications:
                    patient_medications.append(medication)

        patient.allergies = json.dumps(patient_allergies)
        patient.chronic_conditions = json.dumps(patient_conditions)
        patient.current_medications = json.dumps(patient_medications)
        patient.updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"Patient {patient.id} medical info updated via prescription {prescription.id}")

    logger.info(f"Prescription created: {prescription.id} by {current_user.email}")

    return PrescriptionResponse(
        id=prescription.id,
        patient_name=prescription.patient_name,
        patient_age=prescription.patient_age,
        diagnosis=prescription.diagnosis,
        medication=prescription.medication,
        dosage=prescription.dosage,
        duration=prescription.duration,
        special_instructions=prescription.special_instructions,
        status=prescription.status,
        created_by=prescription.created_by,
        created_at=prescription.created_at,
        is_signed=prescription.is_signed,
        doctor_signed_at=prescription.doctor_signed_at
    )


@app.get("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get prescription details"""

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return prescription


@app.get("/api/prescriptions", response_model=list[PrescriptionListResponse])
async def list_prescriptions(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """List prescriptions (filtered by organization)"""

    query = db.query(Prescription).filter(Prescription.org_id == current_user.org_id)

    if status:
        query = query.filter(Prescription.status == status)

    prescriptions = query.order_by(Prescription.created_at.desc()).all()

    return [PrescriptionListResponse.from_attributes(p) for p in prescriptions]


@app.put("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: str,
    request: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Update prescription (draft only)"""

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Only allow editing draft prescriptions
    if prescription.status != "draft":
        raise HTTPException(status_code=403, detail="Only draft prescriptions can be edited")

    # Update fields
    if request.diagnosis:
        prescription.diagnosis = sanitize_input(request.diagnosis, 500)
    if request.medication:
        prescription.medication = sanitize_input(request.medication, 200)
    if request.dosage:
        prescription.dosage = sanitize_input(request.dosage, 200)
    if request.duration:
        prescription.duration = sanitize_input(request.duration, 200)
    if request.special_instructions:
        prescription.special_instructions = sanitize_input(request.special_instructions, 500)
    if request.status:
        prescription.status = request.status

    db.commit()
    db.refresh(prescription)

    # Update patient record with discovered medical information if provided
    if (request.discovered_allergies or request.discovered_conditions or request.discovered_medications) and prescription.patient_id:
        patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
        if patient:
            patient_allergies = json.loads(patient.allergies) if patient.allergies else []
            patient_conditions = json.loads(patient.chronic_conditions) if patient.chronic_conditions else []
            patient_medications = json.loads(patient.current_medications) if patient.current_medications else []

            # Add new discoveries (avoid duplicates)
            if request.discovered_allergies:
                for allergy in request.discovered_allergies:
                    if allergy not in patient_allergies:
                        patient_allergies.append(allergy)

            if request.discovered_conditions:
                for condition in request.discovered_conditions:
                    if condition not in patient_conditions:
                        patient_conditions.append(condition)

            if request.discovered_medications:
                for medication in request.discovered_medications:
                    if medication not in patient_medications:
                        patient_medications.append(medication)

            patient.allergies = json.dumps(patient_allergies)
            patient.chronic_conditions = json.dumps(patient_conditions)
            patient.current_medications = json.dumps(patient_medications)
            patient.updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Patient {patient.id} medical info updated via prescription update {prescription.id}")

    logger.info(f"Prescription updated: {prescription.id}")

    return PrescriptionResponse(
        id=prescription.id,
        patient_name=prescription.patient_name,
        patient_age=prescription.patient_age,
        diagnosis=prescription.diagnosis,
        medication=prescription.medication,
        dosage=prescription.dosage,
        duration=prescription.duration,
        special_instructions=prescription.special_instructions,
        status=prescription.status,
        created_by=prescription.created_by,
        created_at=prescription.created_at,
        is_signed=prescription.is_signed,
        doctor_signed_at=prescription.doctor_signed_at
    )


@app.put("/api/prescriptions/{prescription_id}/sign", response_model=PrescriptionResponse)
async def sign_prescription(
    prescription_id: str,
    request: PrescriptionSignRequest,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Confirm/sign prescription (doctor only)

    This marks the prescription as confirmed and ready for use.
    """

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Only the doctor who created the prescription can sign it (or an admin)
    if prescription.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the doctor who created this prescription can sign it")

    # Check if already signed
    if prescription.is_signed:
        raise HTTPException(status_code=400, detail="Prescription is already signed")

    # Sign the prescription
    prescription.doctor_signed_at = datetime.utcnow()
    prescription.is_signed = True
    prescription.status = "signed"  # Change status to indicate it's signed

    db.commit()
    db.refresh(prescription)

    logger.info(f"Prescription confirmed by doctor {current_user.email}: {prescription.id}")

    return PrescriptionResponse(
        id=prescription.id,
        patient_name=prescription.patient_name,
        patient_age=prescription.patient_age,
        diagnosis=prescription.diagnosis,
        medication=prescription.medication,
        dosage=prescription.dosage,
        duration=prescription.duration,
        special_instructions=prescription.special_instructions,
        status=prescription.status,
        created_by=prescription.created_by,
        created_at=prescription.created_at,
        is_signed=prescription.is_signed,
        doctor_signed_at=prescription.doctor_signed_at
    )


# ============================================================================
# DEVICE MANAGEMENT ENDPOINTS - Link devices to prescriptions
# ============================================================================

@app.post("/api/prescriptions/{prescription_id}/devices", response_model=PrescriptionDeviceResponse)
async def add_device_to_prescription(
    prescription_id: str,
    device_req: PrescriptionDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Add device to prescription (doctor only)"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can assign devices to prescriptions")

    # Verify prescription exists and belongs to user's org
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Verify device exists and belongs to org
    device = db.query(Device).filter(
        Device.id == device_req.device_id,
        Device.org_id == current_user.org_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check if device already assigned
    existing = db.query(PrescriptionDevice).filter(
        PrescriptionDevice.prescription_id == prescription_id,
        PrescriptionDevice.device_id == device_req.device_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Device already assigned to this prescription")

    # Create assignment
    assignment = PrescriptionDevice(
        prescription_id=prescription_id,
        device_id=device_req.device_id,
        quantity=device_req.quantity,
        instructions=device_req.instructions,
        priority=device_req.priority
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    logger.info(f"Device {device.id} assigned to prescription {prescription_id}")

    return PrescriptionDeviceResponse(
        id=assignment.id,
        device_id=assignment.device_id,
        quantity=assignment.quantity,
        instructions=assignment.instructions,
        priority=assignment.priority
    )


@app.get("/api/prescriptions/{prescription_id}/devices", response_model=list[PrescriptionDeviceResponse])
async def get_prescription_devices(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get devices assigned to prescription"""
    # Verify prescription exists
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    devices = db.query(PrescriptionDevice).filter(
        PrescriptionDevice.prescription_id == prescription_id
    ).all()

    return [
        PrescriptionDeviceResponse(
            id=d.id,
            device_id=d.device_id,
            quantity=d.quantity,
            instructions=d.instructions,
            priority=d.priority
        )
        for d in devices
    ]


@app.delete("/api/prescriptions/{prescription_id}/devices/{device_id}")
async def remove_device_from_prescription(
    prescription_id: str,
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Remove device from prescription"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can modify prescription devices")

    # Verify prescription exists
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Find and delete assignment
    assignment = db.query(PrescriptionDevice).filter(
        PrescriptionDevice.prescription_id == prescription_id,
        PrescriptionDevice.device_id == device_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Device not assigned to this prescription")

    db.delete(assignment)
    db.commit()

    logger.info(f"Device {device_id} removed from prescription {prescription_id}")

    return {"message": "Device removed from prescription"}


# ============================================================================
# PATIENT VISIT ENDPOINTS (Nurse field operations)
# ============================================================================

@app.post("/api/patient-visits", response_model=dict)
async def create_patient_visit(
    request: PatientVisitCreate,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Create patient visit assignment (doctor only)"""

    # Verify prescription exists and belongs to org
    prescription = db.query(Prescription).filter(
        Prescription.id == request.prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Verify nurse exists and belongs to org
    nurse = db.query(User).filter(
        User.id == request.assigned_nurse,
        User.org_id == current_user.org_id,
        User.role == UserRole.NURSE
    ).first()

    if not nurse:
        raise HTTPException(status_code=404, detail="Nurse not found")

    # Create visit
    visit = PatientVisit(
        org_id=current_user.org_id,
        prescription_id=request.prescription_id,
        assigned_nurse=request.assigned_nurse,
        patient_address=sanitize_input(request.patient_address, 500),
        scheduled_date=request.scheduled_date,
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(visit)
    db.commit()
    db.refresh(visit)

    logger.info(f"Patient visit created: {visit.id} for nurse {nurse.email}")

    return {"id": visit.id, "status": "pending"}


@app.get("/api/patient-visits", response_model=list[PatientVisitListResponse])
async def list_patient_visits(
    status: str = None,
    date_from: datetime = None,
    date_to: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """List patient visits - nurses see only their visits, doctors see all"""

    query = db.query(PatientVisit).filter(PatientVisit.org_id == current_user.org_id)

    # Nurses see only their assigned visits
    if current_user.role == UserRole.NURSE:
        query = query.filter(PatientVisit.assigned_nurse == current_user.id)

    # Filter by status if provided
    if status:
        query = query.filter(PatientVisit.status == status)

    # Filter by date range
    if date_from:
        query = query.filter(PatientVisit.scheduled_date >= date_from)
    if date_to:
        query = query.filter(PatientVisit.scheduled_date <= date_to)

    visits = query.order_by(PatientVisit.scheduled_date.asc()).all()

    # Enrich with prescription data
    result = []
    for visit in visits:
        prescription = db.query(Prescription).filter(
            Prescription.id == visit.prescription_id
        ).first()

        if prescription:
            response = PatientVisitListResponse(
                id=visit.id,
                prescription_id=visit.prescription_id,
                patient_name=prescription.patient_name,
                diagnosis=prescription.diagnosis,
                patient_address=visit.patient_address,
                scheduled_date=visit.scheduled_date,
                status=visit.status,
                created_at=visit.created_at
            )
            result.append(response)

    return result


@app.get("/api/patient-visits/{visit_id}", response_model=PatientVisitDetailResponse)
async def get_patient_visit(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get patient visit details"""

    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.org_id == current_user.org_id
    ).first()

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Nurses can only see their own visits
    if current_user.role == UserRole.NURSE and visit.assigned_nurse != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this visit")

    # Get prescription data
    prescription = db.query(Prescription).filter(
        Prescription.id == visit.prescription_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Get visit details if completed
    visit_detail = db.query(VisitDetail).filter(
        VisitDetail.visit_id == visit_id
    ).first()

    response = PatientVisitDetailResponse(
        id=visit.id,
        prescription_id=visit.prescription_id,
        assigned_nurse=visit.assigned_nurse,
        patient_address=visit.patient_address,
        scheduled_date=visit.scheduled_date,
        status=visit.status,
        created_at=visit.created_at,
        patient_name=prescription.patient_name,
        patient_age=prescription.patient_age,
        diagnosis=prescription.diagnosis,
        medication=prescription.medication,
        dosage=prescription.dosage,
        duration=prescription.duration,
        special_instructions=prescription.special_instructions,
        nurse_notes=visit_detail.nurse_notes if visit_detail else None,
        device_serial_installed=visit_detail.device_id if visit_detail else None,
        patient_signature=visit_detail.patient_signature if visit_detail else None,
        completed_at=visit_detail.completed_at if visit_detail else None
    )

    return response


@app.put("/api/patient-visits/{visit_id}/status")
async def update_visit_status(
    visit_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Update visit status (pending → in_progress → completed)"""

    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.org_id == current_user.org_id
    ).first()

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Nurses can only update their own visits
    if current_user.role == UserRole.NURSE and visit.assigned_nurse != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this visit")

    # Validate status transition
    valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    visit.status = status
    db.commit()
    db.refresh(visit)

    logger.info(f"Visit {visit_id} status updated to {status} by {current_user.email}")

    return {"id": visit.id, "status": visit.status}


@app.post("/api/patient-visits/{visit_id}/complete")
async def complete_patient_visit(
    visit_id: str,
    request: VisitCompleteRequest,
    current_user: User = Depends(get_nurse),
    db: Session = Depends(get_db_for_request)
):
    """Mark visit as completed with notes and signature (nurse only)"""

    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.org_id == current_user.org_id
    ).first()

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Only assigned nurse can complete
    if visit.assigned_nurse != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to complete this visit")

    # Update visit status
    visit.status = "completed"
    db.commit()

    # Create visit details record
    visit_detail = VisitDetail(
        visit_id=visit_id,
        nurse_notes=sanitize_input(request.nurse_notes, 2000),
        patient_signature=request.patient_signature,  # Already validated by frontend
        completed_at=datetime.utcnow()
    )

    # Add device if provided
    if request.device_serial_installed:
        device = db.query(Device).filter(
            Device.serial_number == request.device_serial_installed,
            Device.org_id == current_user.org_id
        ).first()

        if device:
            visit_detail.device_id = device.id
            device.status = "in_use"
        else:
            logger.warning(f"Device not found: {request.device_serial_installed}")

    db.add(visit_detail)
    db.commit()
    db.refresh(visit_detail)

    logger.info(f"Visit {visit_id} completed by {current_user.email}")

    return {
        "id": visit.id,
        "status": "completed",
        "completed_at": visit_detail.completed_at
    }


# ============================================================================
# PHASE 3: GPS TRACKING ENDPOINTS
# ============================================================================

@app.post("/api/nurse-locations", response_model=dict)
async def record_nurse_location(
    request: NurseLocationCreate,
    current_user: User = Depends(get_nurse),
    db: Session = Depends(get_db_for_request)
):
    """Record nurse GPS location"""

    location = NurseLocation(
        org_id=current_user.org_id,
        nurse_id=current_user.id,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy,
        visit_id=request.visit_id,
        recorded_at=datetime.utcnow()
    )

    db.add(location)
    db.commit()

    logger.info(f"Location recorded for {current_user.email}: ({request.latitude}, {request.longitude})")

    return {"id": location.id, "recorded_at": location.recorded_at}


@app.get("/api/nurse-locations", response_model=list[NurseLocationResponse])
async def get_nurse_locations(
    nurse_id: str = None,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Get current nurse locations (doctor only)"""

    query = db.query(NurseLocation).filter(
        NurseLocation.org_id == current_user.org_id
    )

    if nurse_id:
        query = query.filter(NurseLocation.nurse_id == nurse_id)

    # Get latest location for each nurse (or specific nurse)
    locations = query.order_by(NurseLocation.recorded_at.desc()).all()

    return [NurseLocationResponse.from_attributes(loc) for loc in locations[:100]]


# ============================================================================
# PHASE 3: PHOTO ATTACHMENTS ENDPOINTS
# ============================================================================

@app.post("/api/patient-visits/{visit_id}/photos", response_model=PhotoResponse)
async def upload_visit_photo(
    visit_id: str,
    file: UploadFile = File(...),
    caption: str = None,
    current_user: User = Depends(get_nurse),
    db: Session = Depends(get_db_for_request)
):
    """Upload photo for patient visit"""

    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.org_id == current_user.org_id
    ).first()

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    if visit.assigned_nurse != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Save file to temp directory
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"photo_{visit_id}_{uuid.uuid4()}.{file_ext}"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        # Read and save file
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        # Create database record
        photo = PhotoAttachment(
            visit_id=visit_id,
            file_path=filepath,
            caption=sanitize_input(caption or "", 500),
            file_size=len(contents),
            mime_type=file.content_type or "image/jpeg",
            uploaded_at=datetime.utcnow()
        )

        db.add(photo)
        db.commit()
        db.refresh(photo)

        logger.info(f"Photo uploaded for visit {visit_id}: {filename}")

        return PhotoResponse.from_attributes(photo)

    except Exception as e:
        logger.error(f"Photo upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload photo")


@app.get("/api/patient-visits/{visit_id}/photos", response_model=list[PhotoResponse])
async def get_visit_photos(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get photos for visit"""

    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.org_id == current_user.org_id
    ).first()

    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    if current_user.role == UserRole.NURSE and visit.assigned_nurse != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    photos = db.query(PhotoAttachment).filter(
        PhotoAttachment.visit_id == visit_id
    ).order_by(PhotoAttachment.uploaded_at.asc()).all()

    return [PhotoResponse.from_attributes(photo) for photo in photos]


# ============================================================================
# PHASE 3: DEVICE INVENTORY ENDPOINTS
# ============================================================================

@app.post("/api/devices", response_model=dict)
async def create_device(
    request: DeviceCreate,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Create device in inventory (doctor/admin only)"""

    # Check if serial already exists
    existing = db.query(Device).filter(
        Device.serial_number == request.serial_number
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Device serial already exists")

    device = Device(
        org_id=current_user.org_id,
        name=sanitize_input(request.name, 200),
        model=sanitize_input(request.model or "", 200),
        serial_number=sanitize_input(request.serial_number, 100),
        status="available",
        created_at=datetime.utcnow()
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info(f"Device created: {device.serial_number}")

    return {"id": device.id, "status": "available"}


@app.get("/api/devices", response_model=list[DeviceListResponse])
async def list_devices(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """List devices in organization inventory"""

    query = db.query(Device).filter(Device.org_id == current_user.org_id)

    if status:
        query = query.filter(Device.status == status)

    devices = query.order_by(Device.created_at.desc()).all()

    return [DeviceListResponse.from_attributes(d) for d in devices]


@app.patch("/api/devices/{device_id}")
async def update_device_status(
    device_id: str,
    request: DeviceUpdateStatus,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Update device status"""

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.org_id == current_user.org_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    old_status = device.status
    device.status = request.status
    db.commit()

    # Record status change in history
    history = DeviceStatus(
        device_id=device_id,
        visit_id=request.visit_id,
        old_status=old_status,
        new_status=request.status,
        changed_by=current_user.id,
        reason=request.reason,
        changed_at=datetime.utcnow()
    )

    db.add(history)
    db.commit()

    logger.info(f"Device {device_id} status updated: {old_status} → {request.status}")

    return {"id": device.id, "status": device.status}


# ============================================================================
# PHASE 3: ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics/visits", response_model=VisitAnalytics)
async def get_visit_analytics(
    date_from: datetime = None,
    date_to: datetime = None,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Get visit completion analytics"""

    query = db.query(PatientVisit).filter(PatientVisit.org_id == current_user.org_id)

    if date_from:
        query = query.filter(PatientVisit.created_at >= date_from)
    if date_to:
        query = query.filter(PatientVisit.created_at <= date_to)

    visits = query.all()

    total = len(visits)
    completed = len([v for v in visits if v.status == "completed"])
    pending = len([v for v in visits if v.status == "pending"])
    in_progress = len([v for v in visits if v.status == "in_progress"])

    completion_rate = (completed / total * 100) if total > 0 else 0

    # Calculate average duration
    completed_visits = db.query(PatientVisit, VisitDetail).join(
        VisitDetail, PatientVisit.id == VisitDetail.visit_id
    ).filter(
        PatientVisit.org_id == current_user.org_id,
        PatientVisit.status == "completed"
    ).all()

    if completed_visits:
        durations = [
            (vd[1].completed_at - vd[0].created_at).total_seconds() / 60
            for vd in completed_visits if vd[1].completed_at
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
    else:
        avg_duration = 0

    return VisitAnalytics(
        total_visits=total,
        completed_visits=completed,
        pending_visits=pending,
        in_progress_visits=in_progress,
        completion_rate=completion_rate,
        average_visit_duration_minutes=avg_duration
    )


@app.get("/api/analytics/devices", response_model=DeviceAnalytics)
async def get_device_analytics(
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Get device usage analytics"""

    devices = db.query(Device).filter(Device.org_id == current_user.org_id).all()

    total = len(devices)
    available = len([d for d in devices if d.status == "available"])
    in_use = len([d for d in devices if d.status == "in_use"])
    maintenance = len([d for d in devices if d.status == "maintenance"])

    utilization_rate = ((in_use + total - available) / total * 100) if total > 0 else 0

    return DeviceAnalytics(
        total_devices=total,
        available_devices=available,
        in_use_devices=in_use,
        maintenance_devices=maintenance,
        device_utilization_rate=utilization_rate
    )


@app.get("/api/analytics/nurses", response_model=list[NurseAnalytics])
async def get_nurse_analytics(
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db_for_request)
):
    """Get nurse performance analytics"""

    nurses = db.query(User).filter(
        User.org_id == current_user.org_id,
        User.role == UserRole.NURSE
    ).all()

    results = []

    for nurse in nurses:
        visits = db.query(PatientVisit).filter(
            PatientVisit.assigned_nurse == nurse.id
        ).all()

        total_visits = len(visits)
        completed_visits = len([v for v in visits if v.status == "completed"])

        # Calculate average duration
        completed = db.query(PatientVisit, VisitDetail).join(
            VisitDetail, PatientVisit.id == VisitDetail.visit_id
        ).filter(
            PatientVisit.assigned_nurse == nurse.id,
            PatientVisit.status == "completed"
        ).all()

        if completed:
            durations = [
                (vd[1].completed_at - vd[0].created_at).total_seconds() / 60
                for vd in completed if vd[1].completed_at
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0
        else:
            avg_duration = 0

        completion_rate = (completed_visits / total_visits * 100) if total_visits > 0 else 0

        results.append(NurseAnalytics(
            nurse_id=nurse.id,
            nurse_name=nurse.full_name,
            total_visits=total_visits,
            completed_visits=completed_visits,
            average_visit_duration_minutes=avg_duration,
            completion_rate=completion_rate
        ))

    return results


# ============================================================================
# PHASE 3: WEBSOCKET REAL-TIME UPDATES
# ============================================================================

# Store active WebSocket connections
active_connections: dict[str, list[WebSocket]] = {}


@app.websocket("/ws/doctor/{user_id}")
async def websocket_doctor_updates(websocket: WebSocket, user_id: str):
    """WebSocket for doctor to receive real-time visit updates"""

    await websocket.accept()

    # Store connection
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)

    logger.info(f"Doctor {user_id} connected to WebSocket")

    try:
        while True:
            data = await websocket.receive_text()
            # Can receive keepalive or commands
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        active_connections[user_id].remove(websocket)
        logger.info(f"Doctor {user_id} disconnected from WebSocket")


async def notify_doctor_visit_update(org_id: str, visit_id: str, status: str, details: dict):
    """Send real-time update to all doctors in organization"""
    # In production, would query for all doctor users and send updates
    message = {
        "type": "visit_update",
        "visit_id": visit_id,
        "status": status,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }

    for connections in active_connections.values():
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Vocalis Backend is running", "version": "2.0.0"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "backend": "running",
        "database": "connected",
        "ollama_available": ollama_available,
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL
    }


# ============================================================================
# PHASE 3.5: OFFLINE SYNC ENDPOINTS
# ============================================================================

@app.post("/api/offline-sync/prepare", response_model=OfflineDataPackage)
async def prepare_offline_data(
    date_from: datetime = None,
    date_to: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Prepare data package for offline use (download for mobile app)"""

    # Default to today if no dates specified
    if not date_from:
        date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get user data
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value
    }

    # Get organization data
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    org_data = {
        "id": org.id,
        "name": org.name,
        "address": org.address,
        "phone": org.phone
    } if org else {}

    # Get prescriptions (for doctor or relevant to nurse)
    prescriptions_query = db.query(Prescription).filter(
        Prescription.org_id == current_user.org_id,
        Prescription.created_at >= date_from,
        Prescription.created_at <= date_to
    )

    prescriptions = [
        {
            "id": p.id,
            "patient_name": p.patient_name,
            "patient_age": p.patient_age,
            "diagnosis": p.diagnosis,
            "medication": p.medication,
            "dosage": p.dosage,
            "duration": p.duration,
            "special_instructions": p.special_instructions,
            "status": p.status,
            "created_at": p.created_at.isoformat()
        }
        for p in prescriptions_query.all()
    ]

    # Get patient visits (nurse sees only own, doctor sees all)
    visits_query = db.query(PatientVisit).filter(
        PatientVisit.org_id == current_user.org_id,
        PatientVisit.scheduled_date >= date_from,
        PatientVisit.scheduled_date <= date_to
    )

    if current_user.role == UserRole.NURSE:
        visits_query = visits_query.filter(PatientVisit.assigned_nurse == current_user.id)

    visits = [
        {
            "id": v.id,
            "prescription_id": v.prescription_id,
            "patient_address": v.patient_address,
            "scheduled_date": v.scheduled_date.isoformat(),
            "status": v.status,
            "created_at": v.created_at.isoformat()
        }
        for v in visits_query.all()
    ]

    # Get devices
    devices = [
        {
            "id": d.id,
            "name": d.name,
            "model": d.model,
            "serial_number": d.serial_number,
            "status": d.status,
            "created_at": d.created_at.isoformat()
        }
        for d in db.query(Device).filter(Device.org_id == current_user.org_id).all()
    ]

    # Get photos for nurse's visits
    photos = []
    if current_user.role == UserRole.NURSE:
        nurse_visit_ids = [v.id for v in db.query(PatientVisit).filter(
            PatientVisit.assigned_nurse == current_user.id
        ).all()]

        photos = [
            {
                "id": p.id,
                "visit_id": p.visit_id,
                "caption": p.caption,
                "uploaded_at": p.uploaded_at.isoformat()
            }
            for p in db.query(PhotoAttachment).filter(
                PhotoAttachment.visit_id.in_(nurse_visit_ids)
            ).all()
        ]

    logger.info(f"Offline data prepared for {current_user.email}")

    return OfflineDataPackage(
        user=user_data,
        organization=org_data,
        prescriptions=prescriptions,
        patient_visits=visits,
        devices=devices,
        photos=photos,
        last_sync=datetime.utcnow()
    )


@app.post("/api/offline-sync/push")
async def push_offline_changes(
    request: OfflineSyncPush,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Process queued offline changes from mobile app"""

    synced_count = 0
    failed_count = 0
    conflicts = []

    for item in request.queue_items:
        try:
            action = item.get("action")
            resource_type = item.get("resource_type")
            payload = item.get("payload", {})

            # Validate permissions
            if resource_type in ["prescription", "device"] and current_user.role != UserRole.DOCTOR:
                failed_count += 1
                continue

            # Process based on resource type
            if resource_type == "patient_visit" and action == "update":
                visit = db.query(PatientVisit).filter(
                    PatientVisit.id == item.get("resource_id"),
                    PatientVisit.org_id == current_user.org_id
                ).first()

                if visit:
                    visit.status = payload.get("status", visit.status)
                    db.commit()
                    synced_count += 1
                else:
                    failed_count += 1

            elif resource_type == "nurse_location" and action == "create":
                location = NurseLocation(
                    org_id=current_user.org_id,
                    nurse_id=current_user.id,
                    latitude=payload.get("latitude"),
                    longitude=payload.get("longitude"),
                    accuracy=payload.get("accuracy"),
                    visit_id=payload.get("visit_id"),
                    recorded_at=datetime.utcnow()
                )
                db.add(location)
                db.commit()
                synced_count += 1

            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"Sync error for {resource_type}: {e}")
            failed_count += 1

    logger.info(f"Offline sync: {synced_count} synced, {failed_count} failed for {current_user.email}")

    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "total_processed": len(request.queue_items),
        "conflicts": conflicts
    }


@app.get("/api/offline-sync/status", response_model=OfflineSyncStatus)
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get current sync status"""

    queue = db.query(OfflineQueue).filter(
        OfflineQueue.user_id == current_user.id
    ).all()

    pending = len([q for q in queue if q.status == "pending"])
    synced = len([q for q in queue if q.status == "synced"])
    failed = len([q for q in queue if q.status == "failed"])

    # Find last sync time
    last_synced = max(
        [q.synced_at for q in queue if q.synced_at],
        default=None
    )

    # Calculate next retry time (exponential backoff)
    failed_items = [q for q in queue if q.status == "failed"]
    next_retry = None
    if failed_items:
        latest_failed = max(failed_items, key=lambda x: x.created_at)
        retry_delay = timedelta(minutes=2 ** min(3, (datetime.utcnow() - latest_failed.created_at).seconds // 300))
        next_retry = latest_failed.created_at + retry_delay

    return OfflineSyncStatus(
        pending_count=pending,
        synced_count=synced,
        failed_count=failed,
        last_sync_time=last_synced,
        next_retry_time=next_retry
    )


@app.get("/api/offline-sync/queue", response_model=list[OfflineQueueItem])
async def get_sync_queue(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get pending offline sync queue"""

    query = db.query(OfflineQueue).filter(OfflineQueue.user_id == current_user.id)

    if status:
        query = query.filter(OfflineQueue.status == status)

    items = query.order_by(OfflineQueue.created_at.desc()).all()

    return [OfflineQueueItem.from_attributes(item) for item in items]


@app.post("/api/offline-sync/queue")
async def queue_offline_action(
    action: str,
    resource_type: str,
    payload: dict,
    resource_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Manually queue an offline action"""

    queue_item = OfflineQueue(
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=json.dumps(payload),
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)

    logger.info(f"Action queued: {action} {resource_type} by {current_user.email}")

    return {"id": queue_item.id, "status": "pending"}


@app.delete("/api/offline-sync/queue/{queue_id}")
async def clear_queue_item(
    queue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Clear specific queue item"""

    item = db.query(OfflineQueue).filter(
        OfflineQueue.id == queue_id,
        OfflineQueue.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    db.delete(item)
    db.commit()

    logger.info(f"Queue item cleared: {queue_id}")

    return {"status": "deleted"}


# ============================================================================
# CHAT ENDPOINT (requires authentication)
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat endpoint with LLM (authenticated users only)"""

    if not ollama_available:
        raise HTTPException(
            status_code=503,
            detail="Ollama n'est pas disponible. Veuillez démarrer Ollama."
        )

    try:
        # Use user-specific session storage
        session_key = f"{current_user.id}:chat_session"
        async with session_lock:
            session = session_data.get(session_key, {})
            current_data = PrescriptionData(**session) if session else PrescriptionData()

            # Extract information from user message
            current_data = await extract_data_from_message(request.message, current_data)

            # Save updated data to session
            session_data[session_key] = current_data.model_dump(exclude_none=True)

        # Generate response
        response_text = await generate_response(request.message, current_data)

        return ChatResponse(
            response=response_text,
            is_complete=current_data.is_complete(),
            missing_fields=current_data.get_missing_fields(),
            prescription_data=current_data
        )

    except Exception as e:
        logger.exception("Error in chat")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PDF GENERATION ENDPOINT
# ============================================================================

@app.post("/api/generate-pdf")
async def generate_pdf(
    request: GeneratePDFRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Generate PDF prescription (authenticated users only)"""

    logger.info(f"PDF generation request from {current_user.email}")

    try:
        from fpdf import FPDF

        # Get session data
        session_key = f"{current_user.id}:chat_session"
        async with session_lock:
            session = session_data.get(session_key, {})
            current_data = PrescriptionData(**session) if session else PrescriptionData()

        # Check if complete
        if not current_data.is_complete():
            missing = ", ".join(current_data.get_missing_fields())
            raise HTTPException(
                status_code=400,
                detail=f"Données incomplètes: {missing}"
            )

        # Build prescription text
        prescription_text = f"""ORDONNANCE MEDICALE

Patient: {current_data.patientName}
Age: {current_data.patientAge}

DIAGNOSTIC:
{current_data.diagnosis}

MEDICAMENT:
{current_data.medication}

POSOLOGIE:
{current_data.dosage}

DUREE:
{current_data.duration}

INSTRUCTIONS SPECIALES:
{current_data.specialInstructions}

Date: {datetime.now().strftime('%d/%m/%Y')}
Médecin: {current_user.full_name}
"""

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        # Title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "ORDONNANCE MEDICALE", ln=True, align="C")
        pdf.ln(5)

        # Content
        pdf.set_font("Arial", size=10)
        for line in prescription_text.split("\n"):
            pdf.cell(0, 5, line, ln=True)

        pdf.ln(10)

        # Signature (with validation)
        sig_temp_path = None
        if request.signature_base64:
            img_bytes = validate_signature_image(request.signature_base64)
            if img_bytes:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(img_bytes)
                        sig_temp_path = tmp.name

                    pdf.cell(0, 5, "Signature:", ln=True)
                    pdf.image(sig_temp_path, w=50)

                except Exception as e:
                    logger.error(f"Signature processing error: {e}")
                    pdf.cell(0, 5, "[Signature Error]", ln=True)
            else:
                logger.warning("Signature validation failed")
                pdf.cell(0, 5, "[Invalid Signature]", ln=True)

        # Save PDF
        filename = f"ordonnance_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)

        # Schedule cleanup
        if sig_temp_path:
            background_tasks.add_task(cleanup_temp_file, sig_temp_path)
        background_tasks.add_task(cleanup_temp_file, filepath)

        logger.info(f"PDF generated: {filename}")
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    except Exception as e:
        logger.exception("PDF generation error")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PATIENT MANAGEMENT ENDPOINTS (AI-Oriented App)
# ============================================================================

@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(
    request: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Create a new patient"""
    try:
        patient = Patient(
            id=str(uuid.uuid4()),
            org_id=current_user.org_id,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            phone=request.phone,
            email=request.email,
            address=request.address,
            allergies=json.dumps(request.allergies) if request.allergies else None,
            chronic_conditions=json.dumps(request.chronic_conditions) if request.chronic_conditions else None,
            current_medications=json.dumps(request.current_medications) if request.current_medications else None,
            medical_notes=request.medical_notes
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Convert JSON fields back to lists for response
        patient_dict = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "allergies": json.loads(patient.allergies) if patient.allergies else None,
            "chronic_conditions": json.loads(patient.chronic_conditions) if patient.chronic_conditions else None,
            "current_medications": json.loads(patient.current_medications) if patient.current_medications else None,
            "medical_notes": patient.medical_notes,
            "created_at": patient.created_at
        }
        return PatientResponse(**patient_dict)
    except Exception as e:
        logger.exception("Patient creation error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get patient by ID"""
    try:
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient_dict = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "allergies": json.loads(patient.allergies) if patient.allergies else None,
            "chronic_conditions": json.loads(patient.chronic_conditions) if patient.chronic_conditions else None,
            "current_medications": json.loads(patient.current_medications) if patient.current_medications else None,
            "medical_notes": patient.medical_notes,
            "created_at": patient.created_at
        }
        return PatientResponse(**patient_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Patient retrieval error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/{patient_id}/prescriptions", response_model=list[PrescriptionResponse])
async def get_patient_prescriptions(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get all prescriptions for a patient"""
    try:
        # Verify patient exists and belongs to user's organization
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get all prescriptions for this patient, ordered by creation date (newest first)
        prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient_id,
            Prescription.org_id == current_user.org_id
        ).order_by(Prescription.created_at.desc()).all()

        return [
            PrescriptionResponse(
                id=p.id,
                patient_name=p.patient_name,
                patient_age=p.patient_age,
                diagnosis=p.diagnosis,
                medication=p.medication,
                dosage=p.dosage,
                duration=p.duration,
                special_instructions=p.special_instructions,
                status=p.status,
                created_by=p.created_by_user.email if p.created_by_user else "Unknown",
                created_at=p.created_at,
                is_signed=p.is_signed or False,
                doctor_signed_at=p.doctor_signed_at
            )
            for p in prescriptions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Prescription retrieval error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients", response_model=list[PatientResponse])
async def list_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """List all patients for organization"""
    try:
        patients = db.query(Patient).filter(Patient.org_id == current_user.org_id).all()

        result = []
        for patient in patients:
            patient_dict = {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth,
                "gender": patient.gender,
                "phone": patient.phone,
                "email": patient.email,
                "address": patient.address,
                "allergies": json.loads(patient.allergies) if patient.allergies else None,
                "chronic_conditions": json.loads(patient.chronic_conditions) if patient.chronic_conditions else None,
                "current_medications": json.loads(patient.current_medications) if patient.current_medications else None,
                "medical_notes": patient.medical_notes,
                "created_at": patient.created_at
            }
            result.append(PatientResponse(**patient_dict))

        return result
    except Exception as e:
        logger.exception("Patient listing error")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    request: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Update patient information"""
    try:
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update fields if provided
        if request.first_name is not None:
            patient.first_name = request.first_name
        if request.last_name is not None:
            patient.last_name = request.last_name
        if request.phone is not None:
            patient.phone = request.phone
        if request.email is not None:
            patient.email = request.email
        if request.address is not None:
            patient.address = request.address
        if request.allergies is not None:
            # Deduplicate allergies to avoid duplicates like "allergie aux orthies" and "orthies"
            patient.allergies = json.dumps(deduplicate_items(request.allergies))
        if request.chronic_conditions is not None:
            # Deduplicate conditions
            patient.chronic_conditions = json.dumps(deduplicate_items(request.chronic_conditions))
        if request.current_medications is not None:
            # Deduplicate medications
            patient.current_medications = json.dumps(deduplicate_items(request.current_medications))
        if request.medical_notes is not None:
            patient.medical_notes = request.medical_notes

        patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(patient)

        patient_dict = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "allergies": json.loads(patient.allergies) if patient.allergies else None,
            "chronic_conditions": json.loads(patient.chronic_conditions) if patient.chronic_conditions else None,
            "current_medications": json.loads(patient.current_medications) if patient.current_medications else None,
            "medical_notes": patient.medical_notes,
            "created_at": patient.created_at
        }
        return PatientResponse(**patient_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Patient update error")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Delete patient (soft delete via marking as archived)"""
    try:
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        db.delete(patient)
        db.commit()

        return {"message": "Patient deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Patient deletion error")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VOICE/TEXT PRESCRIPTION ENDPOINTS (AI-Oriented App)
# ============================================================================

@app.post("/api/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = "fr",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Transcribe audio file to text using Whisper"""
    temp_audio_path = None
    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_audio_path = os.path.join(temp_dir, f"audio_{uuid.uuid4()}.wav")

        with open(temp_audio_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Transcribe using Whisper
        text, confidence = transcribe_audio(temp_audio_path, language=language)

        logger.info(f"Transcription completed: {len(text)} chars, confidence: {confidence:.2%}")

        return TranscriptionResponse(
            text=text,
            confidence=confidence,
            language=language
        )
    except Exception as e:
        logger.exception("Transcription error")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


@app.post("/api/prescriptions/voice", response_model=PrescriptionValidationResponse)
async def create_voice_prescription(
    patient_id: str = Form(...),
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Create prescription from voice input with validation"""
    temp_audio_path = None
    try:
        # Get patient data
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Transcribe audio if file provided
        transcribed_text = None
        if file:
            temp_dir = tempfile.gettempdir()
            temp_audio_path = os.path.join(temp_dir, f"audio_{uuid.uuid4()}.wav")

            with open(temp_audio_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            transcribed_text, _ = transcribe_audio(temp_audio_path, language="fr")

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="No audio provided or transcription failed")

        # Parse patient data
        patient_allergies = json.loads(patient.allergies) if patient.allergies else []
        patient_conditions = json.loads(patient.chronic_conditions) if patient.chronic_conditions else []
        current_medications = json.loads(patient.current_medications) if patient.current_medications else []

        # Calculate patient age
        from datetime import datetime as dt
        patient_age = (dt.utcnow().date() - patient.date_of_birth.date()).days // 365

        # Structure and validate prescription using LLM
        structured, validation = await structure_prescription_data(
            transcribed_text,
            patient.id,
            patient_age,
            patient_conditions,
            patient_allergies,
            current_medications
        )

        # Save prescription if valid
        if validation["valid"]:
            prescription = Prescription(
                id=str(uuid.uuid4()),
                org_id=current_user.org_id,
                created_by=current_user.id,
                patient_id=patient.id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=str(patient_age),
                diagnosis=structured.get("diagnosis", ""),
                medication=structured.get("medication", ""),
                dosage=structured.get("dosage", ""),
                duration=structured.get("duration") or "30 days",
                special_instructions=structured.get("special_instructions"),
                status="draft"
            )
            db.add(prescription)
            db.commit()
            db.refresh(prescription)

            # Update patient record with discovered allergies
            if structured.get("allergies"):
                allergies_str = structured.get("allergies", "").strip()
                if allergies_str and allergies_str.lower() not in ["aucune", "none", "no", "non"]:
                    # Add to patient allergies if not already present (with deduplication)
                    patient_allergies.append(allergies_str)
                    # Deduplicate to avoid "allergie aux orthies" and "orthies" both being saved
                    patient_allergies = deduplicate_items(patient_allergies)
                    patient.allergies = json.dumps(patient_allergies)
                    db.commit()
                    logger.info(f"Updated patient {patient.id} with allergy: {allergies_str} (deduplicated: {patient_allergies})")

            prescription_response = PrescriptionResponse(
                id=prescription.id,
                patient_name=prescription.patient_name,
                patient_age=prescription.patient_age,
                diagnosis=prescription.diagnosis,
                medication=prescription.medication,
                dosage=prescription.dosage,
                duration=prescription.duration,
                special_instructions=prescription.special_instructions,
                status=prescription.status,
                created_by=prescription.created_by,
                created_at=prescription.created_at,
                is_signed=prescription.is_signed,
                doctor_signed_at=prescription.doctor_signed_at
            )
        else:
            # Return with validation errors but no saved prescription
            prescription_response = None

        patient_response = PatientResponse(
            id=patient.id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            phone=patient.phone,
            email=patient.email,
            address=patient.address,
            allergies=patient_allergies,
            chronic_conditions=patient_conditions,
            current_medications=current_medications,
            medical_notes=patient.medical_notes,
            created_at=patient.created_at
        )

        return PrescriptionValidationResponse(
            prescription=prescription_response,
            validation=validation,
            patient_summary=patient_response,
            structured_data=structured
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Voice prescription creation error")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


@app.post("/api/prescriptions/text", response_model=PrescriptionValidationResponse)
async def create_text_prescription(
    request: TextPrescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Create prescription from text input with validation"""
    try:
        # Get patient data
        patient = db.query(Patient).filter(
            Patient.id == request.patient_id,
            Patient.org_id == current_user.org_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Parse patient data
        patient_allergies = json.loads(patient.allergies) if patient.allergies else []
        patient_conditions = json.loads(patient.chronic_conditions) if patient.chronic_conditions else []
        current_medications = json.loads(patient.current_medications) if patient.current_medications else []

        # Calculate patient age
        from datetime import datetime as dt
        patient_age = (dt.utcnow().date() - patient.date_of_birth.date()).days // 365

        # Structure and validate prescription using LLM
        structured, validation = await structure_prescription_data(
            request.prescription_text,
            patient.id,
            patient_age,
            patient_conditions,
            patient_allergies,
            current_medications
        )

        # Save prescription if valid
        if validation["valid"]:
            prescription = Prescription(
                id=str(uuid.uuid4()),
                org_id=current_user.org_id,
                created_by=current_user.id,
                patient_id=patient.id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=str(patient_age),
                diagnosis=structured.get("diagnosis", ""),
                medication=structured.get("medication", ""),
                dosage=structured.get("dosage", ""),
                duration=structured.get("duration") or "30 days",
                special_instructions=structured.get("special_instructions"),
                status="draft"
            )
            db.add(prescription)
            db.commit()
            db.refresh(prescription)

            # Update patient record with discovered allergies
            if structured.get("allergies"):
                allergies_str = structured.get("allergies", "").strip()
                if allergies_str and allergies_str.lower() not in ["aucune", "none", "no", "non"]:
                    # Add to patient allergies if not already present (with deduplication)
                    patient_allergies.append(allergies_str)
                    # Deduplicate to avoid "allergie aux orthies" and "orthies" both being saved
                    patient_allergies = deduplicate_items(patient_allergies)
                    patient.allergies = json.dumps(patient_allergies)
                    db.commit()
                    logger.info(f"Updated patient {patient.id} with allergy: {allergies_str} (deduplicated: {patient_allergies})")

            prescription_response = PrescriptionResponse(
                id=prescription.id,
                patient_name=prescription.patient_name,
                patient_age=prescription.patient_age,
                diagnosis=prescription.diagnosis,
                medication=prescription.medication,
                dosage=prescription.dosage,
                duration=prescription.duration,
                special_instructions=prescription.special_instructions,
                status=prescription.status,
                created_by=prescription.created_by,
                created_at=prescription.created_at,
                is_signed=prescription.is_signed,
                doctor_signed_at=prescription.doctor_signed_at
            )
        else:
            prescription_response = None

        patient_response = PatientResponse(
            id=patient.id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            phone=patient.phone,
            email=patient.email,
            address=patient.address,
            allergies=patient_allergies,
            chronic_conditions=patient_conditions,
            current_medications=current_medications,
            medical_notes=patient.medical_notes,
            created_at=patient.created_at
        )

        return PrescriptionValidationResponse(
            prescription=prescription_response,
            validation=validation,
            patient_summary=patient_response,
            structured_data=structured
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Text prescription creation error")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTERVENTIONS (Follow-up Actions)
# ============================================================================

@app.post("/api/interventions", response_model=InterventionResponse)
async def create_intervention(
    data: InterventionCreate,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a new intervention (doctor only)"""
    # Only doctors can create interventions
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create interventions")

    # Verify prescription exists and belongs to same org
    prescription = db.query(Prescription).filter(
        Prescription.id == data.prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Create intervention
    intervention = Intervention(
        id=str(uuid.uuid4()),
        org_id=current_user.org_id,
        prescription_id=data.prescription_id,
        created_by=current_user.user_id,
        intervention_type=sanitize_input(data.intervention_type),
        description=sanitize_input(data.description) if data.description else None,
        scheduled_date=data.scheduled_date,
        priority=data.priority,
        status="scheduled"
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    return InterventionResponse(
        id=intervention.id,
        prescription_id=intervention.prescription_id,
        intervention_type=intervention.intervention_type,
        description=intervention.description,
        scheduled_date=intervention.scheduled_date,
        priority=intervention.priority,
        status=intervention.status,
        created_by=intervention.created_by,
        created_at=intervention.created_at,
        updated_at=intervention.updated_at
    )


@app.get("/api/interventions")
async def list_interventions(
    prescription_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List interventions (filtered by prescription_id if provided)"""
    query = db.query(Intervention).filter(Intervention.org_id == current_user.org_id)

    if prescription_id:
        query = query.filter(Intervention.prescription_id == prescription_id)

    if status:
        query = query.filter(Intervention.status == status)

    interventions = query.all()

    return [
        InterventionListResponse(
            id=i.id,
            prescription_id=i.prescription_id,
            intervention_type=i.intervention_type,
            scheduled_date=i.scheduled_date,
            priority=i.priority,
            status=i.status,
            created_at=i.created_at
        )
        for i in interventions
    ]


@app.get("/api/interventions/{intervention_id}", response_model=InterventionDetailResponse)
async def get_intervention(
    intervention_id: str,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get intervention details with logs"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    logs = db.query(InterventionLog).filter(
        InterventionLog.intervention_id == intervention_id
    ).all()

    return InterventionDetailResponse(
        id=intervention.id,
        prescription_id=intervention.prescription_id,
        intervention_type=intervention.intervention_type,
        description=intervention.description,
        scheduled_date=intervention.scheduled_date,
        priority=intervention.priority,
        status=intervention.status,
        created_by=intervention.created_by,
        created_at=intervention.created_at,
        updated_at=intervention.updated_at,
        logs=[
            InterventionLogResponse(
                id=log.id,
                intervention_id=log.intervention_id,
                logged_by=log.logged_by,
                status_change=log.status_change,
                notes=log.notes,
                logged_at=log.logged_at
            )
            for log in logs
        ]
    )


@app.put("/api/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: str,
    data: InterventionUpdate,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update intervention (doctor only, only if scheduled)"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can update interventions")

    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if intervention.status != "scheduled":
        raise HTTPException(status_code=400, detail="Can only update scheduled interventions")

    # Update fields if provided
    if data.intervention_type:
        intervention.intervention_type = sanitize_input(data.intervention_type)
    if data.description:
        intervention.description = sanitize_input(data.description)
    if data.scheduled_date:
        intervention.scheduled_date = data.scheduled_date
    if data.priority:
        intervention.priority = data.priority

    intervention.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(intervention)

    return InterventionResponse(
        id=intervention.id,
        prescription_id=intervention.prescription_id,
        intervention_type=intervention.intervention_type,
        description=intervention.description,
        scheduled_date=intervention.scheduled_date,
        priority=intervention.priority,
        status=intervention.status,
        created_by=intervention.created_by,
        created_at=intervention.created_at,
        updated_at=intervention.updated_at
    )


@app.delete("/api/interventions/{intervention_id}")
async def delete_intervention(
    intervention_id: str,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete intervention (doctor only, only if scheduled)"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can delete interventions")

    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if intervention.status != "scheduled":
        raise HTTPException(status_code=400, detail="Can only delete scheduled interventions")

    db.delete(intervention)
    db.commit()

    return {"message": "Intervention deleted"}


@app.post("/api/interventions/{intervention_id}/log", response_model=InterventionLogResponse)
async def log_intervention(
    intervention_id: str,
    data: InterventionLogCreate,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Log intervention completion/status change (doctor or nurse)"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    # Create log entry
    log = InterventionLog(
        id=str(uuid.uuid4()),
        intervention_id=intervention_id,
        logged_by=current_user.user_id,
        status_change=sanitize_input(data.status_change),
        notes=sanitize_input(data.notes) if data.notes else None
    )
    db.add(log)

    # Update intervention status based on status_change
    if "→" in data.status_change:
        new_status = data.status_change.split("→")[-1].strip()
        if new_status in ["scheduled", "in_progress", "completed", "cancelled"]:
            intervention.status = new_status
            intervention.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(log)

    return InterventionLogResponse(
        id=log.id,
        intervention_id=log.intervention_id,
        logged_by=log.logged_by,
        status_change=log.status_change,
        notes=log.notes,
        logged_at=log.logged_at
    )


@app.post("/api/interventions/{intervention_id}/documents", response_model=InterventionDocumentResponse)
async def upload_intervention_document(
    intervention_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("note"),
    caption: Optional[str] = Form(None),
    log_id: Optional[str] = Form(None),
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload document to intervention log"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    # If no log_id provided, use the most recent log
    if not log_id:
        latest_log = db.query(InterventionLog).filter(
            InterventionLog.intervention_id == intervention_id
        ).order_by(InterventionLog.logged_at.desc()).first()

        if not latest_log:
            raise HTTPException(status_code=400, detail="No intervention logs found")
        log_id = latest_log.id
    else:
        # Verify log belongs to this intervention
        log = db.query(InterventionLog).filter(
            InterventionLog.id == log_id,
            InterventionLog.intervention_id == intervention_id
        ).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

    # Save file
    file_content = await file.read()
    file_size = len(file_content)

    # Create temp file path
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    file_path = f"documents/interventions/{intervention_id}/{str(uuid.uuid4())}.{file_ext}"

    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write file
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Create document record
    document = InterventionDocument(
        id=str(uuid.uuid4()),
        log_id=log_id,
        document_type=document_type,
        file_path=file_path,
        file_name=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        caption=sanitize_input(caption) if caption else None
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return InterventionDocumentResponse(
        id=document.id,
        log_id=document.log_id,
        document_type=document.document_type,
        file_name=document.file_name,
        file_path=document.file_path,
        mime_type=document.mime_type,
        file_size=document.file_size,
        caption=document.caption,
        uploaded_at=document.uploaded_at
    )


@app.get("/api/interventions/{intervention_id}/logs")
async def get_intervention_logs(
    intervention_id: str,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all logs for an intervention"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    logs = db.query(InterventionLog).filter(
        InterventionLog.intervention_id == intervention_id
    ).order_by(InterventionLog.logged_at.desc()).all()

    return [
        InterventionLogResponse(
            id=log.id,
            intervention_id=log.intervention_id,
            logged_by=log.logged_by,
            status_change=log.status_change,
            notes=log.notes,
            logged_at=log.logged_at
        )
        for log in logs
    ]


@app.get("/api/interventions/{intervention_id}/documents")
async def get_intervention_documents(
    intervention_id: str,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all documents for an intervention"""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.org_id == current_user.org_id
    ).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    # Get all logs for this intervention
    logs = db.query(InterventionLog).filter(
        InterventionLog.intervention_id == intervention_id
    ).all()
    log_ids = [log.id for log in logs]

    # Get all documents from these logs
    documents = db.query(InterventionDocument).filter(
        InterventionDocument.log_id.in_(log_ids)
    ).order_by(InterventionDocument.uploaded_at.desc()).all()

    return [
        InterventionDocumentResponse(
            id=doc.id,
            log_id=doc.log_id,
            document_type=doc.document_type,
            file_name=doc.file_name,
            file_path=doc.file_path,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            caption=doc.caption,
            uploaded_at=doc.uploaded_at
        )
        for doc in documents
    ]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
