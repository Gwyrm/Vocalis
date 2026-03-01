# Vocalis V0 - Core Features Documentation

**Status:** ✅ Complete & Tested
**Last Updated:** March 1, 2026

---

## Overview

Vocalis V0 is a medical prescription management system with doctor-assisted workflow. It focuses on **simplicity, core functionality, and security** for single-company medical practices.

### Key Principle
> **Simple, focused, and secure.** V0 provides essential features for prescription management with clear role-based access control. Complex audit trails and multi-tenant features are deferred to V1+.

---

## Architecture

### Tech Stack
- **Backend:** FastAPI (Python 3.11+)
- **Database:** SQLite (vocalis.db)
- **Authentication:** JWT with refresh token rotation
- **Models:** SQLAlchemy ORM
- **API:** REST with JSON

### Key Files
```
backend/
├── main.py              # API endpoints & business logic
├── models.py            # Database models
├── auth.py              # JWT & authentication
├── schemas.py           # Request/response validation
├── database.py          # DB initialization
└── test_v0_workflow.py  # Comprehensive test suite
```

---

## Core Features

### 1. User Management

**Roles:**
- **Doctor** - Can create prescriptions, sign them, schedule interventions
- **Nurse** - Can view patients, log intervention completions
- **Admin** - Full system access (future)

**Authentication:**
- Registration: `POST /api/auth/register`
- Login: `POST /api/auth/login`
- Token Refresh: `POST /api/auth/refresh` (automatic rotation)
- Logout: `POST /api/auth/logout`

**Endpoints:**
```bash
# Register doctor
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@clinic.com",
    "password": "SecurePass123",
    "full_name": "Dr. Sarah Johnson",
    "role": "doctor"
  }'

# Response includes access_token + refresh_token
```

### 2. Patient Management

**Scope:** Simple CRUD operations, open to all authenticated users

**Fields:**
- Basic info: first_name, last_name, date_of_birth, gender
- Contact: phone, email, address
- Medical: allergies, chronic_conditions, current_medications, medical_notes

**Endpoints:**
```bash
# Create patient
curl -X POST http://localhost:8080/api/patients \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_of_birth": "1980-01-15",
    "gender": "M",
    "allergies": ["Penicillin"],
    "chronic_conditions": ["Hypertension"]
  }'

# List patients
curl -X GET http://localhost:8080/api/patients \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get patient by ID
curl -X GET http://localhost:8080/api/patients/{patient_id} \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Update patient
curl -X PUT http://localhost:8080/api/patients/{patient_id} \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{...updates...}'

# Delete patient
curl -X DELETE http://localhost:8080/api/patients/{patient_id} \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3. Prescription Management (Medications & Medical Devices)

**Prescription Types:**
- **Medication Prescriptions** - Drugs, treatments, pharmaceutical interventions
- **Medical Device Prescriptions** - Equipment, devices, mobility aids, monitoring devices
- **Combined** - Both medications AND devices in single prescription

**Workflow:**
1. Doctor creates prescription (draft) - medications and/or devices
2. Doctor assigns medical devices to prescription
3. Prescription is AI-assisted (optional)
4. Doctor signs with digital signature
5. Prescription marked as "signed" and ready for delivery
6. Interventions scheduled as follow-up

**Status Stages:**
- `draft` - Initial creation
- `signed` - Doctor signature applied
- `completed` - All interventions done (future)
- `archived` - Historical record

**Device Management:**
- Create reusable device catalog
- Assign devices to prescriptions (quantity, instructions, priority)
- Track device status (available, assigned, in_use, maintenance, returned)
- Device history and utilization tracking

**Endpoints:**
```bash
# Create prescription
curl -X POST http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "...",
    "patient_name": "Jean Dupont",
    "patient_age": "44",
    "diagnosis": "Type 2 Diabetes",
    "medication": "Metformin",
    "dosage": "500mg",
    "duration": "30 days",
    "special_instructions": "Take with meals"
  }'

# List prescriptions
curl -X GET http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer $TOKEN"

# Get prescription by ID
curl -X GET http://localhost:8080/api/prescriptions/{prescription_id} \
  -H "Authorization: Bearer $TOKEN"

# SIGN PRESCRIPTION (Doctor only - 403 Forbidden for nurses)
curl -X PUT http://localhost:8080/api/prescriptions/{prescription_id}/sign \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signature_base64": "iVBORw0KGgo..."  # Base64 encoded PNG
  }'

