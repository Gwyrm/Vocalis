# Prescriptions API

Manage medical prescriptions with draft editing and signing workflow.

## Overview

Prescriptions in Vocalis follow a lifecycle:
1. **Draft** - Can be created and edited freely
2. **Signed** - Locked and read-only after doctor approval
3. **Completed** - Dispensed to patient

## Prescription Status

- **draft** - Prescription is editable, not yet confirmed
- **signed** - Prescription confirmed by doctor, cannot be edited
- **completed** - Prescription has been dispensed to patient

## Endpoints

### GET /api/prescriptions

List all prescriptions for the organization.

**Auth Required:** Yes (Bearer token)

**Query Parameters:**
```
page: integer (default: 1)
limit: integer (default: 10)
```

**Response (200):**
```json
[
  {
    "id": "uuid",
    "patient_name": "John Doe",
    "patient_age": "45",
    "diagnosis": "Bronchitis",
    "medication": "Amoxicilline",
    "dosage": "500mg, 3 times daily",
    "duration": "10 days",
    "special_instructions": "Take with food",
    "status": "draft",
    "created_by": "doctor-uuid",
    "created_at": "2026-02-28T10:30:00",
    "is_signed": false,
    "doctor_signed_at": null
  }
]
```

---

### GET /api/prescriptions/{id}

Get specific prescription details.

**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "prescription-uuid",
  "patient_name": "John Doe",
  "patient_age": "45",
  "diagnosis": "Bronchitis",
  "medication": "Amoxicilline",
  "dosage": "500mg, 3 times daily",
  "duration": "10 days",
  "special_instructions": "Take with food",
  "status": "draft",
  "created_by": "doctor-uuid",
  "created_at": "2026-02-28T10:30:00",
  "is_signed": false,
  "doctor_signed_at": null
}
```

**Error (404):**
```json
{"detail": "Prescription not found"}
```

---

### POST /api/prescriptions/text

Create prescription from text input.

**Auth Required:** Yes (Bearer token)

**Request:**
```json
{
  "patient_id": "uuid",
  "text_input": "Amoxicilline 500mg, three times daily for 10 days for bronchitis",
  "diagnosis": "Bronchitis (optional)"
}
```

**Response (200):**
```json
{
  "prescription": {
    "id": "uuid",
    "patient_name": "John Doe",
    "medication": "Amoxicilline",
    "dosage": "500mg, three times daily",
    "duration": "10 days",
    "status": "draft"
  },
  "validation": {
    "valid": true,
    "confidence": 0.95,
    "errors": [],
    "warnings": []
  }
}
```

---

### POST /api/prescriptions/voice

Create prescription from audio input (voice transcription + LLM extraction).

**Auth Required:** Yes

**Request (Multipart form data):**
```
audio_file: audio/wav or audio/mp3
patient_id: uuid
diagnosis: string (optional)
```

**Response (200):**
Same as POST /api/prescriptions/text

---

### PUT /api/prescriptions/{id}

Edit a draft prescription.

**Auth Required:** Yes (Doctor or Nurse)

**Important:** Only prescriptions with status "draft" can be edited. Signed prescriptions are read-only.

**Request:**
```json
{
  "medication": "Amoxicilline 250mg",
  "dosage": "2 times daily",
  "duration": "7 days",
  "diagnosis": "Mild bronchitis",
  "special_instructions": "Take with meals"
}
```

All fields are optional. Only provided fields will be updated.

**Response (200):**
```json
{
  "id": "prescription-uuid",
  "medication": "Amoxicilline 250mg",
  "dosage": "2 times daily",
  "duration": "7 days",
  "diagnosis": "Mild bronchitis",
  "special_instructions": "Take with meals",
  "status": "draft",
  "created_at": "2026-02-28T10:30:00",
  "is_signed": false
}
```

**Error (403):**
```json
{"detail": "Only draft prescriptions can be edited"}
```

**Error (404):**
```json
{"detail": "Prescription not found"}
```

---

### PUT /api/prescriptions/{id}/sign

Sign and finalize a prescription (doctor approval).

**Auth Required:** Yes (Bearer token)

**Request:**
```json
{
  "doctor_signature": ""
}
```

Signature field accepts Base64 encoded PNG or empty string.

**Response (200):**
```json
{
  "id": "prescription-uuid",
  "medication": "Amoxicilline",
  "dosage": "500mg, 3 times daily",
  "duration": "10 days",
  "status": "signed",
  "created_at": "2026-02-28T10:30:00",
  "is_signed": true,
  "doctor_signed_at": "2026-02-28T11:00:00"
}
```

**Error (404):**
```json
{"detail": "Prescription not found"}
```

---

## Prescription Workflow

### Creating a Prescription

1. **Choose Input Method:**
   - Text: `POST /api/prescriptions/text` with text description
   - Voice: `POST /api/prescriptions/voice` with audio file

2. **System Extracts Data:**
   - LLM parses text/audio
   - Extracts medication, dosage, duration
   - Validates against medication database
   - Returns structured data with warnings/errors

3. **Review & Validate:**
   - User sees validation results screen
   - Can edit patient information
   - Reviews any warnings or errors

4. **Sign or Edit:**
   - Click "Valider et enregistrer" to finalize (status: signed)
   - Or go back to edit prescription before signing

### Editing a Draft Prescription

1. **View prescription in patient history**
2. **If status is "draft":**
   - Click "Éditer" button
   - Modify any field (medication, dosage, etc.)
   - Click "Enregistrer" to save changes
3. **If status is "signed":**
   - No edit button shown
   - Prescription is read-only and locked

### Signing a Prescription

1. **Review prescription data**
2. **Click "Signer" button**
3. **Confirm on validation screen**
4. **Status changes to "signed"**
5. **Edit button disappears** - prescription is now locked

---

## Important Notes

### Draft vs. Signed

| Aspect | Draft | Signed |
|--------|-------|--------|
| Editable | ✅ Yes | ❌ No |
| Edit Button | ✅ Show | ❌ Hide |
| Sign Button | ✅ Show | ❌ Hide |
| Status Badge | ⏳ To sign | ✓ Signed |
| Can be modified | ✅ Yes | ❌ No |

### Editing Restrictions

- Only **draft** prescriptions can be edited
- Attempting to edit a **signed** prescription returns `403 Forbidden`
- Changes are validated and sanitized before saving
- Patient medical info can be updated via discovery fields

### Permissions

- **Doctors**: Can create, edit (draft only), and sign prescriptions
- **Nurses**: Can create and edit (draft only), cannot sign
- **Organization Isolation**: Users can only see prescriptions from their organization

---

## Error Handling

| Status | Error | Meaning |
|--------|-------|---------|
| 400 | Bad Request | Invalid input (missing required fields) |
| 403 | Forbidden | Cannot edit signed prescription |
| 404 | Not Found | Prescription doesn't exist |
| 422 | Validation Error | Prescription data invalid |
| 500 | Server Error | Internal error |

---

## Examples

### Example 1: Create and Sign Prescription

```bash
# Step 1: Create prescription from text
curl -X POST http://localhost:8080/api/prescriptions/text \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid",
    "text_input": "Amoxicilline 500mg, three times daily for 10 days"
  }'

