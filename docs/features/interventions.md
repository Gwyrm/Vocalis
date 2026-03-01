# Patient Follow-up Interventions

The Intervention Management System enables doctors to schedule patient follow-up interventions linked to prescriptions, and allows nurses to log completion and track progress through a workflow.

## Overview

Interventions are clinical follow-up actions prescribed by doctors for patients after prescriptions are issued. They include:

- **Doctor-initiated scheduling** - Doctors create interventions on prescriptions
- **Nurse workflow** - Nurses log completion with status transitions
- **Status tracking** - Visual timeline showing progression (scheduled → in_progress → completed)
- **Priority levels** - Low, normal, or high priority
- **Customizable types** - Various intervention types (e.g., follow-up visit, lab work, device adjustment)
- **Document attachments** - Upload supporting documents (test results, notes, etc.)

## Key Features

### Status Workflow

Interventions follow a state machine:

```
scheduled → in_progress → completed
   ↓                           ↑
   └─────→ cancelled ──────────┘
```

- **Scheduled**: Initial state when doctor creates intervention
- **In Progress**: Nurse has started the intervention
- **Completed**: Intervention finished with documentation
- **Cancelled**: Intervention was cancelled (if needed)

### Priority Levels

- **Low** - Routine follow-up
- **Normal** - Standard follow-up (default)
- **High** - Urgent follow-up required

### Intervention Types

Customizable types include:
- Follow-up visit
- Phone consultation
- Lab work
- Device adjustment
- Prescription refill
- Patient education
- And more...

## API Endpoints

### Create Intervention (Doctor Only)

**POST** `/api/interventions`

Create a new follow-up intervention for a patient prescription.

**Request:**
```json
{
  "prescription_id": "uuid",
  "patient_id": "uuid",
  "intervention_type": "follow-up visit",
  "scheduled_date": "2026-03-15T10:00:00Z",
  "priority": "normal",
  "description": "Post-treatment follow-up assessment",
  "notes": "Check for side effects and medication effectiveness"
}
```

**Response:**
```json
{
  "id": "uuid",
  "prescription_id": "uuid",
  "patient_id": "uuid",
  "organization_id": "uuid",
  "created_by": "doctor_user_id",
  "intervention_type": "follow-up visit",
  "scheduled_date": "2026-03-15T10:00:00Z",
  "priority": "normal",
  "description": "Post-treatment follow-up assessment",
  "notes": "Check for side effects and medication effectiveness",
  "status": "scheduled",
  "created_at": "2026-03-01T12:00:00Z"
}
```

### List Interventions

**GET** `/api/interventions`

List all interventions for the organization (doctors) or assigned to the nurse (nurses).

**Query Parameters:**
- `status` (optional) - Filter by status (scheduled, in_progress, completed, cancelled)
- `priority` (optional) - Filter by priority (low, normal, high)
- `start_date` (optional) - Filter interventions >= this date
- `end_date` (optional) - Filter interventions <= this date

**Response:**
```json
{
  "interventions": [
    {
      "id": "uuid",
      "prescription_id": "uuid",
      "patient_id": "uuid",
      "patient_name": "John Doe",
      "intervention_type": "follow-up visit",
      "scheduled_date": "2026-03-15T10:00:00Z",
      "priority": "normal",
      "status": "scheduled",
      "created_by": "doctor_name"
    }
  ],
  "total": 10
}
```

### Get Intervention Details

**GET** `/api/interventions/{intervention_id}`

Get full details of a specific intervention including logs and documents.

**Response:**
```json
{
  "id": "uuid",
  "prescription_id": "uuid",
  "patient_id": "uuid",
  "intervention_type": "follow-up visit",
  "scheduled_date": "2026-03-15T10:00:00Z",
  "priority": "normal",
  "description": "Post-treatment follow-up assessment",
  "status": "scheduled",
  "created_by": "doctor_user_id",
  "created_at": "2026-03-01T12:00:00Z",
  "logs": [
    {
      "id": "uuid",
      "status": "in_progress",
      "timestamp": "2026-03-15T10:15:00Z",
      "notes": "Started intervention",
      "logged_by": "nurse_user_id"
    }
  ],
  "documents": [
    {
      "id": "uuid",
      "file_name": "test_results.pdf",
      "file_path": "s3://...",
      "uploaded_at": "2026-03-15T11:00:00Z",
      "uploaded_by": "nurse_user_id"
    }
  ]
}
```

### Update Intervention (Doctor Only)

**PUT** `/api/interventions/{intervention_id}`

Update intervention details (scheduled status only).

**Request:**
```json
{
  "scheduled_date": "2026-03-20T14:00:00Z",
  "priority": "high",
  "description": "Updated description",
  "notes": "Updated notes"
}
```

