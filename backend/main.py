"""
Vocalis Backend - Healthcare Device Delivery Platform
Multi-user system with authentication, prescriptions, and LLM-powered assistance
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
from database import get_db, init_db, engine, Base
from models import (
    User, Prescription, Organization, UserRole, PatientVisit, Device, VisitDetail,
    NurseLocation, PhotoAttachment, DeviceStatus, OfflineQueue,
    Patient, Medication, MedicationInteraction, DrugAllergy
)
from schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, CurrentUserResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse, PrescriptionListResponse,
    PatientVisitCreate, PatientVisitUpdate, PatientVisitListResponse, PatientVisitDetailResponse,
    VisitCompleteRequest,
    NurseLocationCreate, NurseLocationResponse, PhotoResponse,
    DeviceCreate, DeviceUpdateStatus, DeviceListResponse,
    VisitAnalytics, DeviceAnalytics, NurseAnalytics,
    OfflineQueueItem, OfflineSyncPush, OfflineSyncStatus, OfflineDataPackage, SyncConflict,
    PatientCreate, PatientUpdate, PatientResponse, MedicationResponse,
    VoicePrescriptionRequest, TextPrescriptionRequest, PrescriptionValidationResponse,
    TranscriptionResponse
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
# STARTUP & SHUTDOWN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup, cleanup on shutdown"""
    global ollama_available

    # Initialize database tables
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")

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

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

logger.info(f"CORS enabled for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
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

    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.org_id == token_data.org_id
    ).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


async def get_current_user_demo(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user - allows demo mode without authentication"""
    if not authorization:
        # Demo mode: create/return a default demo user
        demo_user = db.query(User).filter(User.email == "demo@demo.com").first()
        if not demo_user:
            org = db.query(Organization).first()
            if not org:
                org = Organization(name="Demo Organization", created_at=datetime.utcnow())
                db.add(org)
                db.flush()
            demo_user = User(
                email="demo@demo.com",
                password_hash="demo",
                full_name="Demo User",
                role="doctor",
                org_id=org.id,
                created_at=datetime.utcnow()
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        return demo_user

    # If auth header provided, validate it normally
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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

    return TokenResponse(access_token=token)


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""

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

    return TokenResponse(access_token=token)


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


# ============================================================================
# PRESCRIPTION ENDPOINTS
# ============================================================================

@app.post("/api/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(
    request: PrescriptionCreate,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db)
):
    """Create a new prescription (doctor only)"""

    prescription = Prescription(
        org_id=current_user.org_id,
        created_by=current_user.id,
        patient_name=sanitize_input(request.patient_name, 200),
        patient_age=sanitize_input(request.patient_age, 100),
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

    logger.info(f"Prescription created: {prescription.id} by {current_user.email}")

    return PrescriptionResponse.from_attributes(prescription)


@app.get("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prescription details"""

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return PrescriptionResponse.from_attributes(prescription)


@app.get("/api/prescriptions", response_model=list[PrescriptionListResponse])
async def list_prescriptions(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db)
):
    """Update prescription (doctor only)"""

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.org_id == current_user.org_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Update fields
    if request.patient_name:
        prescription.patient_name = sanitize_input(request.patient_name, 200)
    if request.patient_age:
        prescription.patient_age = sanitize_input(request.patient_age, 100)
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

    logger.info(f"Prescription updated: {prescription.id}")

    return PrescriptionResponse.from_attributes(prescription)


# ============================================================================
# PATIENT VISIT ENDPOINTS (Nurse field operations)
# ============================================================================

@app.post("/api/patient-visits", response_model=dict)
async def create_patient_visit(
    request: PatientVisitCreate,
    current_user: User = Depends(get_doctor),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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


@app.get("/api/patients", response_model=list[PatientResponse])
async def list_patients(
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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
        if request.allergies is not None:
            patient.allergies = json.dumps(request.allergies)
        if request.chronic_conditions is not None:
            patient.chronic_conditions = json.dumps(request.chronic_conditions)
        if request.current_medications is not None:
            patient.current_medications = json.dumps(request.current_medications)
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
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    request: VoicePrescriptionRequest,
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
):
    """Create prescription from voice input with validation"""
    temp_audio_path = None
    try:
        # Get patient data
        patient = db.query(Patient).filter(
            Patient.id == request.patient_id,
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

        # Structure and validate prescription
        structured, validation = structure_prescription_data(
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
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=str(patient_age),
                diagnosis=structured.get("diagnosis", ""),
                medication=structured.get("medication", ""),
                dosage=structured.get("dosage", ""),
                duration=structured.get("duration", "30 days"),
                special_instructions=structured.get("special_instructions"),
                status="active"
            )
            db.add(prescription)
            db.commit()
            db.refresh(prescription)

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
                created_at=prescription.created_at
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
    current_user: User = Depends(get_current_user_demo),
    db: Session = Depends(get_db)
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

        # Structure and validate prescription
        structured, validation = structure_prescription_data(
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
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=str(patient_age),
                diagnosis=structured.get("diagnosis", ""),
                medication=structured.get("medication", ""),
                dosage=structured.get("dosage", ""),
                duration=structured.get("duration", "30 days"),
                special_instructions=structured.get("special_instructions"),
                status="active"
            )
            db.add(prescription)
            db.commit()
            db.refresh(prescription)

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
                created_at=prescription.created_at
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
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
