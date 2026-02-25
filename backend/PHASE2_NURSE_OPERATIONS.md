# Phase 2: Nurse Field Operations

Complete guide for nurse features and patient visit management.

## Overview

Phase 2 enables nurses to manage field operations:
- View daily/weekly schedules
- Track patient visits
- Mark visits as complete
- Capture patient signatures (consent)
- Record device information

## New Endpoints

### Doctor Operations (Creates Visits)

#### Create Patient Visit Assignment
**POST** `/api/patient-visits`

Assign a nurse to visit a patient for device delivery.

```bash
curl -X POST http://localhost:8080/api/patient-visits \
  -H "Authorization: Bearer <doctor_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "assigned_nurse": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "patient_address": "123 Rue de Paris, 75001 Paris",
    "scheduled_date": "2026-02-26T14:00:00"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "pending"
}
```

#### List All Visits
**GET** `/api/patient-visits?status=pending&date_from=2026-02-26T00:00:00&date_to=2026-02-26T23:59:59`

Doctor sees all organization visits.

```bash
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/patient-visits"
```

Response:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "patient_name": "Jean Martin",
    "diagnosis": "Hypertension",
    "patient_address": "123 Rue de Paris, 75001 Paris",
    "scheduled_date": "2026-02-26T14:00:00",
    "status": "pending",
    "created_at": "2026-02-25T10:00:00"
  }
]
```

---

### Nurse Operations (Field Work)

#### Get My Daily Schedule
**GET** `/api/patient-visits?date_from=2026-02-26T00:00:00&date_to=2026-02-26T23:59:59`

Nurses see only their assigned visits, filtered by date.

```bash
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits?date_from=2026-02-26T00:00:00&date_to=2026-02-26T23:59:59"
```

Response: List of visits assigned to this nurse.

#### Get Visit Details
**GET** `/api/patient-visits/{visit_id}`

View full prescription and visit information before going to patient home.

```bash
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits/550e8400-e29b-41d4-a716-446655440001"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
  "assigned_nurse": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "patient_address": "123 Rue de Paris, 75001 Paris",
  "scheduled_date": "2026-02-26T14:00:00",
  "status": "pending",
  "patient_name": "Jean Martin",
  "patient_age": "52",
  "diagnosis": "Hypertension",
  "medication": "Amlodipine",
  "dosage": "5mg daily",
  "duration": "30 days",
  "special_instructions": "Take with water in the morning",
  "nurse_notes": null,
  "device_serial_installed": null,
  "patient_signature": null,
  "completed_at": null
}
```

#### Mark Visit In Progress
**PUT** `/api/patient-visits/{visit_id}/status`

When arriving at patient home, mark visit as in progress.

```bash
curl -X PUT "http://localhost:8080/api/patient-visits/550e8400-e29b-41d4-a716-446655440001/status" \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "in_progress"
}
```

#### Complete Visit with Signature
**POST** `/api/patient-visits/{visit_id}/complete`

Mark visit complete with patient signature and notes.

```bash
curl -X POST "http://localhost:8080/api/patient-visits/550e8400-e29b-41d4-a716-446655440001/complete" \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nurse_notes": "Device installed successfully. Patient trained on usage. Device at bedside. No complications.",
    "device_serial_installed": "SN-2024-001234",
    "patient_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ..."
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "completed_at": "2026-02-26T14:45:00"
}
```

---

## Workflow Example

### 1. Doctor Creates Prescription
```bash
# Doctor creates prescription
curl -X POST http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer <doctor_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Jean Martin",
    "patient_age": "52",
    "diagnosis": "Hypertension",
    "medication": "Amlodipine",
    "dosage": "5mg daily",
    "duration": "30 days",
    "special_instructions": "Take with water"
  }'

# Response: {"id": "550e8400-...", ...}
```

### 2. Doctor Assigns Nurse to Visit
```bash
# Doctor creates visit for nurse
curl -X POST http://localhost:8080/api/patient-visits \
  -H "Authorization: Bearer <doctor_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "assigned_nurse": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "patient_address": "123 Rue de Paris, 75001 Paris",
    "scheduled_date": "2026-02-26T14:00:00"
  }'

# Response: {"id": "visit-id-123", "status": "pending"}
```

### 3. Nurse Views Schedule
```bash
# Nurse checks today's schedule
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits?date_from=2026-02-26T00:00:00"

# Response: [{ visit 1 }, { visit 2 }, ...]
```

### 4. Nurse Views Details
```bash
# Nurse reviews prescription before visit
curl -H "Authorization: Bearer <nurse_token>" \
  "http://localhost:8080/api/patient-visits/visit-id-123"

# Response: Full prescription + visit details
```

### 5. Nurse Marks In Progress
```bash
# Nurse arrives at home and marks in progress
curl -X PUT "http://localhost:8080/api/patient-visits/visit-id-123/status" \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### 6. Nurse Completes Visit
```bash
# Nurse installs device, gets signature, records notes
curl -X POST "http://localhost:8080/api/patient-visits/visit-id-123/complete" \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nurse_notes": "Installation complete. Patient trained.",
    "device_serial_installed": "SN-2024-001234",
    "patient_signature": "data:image/png;base64,..."
  }'

# Response: {"id": "...", "status": "completed", "completed_at": "..."}
```

### 7. Doctor Sees Completion
```bash
# Doctor verifies all visits are complete
curl -H "Authorization: Bearer <doctor_token>" \
  "http://localhost:8080/api/patient-visits"

# Response: All visits with updated statuses and completion details
```

---

## Data Model

### PatientVisit
- `id`: Unique identifier
- `prescription_id`: Link to prescription
- `assigned_nurse`: Nurse user ID
- `patient_address`: Delivery address
- `scheduled_date`: Appointment time
- `status`: `pending` → `in_progress` → `completed` or `cancelled`
- `created_at`: Creation timestamp

### VisitDetail (created on completion)
- `id`: Unique identifier
- `visit_id`: Link to visit
- `nurse_notes`: Notes from nurse (e.g., "Device installed, patient trained")
- `device_serial_installed`: Device serial number installed
- `patient_signature`: Base64 encoded signature (consent)
- `completed_at`: Completion timestamp

---

## Access Control

### Doctor Can:
- ✅ Create prescriptions
- ✅ Create patient visit assignments
- ✅ View all organization visits
- ✅ View visit completion details
- ❌ Mark visits as complete

### Nurse Can:
- ✅ View only their assigned visits
- ✅ Filter visits by date (daily schedule)
- ✅ View prescription details
- ✅ Update visit status (pending → in_progress → completed)
- ✅ Mark visits complete with signature
- ❌ Create visits
- ❌ Create prescriptions

---

## Frontend Implementation Tips

### Nurse Schedule View
- Fetch visits with date filters for today/week
- Display as card list or calendar
- Sort by scheduled_date
- Color code by status (gray=pending, blue=in_progress, green=completed)

### Visit Detail Screen
- Show prescription info (patient, diagnosis, medication)
- Display patient address (can integrate with maps)
- Show special instructions
- Have "Start Visit" button (updates status)

### Device Installation Screen
- Barcode scanner for device serial
- Text area for notes
- Signature capture widget
- "Complete Visit" button

### Signature Capture
- Use Canvas or signature library
- Convert to PNG
- Base64 encode
- Send as: `data:image/png;base64,...`

---

## Phase 3 Preview

After Phase 2 works, Phase 3 will add:
- 📍 GPS tracking for nurses
- 📸 Photo attachments
- 📦 Device inventory management
- 📊 Real-time status updates (WebSocket)
- 📱 Offline mode (sync when online)