# Update prescription
curl -X PUT http://localhost:8080/api/prescriptions/{prescription_id} \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{...updates...}'
```

### 3.1 Medical Device Integration

**Supported Medical Device Types:**
- Mobility aids: Walkers, canes, crutches, wheelchairs, scooters
- Monitoring devices: Blood pressure monitors, glucose meters, pulse oximeters
- Assistive devices: Hearing aids, compression stockings, braces
- Home medical equipment: Nebulizers, CPAPs, oxygen concentrators
- Bath/safety equipment: Grab bars, shower chairs, raised toilet seats
- Specialized: Feeding tubes, catheters, wound care supplies
- And many others...

**Device Management:**
```bash
# Create medical device (inventory)
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wheelchair - Folding Manual",
    "model": "WC-2024-Premium",
    "serial_number": "WC-2024-0001",
    "description": "Lightweight folding manual wheelchair"
  }'
# Get: DEVICE_ID

# List all devices
curl -X GET http://localhost:8080/api/devices \
  -H "Authorization: Bearer $TOKEN"

# Update device status
curl -X PATCH http://localhost:8080/api/devices/{device_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "available"}'
```

**Device Assignment to Prescription:**
```bash
# Add device to prescription (after creating prescription)
curl -X POST http://localhost:8080/api/prescriptions/{prescription_id}/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "quantity": 1,
    "instructions": "Use for mobility assistance",
    "priority": "high"
  }'

# Get devices for prescription
curl -X GET http://localhost:8080/api/prescriptions/{prescription_id}/devices \
  -H "Authorization: Bearer $TOKEN"

# Remove device from prescription
curl -X DELETE http://localhost:8080/api/prescriptions/{prescription_id}/devices/{device_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Device Status Tracking:**
- `available` - In inventory, not assigned
- `assigned` - Linked to prescription
- `in_use` - Delivered to patient
- `maintenance` - Under repair/service
- `returned` - Returned by patient

**Access Control Matrix:**

| Operation | Doctor | Nurse | Public |
|-----------|--------|-------|--------|
| Create prescription | ✅ | ✅ | ❌ |
| Edit prescription | ✅ (draft) | ✅ (draft) | ❌ |
| Add devices to Rx | ✅ | ✅ | ❌ |
| Read prescription | ✅ | ✅ | ❌ |
| **Sign prescription** | **✅ ONLY** | **❌** | **❌** |
| Manage devices | ✅ | ✅ | ❌ |
| Track device status | ✅ | ✅ | ❌ |
| Delete | ✅ | ✅ | ❌ |

**Important Note:** Only **doctors can sign prescriptions**. Nurses can create, edit, and manage prescriptions up until signing.

### 4. Prescription Signature

**Doctor-Only Feature** - Core security requirement

**How It Works:**
1. Doctor receives draft prescription
2. Doctor signs with digital signature (PNG image, Base64 encoded)
3. Signature stored with prescription
4. Timestamp recorded (doctor_signed_at)
5. Status changed to "signed"

**Example:**
```python
import base64

# Read signature image (PNG)
with open("doctor_signature.png", "rb") as f:
    signature_bytes = f.read()
    signature_b64 = base64.b64encode(signature_bytes).decode()

# Send to API
curl -X PUT http://localhost:8080/api/prescriptions/{id}/sign \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d "{\"signature_base64\": \"$signature_b64\"}"
```

**Security:**
- Nurse cannot sign (`get_doctor` dependency)
- Returns 403 Forbidden if not doctor
- Signature timestamp is immutable
- Cannot re-sign already signed prescription

### 5. Intervention Scheduling & Tracking

**Purpose:** Track follow-up tasks/monitoring for prescriptions

**Workflow:**
1. Doctor creates intervention for prescription (e.g., "Blood glucose check")
2. Intervention scheduled for specific date
3. Nurse logs completion with notes
4. Status transitions tracked

**Status Lifecycle:**
- `scheduled` - Initial creation
- `in_progress` - Work started
- `completed` - Work finished
- `cancelled` - Abandoned

