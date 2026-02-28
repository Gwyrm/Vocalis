# System Design

## Architecture Overview

Vocalis uses a client-server architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   Client Layer                          │
│  Flutter Web/Mobile/Desktop Application                │
│  - UI Components                                        │
│  - State Management (Provider)                         │
│  - Local Storage (SharedPreferences)                   │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (HTTP/JSON)
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Server Layer                           │
│  FastAPI Backend                                        │
│  - Authentication (JWT)                                │
│  - API Endpoints                                       │
│  - Business Logic                                      │
│  - Data Validation                                     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌──────────┐
   │Database│  │Ollama  │  │Whisper   │
   │(SQLite)│  │(LLM)   │  │(Audio)   │
   └────────┘  └────────┘  └──────────┘
```

## Component Breakdown

### Frontend (Flutter)

**Responsibilities:**
- User interface for all platforms
- Form input and validation
- API communication
- Local state management
- Token persistence

**Key Screens:**
- LoginScreen - Authentication
- PatientListScreen - Patient management
- PatientDetailScreen - Prescription creation
- ValidationResultsScreen - Results review
- VoicePrescriptionScreen - Voice input
- TextPrescriptionScreen - Text input

**Technology:**
```dart
dependencies:
  flutter: latest
  provider: state management
  http: API calls
  shared_preferences: local storage
  signature: signature capture
  intl: date formatting
```

### Backend (FastAPI)

**Responsibilities:**
- REST API endpoints
- Authentication & authorization
- Data persistence
- Business logic
- LLM integration
- Input validation

**Components:**
- `main.py` - FastAPI application
- `database.py` - SQLAlchemy ORM
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic validation
- `auth.py` - JWT & password handling
- `voice_utils.py` - Whisper & LLM integration
- `llm_utils.py` - LLM interactions

**Technology:**
```python
dependencies:
  fastapi: web framework
  sqlalchemy: ORM
  python-jose: JWT
  passlib[bcrypt]: password hashing
  whisper: audio transcription
  httpx: async HTTP
```

### Database

**Purpose:** Persistent data storage

**Supports:**
- User accounts & authentication
- Patient information
- Prescriptions & history
- Organizations & roles

**Schema:**
```
Users
├── id (UUID)
├── email
├── password_hash (bcrypt)
├── full_name
├── role (DOCTOR/NURSE)
├── org_id (foreign key)
└── is_active

Patients
├── id (UUID)
├── org_id (foreign key)
├── first_name
├── last_name
├── date_of_birth
├── allergies
├── chronic_conditions
├── current_medications
└── created_at

Prescriptions
├── id (UUID)
├── patient_id (foreign key)
├── created_by (doctor id)
├── medication
├── dosage
├── duration
├── status (draft/signed)
├── is_signed
├── doctor_signed_at
└── created_at
```

## Data Flow

### Prescription Creation Flow

```
1. User Input (Flutter)
   └─► Text or Voice data

2. API Request (REST)
   └─► POST /api/prescriptions/text or /voice

3. Backend Processing (FastAPI)
   ├─► Extract text from audio (Whisper)
   ├─► Parse with LLM (Mistral)
   ├─► Validate medication/dosage
   └─► Store in database

4. Response (JSON)
   ├─► Extracted data (medication, dosage, duration)
   ├─► Validation results (errors/warnings)
   └─► Prescription ID

5. User Confirmation (Flutter)
   ├─► Review data
   └─► Click "Confirm"

6. Finalization (FastAPI)
   ├─► Mark as signed
   ├─► Set timestamp
   └─► Update status
```

## Security Architecture

### Authentication Flow

```
┌──────────┐
│  Login   │ POST /api/auth/login
└────┬─────┘
     │
     ▼
┌─────────────────────────┐
│  Validate Credentials   │
├─────────────────────────┤
│ 1. Find user in DB      │
│ 2. Hash password (bcrypt)
│ 3. Verify match        │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  Generate JWT Token     │
├─────────────────────────┤
│ Payload:                │
│ - user_id               │
│ - email                 │
│ - role                  │
│ - org_id                │
│ - exp (24 hours)        │
└────┬────────────────────┘
     │
     ▼
┌──────────────────────────┐
│  Return Token to Client  │
├──────────────────────────┤
│ Store in SharedPrefs     │
│ Include in all API calls │
│ Authorization: Bearer XX │
└──────────────────────────┘
```

### Permission Model

```
Resource Access:
├─ Doctor
│  ├─ Create prescriptions ✅
│  ├─ Confirm prescriptions ✅
│  ├─ View all org prescriptions ✅
│  └─ Manage patient data ✅
│
└─ Nurse
   ├─ Create prescriptions ✅
   ├─ Confirm prescriptions ❌
   ├─ View org prescriptions ✅
   └─ Limited patient management ⚠️
```

## API Endpoint Categories

### Authentication Endpoints
- `POST /api/auth/login` - Get JWT token
- `GET /api/auth/me` - Get current user
- `POST /api/users/change-password` - Change password

### Patient Endpoints
- `GET /api/patients` - List patients
- `GET /api/patients/{id}` - Get patient details
- `GET /api/patients/{id}/prescriptions` - Get history
- `PUT /api/patients/{id}` - Update patient info

### Prescription Endpoints
- `POST /api/prescriptions/text` - Create from text
- `POST /api/prescriptions/voice` - Create from audio
- `PUT /api/prescriptions/{id}/sign` - Confirm prescription
- `GET /api/prescriptions/{id}` - Get prescription details

## Error Handling

### HTTP Status Codes

```
200 - OK (successful request)
201 - Created (resource created)
400 - Bad Request (validation error)
401 - Unauthorized (missing/invalid token)
403 - Forbidden (permission denied)
404 - Not Found (resource doesn't exist)
422 - Unprocessable Entity (validation failed)
500 - Internal Server Error (unexpected error)
```

### Error Response Format

```json
{
  "detail": "Error message explaining what went wrong",
  "type": "error_type",
  "field": "field_name (if validation error)"
}
```

## Scalability Considerations

### Current Limitations
- Single-server deployment
- SQLite database (single-user)
- No caching layer

### Future Improvements
- PostgreSQL for multi-user support
- Redis for caching
- Message queue for async jobs
- Kubernetes deployment
- Multi-region support

## Performance Characteristics

### Typical Response Times
- Login: 50-100ms
- Get prescriptions: 50-150ms
- Create text prescription: 500-2000ms (includes LLM)
- Create voice prescription: 2000-5000ms (includes Whisper + LLM)
- Confirm prescription: 100-200ms

### Database Query Optimization
- Indexed on patient_id
- Indexed on created_by
- Indexed on created_at
- Organization-scoped queries

---

**Next:** Learn about [Database Schema](database.md)