### Delete Intervention (Doctor Only)

**DELETE** `/api/interventions/{intervention_id}`

Delete an intervention (scheduled status only).

**Status Code:** 204 No Content

### Log Intervention Status

**POST** `/api/interventions/{intervention_id}/logs`

Nurse logs status change for an intervention.

**Request:**
```json
{
  "status": "in_progress",
  "notes": "Patient arrived for follow-up visit"
}
```

**Response:**
```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "status": "in_progress",
  "timestamp": "2026-03-15T10:15:00Z",
  "notes": "Patient arrived for follow-up visit",
  "logged_by": "nurse_user_id"
}
```

### Get Intervention Logs

**GET** `/api/interventions/{intervention_id}/logs`

Get all status logs for an intervention.

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "status": "scheduled",
      "timestamp": "2026-03-01T12:00:00Z",
      "notes": "Intervention created",
      "logged_by": "doctor_user_id"
    },
    {
      "id": "uuid",
      "status": "in_progress",
      "timestamp": "2026-03-15T10:15:00Z",
      "notes": "Patient arrived",
      "logged_by": "nurse_user_id"
    }
  ]
}
```

### Upload Document

**POST** `/api/interventions/{intervention_id}/documents`

Upload a document (test results, notes, etc.) for the intervention.

**Request:** (multipart/form-data)
```
file: <binary file>
description: "Lab test results"
```

**Response:**
```json
{
  "id": "uuid",
  "intervention_id": "uuid",
  "file_name": "lab_results.pdf",
  "file_path": "s3://...",
  "description": "Lab test results",
  "uploaded_at": "2026-03-15T11:00:00Z",
  "uploaded_by": "nurse_user_id"
}
```

### Get Intervention Documents

**GET** `/api/interventions/{intervention_id}/documents`

Get all documents for an intervention.

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "file_name": "lab_results.pdf",
      "file_path": "s3://...",
      "description": "Lab test results",
      "uploaded_at": "2026-03-15T11:00:00Z",
      "uploaded_by": "nurse_user_id"
    }
  ]
}
```

## Workflow Examples

### Complete Follow-up Intervention

1. **Doctor creates intervention**
   ```bash
   POST /api/interventions
   {
     "prescription_id": "rx-123",
     "patient_id": "pat-456",
     "intervention_type": "follow-up visit",
     "scheduled_date": "2026-03-15T10:00:00Z",
     "priority": "normal"
   }
   ```
   → Status: `scheduled`

2. **Nurse logs arrival**
   ```bash
   POST /api/interventions/{id}/logs
   {
     "status": "in_progress",
     "notes": "Patient arrived for follow-up"
   }
   ```
   → Status: `in_progress`

3. **Nurse uploads test results**
   ```bash
   POST /api/interventions/{id}/documents
   file: test_results.pdf
   ```

4. **Nurse completes intervention**
   ```bash
   POST /api/interventions/{id}/logs
   {
     "status": "completed",
     "notes": "Follow-up completed. Patient responsive to treatment."
   }
   ```
   → Status: `completed`

### Cancel Intervention

If intervention is no longer needed:

```bash
POST /api/interventions/{id}/logs
{
  "status": "cancelled",
  "notes": "Patient no longer needs follow-up"
}
```

## Access Control

### Doctor Permissions
- ✅ Create interventions
- ✅ Update interventions (scheduled status only)
- ✅ Delete interventions (scheduled status only)
- ✅ View all organization interventions
- ✅ View logs and documents

### Nurse Permissions
- ✅ View assigned interventions
- ✅ Log status changes
- ✅ Upload documents
- ✅ View logs and documents
- ❌ Create/modify/delete interventions

## Data Model

### Intervention
- `id` - UUID
- `prescription_id` - Foreign key to prescription
- `patient_id` - Foreign key to patient
- `organization_id` - Organization isolation
- `intervention_type` - Type of intervention
- `scheduled_date` - When intervention is scheduled
- `priority` - low/normal/high
- `description` - Detailed description
- `notes` - Additional notes
- `status` - Current status
- `created_by` - Doctor who created it
- `created_at` - Timestamp

### InterventionLog
- `id` - UUID
- `intervention_id` - Foreign key to intervention
- `status` - Status change
- `timestamp` - When status changed
- `notes` - What was done
- `logged_by` - Who made the change

### InterventionDocument
- `id` - UUID
- `intervention_id` - Foreign key to intervention
- `file_name` - Original file name
- `file_path` - S3 or storage path
- `description` - Document description
- `uploaded_at` - Upload timestamp
- `uploaded_by` - Who uploaded it