**Endpoints:**
```bash
# Create intervention
curl -X POST http://localhost:8080/api/interventions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": "...",
    "intervention_type": "Blood glucose check",
    "description": "Check glucose and review medication",
    "scheduled_date": "2026-03-15T10:00:00",
    "priority": "normal"  # low, normal, high
  }'

# List interventions
curl -X GET http://localhost:8080/api/interventions \
  -H "Authorization: Bearer $TOKEN"

# Get intervention details
curl -X GET http://localhost:8080/api/interventions/{intervention_id} \
  -H "Authorization: Bearer $TOKEN"

# Log completion/status update (Nurse)
curl -X POST http://localhost:8080/api/interventions/{intervention_id}/log \
  -H "Authorization: Bearer $NURSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status_change": "scheduled→in_progress",
    "notes": "Patient contacted for appointment"
  }'

# Get intervention history/logs
curl -X GET http://localhost:8080/api/interventions/{intervention_id}/logs \
  -H "Authorization: Bearer $TOKEN"
```

---

## Complete V0 Workflow Example (Medications + Devices)

This example shows a complete prescription with **both medications AND medical devices**.

### Step 0: Setup Device Inventory
```bash
# Create medical device (add to inventory)
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "name":"Mobility Walker",
    "model":"MW-2024-Elite",
    "serial_number":"MW-2024-001",
    "description":"4-wheel walker with seat and brakes"
  }'
# Get: DEVICE_ID

# Create another device (optional)
curl -X POST http://localhost:8080/api/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "name":"Blood Pressure Monitor",
    "model":"BPM-2024",
    "serial_number":"BPM-2024-001",
    "description":"Home use automated blood pressure monitor"
  }'
```

### Step 1: Setup Users
```bash
# Register doctor
curl -X POST http://localhost:8080/api/auth/register \
  -d '{"email":"dr_smith@clinic.com","password":"Pass123!","full_name":"Dr. Smith","role":"doctor"}'
# Get: DOCTOR_TOKEN, doctor_id

# Register nurse
curl -X POST http://localhost:8080/api/auth/register \
  -d '{"email":"nurse_marie@clinic.com","password":"Pass123!","full_name":"Marie","role":"nurse"}'
# Get: NURSE_TOKEN
```

### Step 2: Create Patient
```bash
curl -X POST http://localhost:8080/api/patients \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "first_name":"John","last_name":"Smith","date_of_birth":"1965-05-20",
    "allergies":["Penicillin"]
  }'
# Get: PATIENT_ID
```

### Step 3: Create Prescription (Medications)
```bash
curl -X POST http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "patient_id":"'$PATIENT_ID'",
    "patient_name":"John Smith","patient_age":"61",
    "diagnosis":"Hypertension - Mobility Limited",
    "medication":"Lisinopril",
    "dosage":"10mg","duration":"30 days"
  }'
# Get: PRESCRIPTION_ID
```

### Step 3.5: Add Medical Devices to Prescription
```bash
# Add walker to prescription
curl -X POST http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "device_id":"'$DEVICE_ID'",
    "quantity":1,
    "instructions":"Use for mobility assistance, especially on stairs",
    "priority":"high"
  }'

# Add blood pressure monitor to prescription
curl -X POST http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "device_id":"'$BPM_DEVICE_ID'",
    "quantity":1,
    "instructions":"Check BP daily, log readings",
    "priority":"normal"
  }'

# View all devices on this prescription
curl -X GET http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/devices \
  -H "Authorization: Bearer $DOCTOR_TOKEN"
```

**Result:** Prescription now includes:
- ✅ Medication: Lisinopril 10mg
- ✅ Device 1: Mobility Walker (high priority)
- ✅ Device 2: Blood Pressure Monitor (normal priority)

### Step 4: Sign Prescription (Doctor)
```bash
# Create simple PNG signature (or use real one)
curl -X PUT http://localhost:8080/api/prescriptions/$PRESCRIPTION_ID/sign \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{"signature_base64":"iVBORw0KGgo..."}'
# Status: draft → signed
```

### Step 5: Sign Prescription with Signature
```bash
# Signature is now ready to be applied (medications + devices included)
# Status: draft → signed
# Both medications AND devices are now part of signed prescription
```

### Step 6: Schedule Follow-up Intervention
```bash
curl -X POST http://localhost:8080/api/interventions \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "prescription_id":"'$PRESCRIPTION_ID'",
    "intervention_type":"Walker delivery & training",
    "description":"Deliver mobility walker and provide usage training",
    "scheduled_date":"2026-03-10T14:00:00",
    "priority":"high"
  }'
# Get: INTERVENTION_ID
```

### Step 7: Nurse Logs Completion
```bash
curl -X POST http://localhost:8080/api/interventions/$INTERVENTION_ID/log \
  -H "Authorization: Bearer $NURSE_TOKEN" \
  -d '{"status_change":"scheduled→completed","notes":"Patient BP 130/85, stable"}'
```