# Returns: prescription with id and validation results

# Step 2: Edit before signing (optional)
curl -X PUT http://localhost:8080/api/prescriptions/PRESCRIPTION_ID \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dosage": "250mg, two times daily"
  }'

# Step 3: Sign prescription
curl -X PUT http://localhost:8080/api/prescriptions/PRESCRIPTION_ID/sign \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_signature": ""
  }'
```

### Example 2: Edit Draft Prescription

```bash
# Get current prescription
curl -X GET http://localhost:8080/api/prescriptions/PRESCRIPTION_ID \
  -H "Authorization: Bearer TOKEN"

# Edit if status is "draft"
curl -X PUT http://localhost:8080/api/prescriptions/PRESCRIPTION_ID \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "Amoxicilline 250mg",
    "dosage": "two times daily",
    "duration": "7 days"
  }'
```

### Example 3: Try to Edit Signed Prescription (fails)

```bash
# This will return 403 Forbidden
curl -X PUT http://localhost:8080/api/prescriptions/SIGNED_PRESCRIPTION_ID \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dosage": "new dosage"
  }'

# Response:
# {"detail": "Only draft prescriptions can be edited"}
```

---

## Related

- [Patients API](patients.md) - Get patient history
- [Authentication](authentication.md) - Login and tokens
- [System Design](../architecture/design.md) - Architecture overview
