"""
Vocalis Backend - Healthcare Device Delivery Platform
Multi-user system with authentication, prescriptions, and LLM-powered assistance
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
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
from datetime import datetime

# Local imports
from database import get_db, init_db, engine, Base
from models import User, Prescription, Organization, UserRole, PatientVisit, Device
from schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, CurrentUserResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse, PrescriptionListResponse,
    PatientVisitCreate, PatientVisitUpdate, PatientVisitListResponse, PatientVisitDetailResponse,
    VisitCompleteRequest
)
from auth import (
    hash_password, verify_password, create_access_token, verify_token, TokenData
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
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