---

## Testing

### Automated Tests
```bash
cd backend

# Run V0 workflow test (end-to-end)
python test_v0_workflow.py

# Output should show:
# ✓ Backend is running
# ✓ Doctor registered
# ✓ Nurse registered
# ✓ Patient created
# ✓ Prescription created
# ✓ Prescription signed
# ✓ Access control verified (nurse cannot sign)
# ✓ Intervention created
# ✓ Intervention logged
# ✓ ALL TESTS PASSED
```

### Manual Testing Checklist

**Authentication:**
- [ ] Doctor can register and login
- [ ] Nurse can register and login
- [ ] Invalid credentials return 401
- [ ] Refresh token works (get new access token)
- [ ] Logout revokes token

**Patient Management:**
- [ ] Create patient (any authenticated user)
- [ ] List patients (shows own org patients)
- [ ] Get patient by ID
- [ ] Update patient data
- [ ] Delete patient (removes from system)

**Prescription Workflow:**
- [ ] Doctor creates prescription (status: draft)
- [ ] Doctor can see unsigned prescriptions
- [ ] Doctor signs prescription with signature
- [ ] Signature timestamp recorded
- [ ] Status changes to "signed"
- [ ] Cannot re-sign already signed prescription

**Access Control:**
- [ ] Nurse attempts to sign → 403 Forbidden ✓
- [ ] Nurse can read prescriptions
- [ ] Nurse cannot create prescriptions
- [ ] Only creator/admin can update

**Interventions:**
- [ ] Doctor creates intervention
- [ ] Intervention shows in list
- [ ] Nurse logs status update
- [ ] Intervention history visible

---

## API Summary

### Authentication (4 endpoints)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/register` | POST | None | User registration |
| `/api/auth/login` | POST | None | User login |
| `/api/auth/refresh` | POST | None | Refresh access token |
| `/api/auth/logout` | POST | Bearer | Logout & revoke token |

### Patient Management (5 endpoints)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/patients` | POST | Bearer | Create patient |
| `/api/patients` | GET | Bearer | List patients |
| `/api/patients/{id}` | GET | Bearer | Get patient |
| `/api/patients/{id}` | PUT | Bearer | Update patient |
| `/api/patients/{id}` | DELETE | Bearer | Delete patient |

### Prescription Management (7 endpoints)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/prescriptions` | POST | Bearer | Create prescription (Doctor or Nurse) |
| `/api/prescriptions` | GET | Bearer | List prescriptions |
| `/api/prescriptions/{id}` | GET | Bearer | Get prescription details |
| `/api/prescriptions/{id}` | PUT | Bearer | Update prescription (draft only) |
| `/api/prescriptions/{id}/sign` | PUT | **Doctor** | **Sign prescription (DOCTOR ONLY)** |
| `/api/prescriptions/{id}/devices` | POST | Bearer | Add device to prescription |
| `/api/prescriptions/{id}/devices` | GET | Bearer | Get devices on prescription |

### Medical Device Management (4 endpoints)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/devices` | POST | Doctor | Create device (add to inventory) |
| `/api/devices` | GET | Bearer | List all devices |
| `/api/devices/{id}` | PATCH | Doctor | Update device status |
| `/api/devices/{id}/analytics` | GET | Doctor | Get device utilization metrics |

### Intervention Tracking (5 endpoints)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/interventions` | POST | Doctor | Create intervention (follow-up) |
| `/api/interventions` | GET | Bearer | List interventions |
| `/api/interventions/{id}` | GET | Bearer | Get intervention |
| `/api/interventions/{id}/log` | POST | Bearer | Log status update |
| `/api/interventions/{id}/logs` | GET | Bearer | Get intervention history |

**Total: 25 endpoints**

---

## Database Schema (Simplified for V0)

```sql
-- Users (authentication)
users
├── id (UUID)
├── email (unique)
├── password_hash
├── full_name
├── role (doctor, nurse)
└── org_id (foreign key)

-- Organizations (single for V0)
organizations
├── id (UUID)
├── name
└── created_at

-- Patients (simple CRUD)
patients
├── id (UUID)
├── org_id
├── first_name
├── last_name
├── date_of_birth
├── gender
├── phone
├── email
├── address
├── allergies (JSON)
├── chronic_conditions (JSON)
├── current_medications (JSON)
├── medical_notes
├── created_at
└── updated_at

-- Prescriptions (MEDICATIONS & DEVICES)
prescriptions
├── id (UUID)
├── org_id
├── created_by (user_id)
├── patient_id
├── patient_name
├── diagnosis
├── medication (primary medication)
├── dosage
├── duration
├── status (draft, signed, ...)
├── is_signed (boolean)
├── doctor_signature (Base64)
├── doctor_signed_at (datetime)
└── created_at
Note: Can have 0+ medications, linked with PrescriptionDevice table

-- Medical Devices (INVENTORY)
devices
├── id (UUID)
├── org_id
├── name (e.g., "Wheelchair", "Monitor")
├── model
├── serial_number (unique)
├── description
├── status (available, assigned, in_use, maintenance, returned)
└── created_at

-- Prescription-Device Link (MANY-TO-MANY)
prescription_devices
├── id (UUID)
├── prescription_id (foreign key)
├── device_id (foreign key)
├── quantity (how many of this device)
├── instructions (usage instructions for this device)
├── priority (low, normal, high)
└── created_at
Note: Links prescriptions to devices (one prescription can have multiple devices)

-- Interventions (follow-up tasks)
interventions
├── id (UUID)
├── org_id
├── prescription_id
├── created_by
├── intervention_type
├── description
├── scheduled_date
├── priority
├── status
└── created_at

-- Intervention Logs (audit trail for interventions)
intervention_logs
├── id (UUID)
├── intervention_id
├── logged_by
├── status_change
├── notes
└── logged_at
```

---

## Security Features

✅ **Implemented in V0:**
- JWT bearer token authentication
- Token refresh with rotation (prevents reuse)
- Password hashing with bcrypt
- Doctor-only prescription signature enforcement
- Organization data isolation
- Rate limiting on authentication endpoints (5/min)
- CORS configuration for frontend
- HTTPS ready (configure in production)

⏳ **Planned for V1+:**
- Full audit trail (who accessed what when)
- Detailed access logging
- Device fingerprinting
- Biometric re-authentication
- End-to-end encryption for sensitive data
- Automatic log cleanup policies

---

## Deployment

### Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables (see .env.example)
export JWT_SECRET="your-secret-key"
export DATABASE_URL="sqlite:///vocalis.db"

# Run backend
python main.py
# Server runs on http://localhost:8080
```

### Production (Future)
- Use PostgreSQL instead of SQLite
- Enable HTTPS/TLS
- Set strong JWT_SECRET
- Configure CORS for frontend domain
- Use reverse proxy (nginx)
- Add WAF (Web Application Firewall)
- Implement log aggregation
- Monitor API performance

---

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip install -r requirements.txt

# Check database file
ls -la backend/vocalis.db

# View startup logs
tail -f backend/backend.log
```

### Authentication Fails
```bash
# Check JWT_SECRET is set
echo $JWT_SECRET

# Verify token format (Bearer token)
curl -H "Authorization: Bearer $TOKEN"

# Test login endpoint
curl -X POST http://localhost:8080/api/auth/login \
  -d '{"email":"...","password":"..."}'
```

### Patient CRUD Not Working
```bash
# Check user has Bearer token
# Check user is authenticated

# Verify patient exists
curl http://localhost:8080/api/patients \
  -H "Authorization: Bearer $TOKEN"
```

---

## Next Steps (V1+)

### Phase 1: Audit & Compliance
- Full access logging for HIPAA
- Detailed change history
- Compliance reporting
- Document retention policies

### Phase 2: Advanced Workflow
- Prescription template library
- Device inventory management
- Multi-user device assignments
- GPS location tracking for nurses

### Phase 3: Scaling
- Multi-organization support
- Custom fields per organization
- Advanced analytics
- Mobile app optimization

---

## Support & Questions

### Documentation Files
- `V0_FEATURES.md` - This document
- `REFRESH_TOKENS.md` - Token management details
- `SECURITY_CONFIG.md` - Security configuration
- `RATE_LIMITING.md` - Rate limiting configuration

### Testing
- `test_v0_workflow.py` - Comprehensive integration test
- `test_patient_rights_phase1.py` - Legacy audit tests (can be removed in V1)

### Running Tests
```bash
# End-to-end V0 workflow test
cd backend
python test_v0_workflow.py

# Check health
curl http://localhost:8080/api/health
```

---

## Version Info
- **Release:** V0 (March 1, 2026)
- **Status:** ✅ Stable & Production Ready
- **Last Updated:** March 1, 2026
- **License:** Proprietary (Vocalis)
