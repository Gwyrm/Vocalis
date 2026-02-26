# Doctor Signature Requirement for Prescription Validity

## Overview

**Legal Requirement**: Prescriptions MUST be digitally signed by a doctor to be legally valid. This document outlines the complete signature workflow, implementation, and requirements.

---

## Why Doctor Signatures Matter

✅ **Legal Compliance**: Medical prescriptions require doctor authorization
✅ **Accountability**: Clear audit trail of who prescribed what
✅ **Authentication**: Proves the doctor approved the prescription
✅ **Tamper-Proof**: Signature validates authenticity
✅ **Medical Record**: Part of legal medical documentation

---

## Prescription Lifecycle

### Stage 1: Draft (Not Valid)
```
Doctor creates prescription
↓
Status: 'draft'
is_signed: false
doctor_signed_at: null
❌ NOT LEGALLY VALID - Cannot be used
```

### Stage 2: Review
```
Doctor reviews prescription details:
- Patient info correct?
- Medication and dosage valid?
- Duration appropriate?
- Special instructions clear?
```

### Stage 3: Sign (Becomes Valid)
```
Doctor applies digital signature
↓
Status: 'signed'
is_signed: true
doctor_signed_at: <timestamp>
doctor_signature: <base64 PNG image>
✅ LEGALLY VALID - Can be used
```

### Stage 4: Use/Complete
```
Prescription sent to patient
Nurse delivers medication
Prescription marked as completed
```

---

## API Workflow

### Step 1: Create Prescription
```bash
POST /api/prescriptions
Authorization: Bearer <doctor_token>

Request:
{
  "patient_id": "patient-123",
  "diagnosis": "Bacterial infection",
  "medication": "amoxicilline",
  "dosage": "500mg",
  "duration": "7 jours",
  "special_instructions": "trois fois par jour avec les repas"
}

Response:
{
  "id": "rx-001",
  "patient_name": "Jean Dupont",
  "medication": "amoxicilline",
  "dosage": "500mg",
  "duration": "7 jours",
  "status": "draft",      ← NOT SIGNED YET
  "is_signed": false,
  "doctor_signed_at": null,
  "created_at": "2026-02-26T10:00:00Z"
}
```

### Step 2: Sign Prescription
```bash
PUT /api/prescriptions/{prescription_id}/sign
Authorization: Bearer <doctor_token>

Request:
{
  "doctor_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEA..."
}

Response:
{
  "id": "rx-001",
  "patient_name": "Jean Dupont",
  "medication": "amoxicilline",
  "dosage": "500mg",
  "duration": "7 jours",
  "status": "signed",     ← NOW SIGNED
  "is_signed": true,
  "doctor_signed_at": "2026-02-26T10:05:30Z",
  "created_at": "2026-02-26T10:00:00Z"
}
```

### Step 3: Use Prescription
```bash
GET /api/prescriptions/{prescription_id}
Authorization: Bearer <token>

Response:
{
  "id": "rx-001",
  "status": "signed",
  "is_signed": true,      ← VALID - Can proceed
  "doctor_signed_at": "2026-02-26T10:05:30Z",
  ...
}
```

---

## Signature Format

### Signature Image Requirements
```
Format:       PNG (Portable Network Graphics)
Max Size:     1 MB
Encoding:     Base64 (for transport)
Example:      "data:image/png;base64,iVBORw0KGgo..."

PNG Magic Bytes: 89 50 4E 47 0D 0A 1A 0A
Validation:   Server validates format and size
```

### Example: Base64 Encoded Signature
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA
AAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXD
MEzK/3r+//8zzDCdJyoFAKzG1jTkNbWqAAAAAElFTkSu
QmCC
```

### Signature Data Structure
```json
{
  "doctor_signature": "data:image/png;base64,<encoded image>",
  "password_confirmation": "optional"
}
```

---

## Validation Rules

### Signature Image Validation
```
✓ Must be PNG format (checked via magic bytes)
✓ Must not exceed 1 MB
✓ Must be valid base64 encoded
✓ Must not be null/empty
✗ JPEG, BMP, or other formats rejected
✗ Oversized images rejected (>1MB)
✗ Invalid base64 rejected
```

### Signing Authorization
```
✓ Only the doctor who created the prescription can sign it
✓ Admin users can sign any prescription
✗ Other doctors cannot sign each other's prescriptions
✗ Nurses cannot sign prescriptions
```

### Status Validation
```
✓ Draft prescriptions can be signed
✗ Already signed prescriptions cannot be re-signed
✗ Completed/archived prescriptions cannot be signed
```

---

## Prescription Status Transitions

```
┌─────────────────────────────────────┐
│ Draft                               │
│ (Not signed, cannot be used)        │
│ is_signed: false                    │
└────────────┬────────────────────────┘
             │
             │ Doctor signs prescription
             │ PUT /prescriptions/{id}/sign
             ↓
┌─────────────────────────────────────┐
│ Signed                              │
│ (Legally valid, can be used)        │
│ is_signed: true                     │
│ doctor_signed_at: <timestamp>       │
└────────────┬────────────────────────┘
             │
             │ Prescription delivered to patient
             │ Treatment completed
             ↓
┌─────────────────────────────────────┐
│ Completed                           │
│ (Usage complete, archived)          │
│ is_signed: true                     │
└─────────────────────────────────────┘
```

---

## Error Scenarios

### Error 1: Trying to Use Unsigned Prescription
```bash
GET /api/prescriptions/{prescription_id}

Response (draft prescription):
{
  "id": "rx-001",
  "status": "draft",
  "is_signed": false,     ← INVALID
  "error": "Prescription must be signed before use"
}
```

### Error 2: Invalid Signature Image
```bash
PUT /api/prescriptions/{prescription_id}/sign

Request (JPEG image):
{
  "doctor_signature": "data:image/jpeg;base64,..."
}

Response:
{
  "statusCode": 422,
  "detail": "Invalid signature image. Must be a valid PNG file, max 1MB"
}
```

### Error 3: Re-signing Already Signed Prescription
```bash
PUT /api/prescriptions/{prescription_id}/sign

Response (already signed):
{
  "statusCode": 400,
  "detail": "Prescription is already signed"
}
```

### Error 4: Wrong Doctor Trying to Sign
```bash
PUT /api/prescriptions/{prescription_id}/sign
Authorization: Bearer <different_doctor_token>

Response:
{
  "statusCode": 403,
  "detail": "Only the doctor who created this prescription can sign it"
}
```

---

## Frontend Implementation

### 1. Signature Capture Component

```dart
// On prescription review screen
import 'package:signature/signature.dart';

class PrescriptionSignatureScreen extends StatefulWidget {
  final String prescriptionId;
  final Prescription prescription;

  @override
  State<PrescriptionSignatureScreen> createState() =>
      _PrescriptionSignatureScreenState();
}

class _PrescriptionSignatureScreenState
    extends State<PrescriptionSignatureScreen> {

  late SignatureController _signatureController;

  @override
  void initState() {
    super.initState();
    _signatureController = SignatureController();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Sign Prescription')),
      body: Column(
        children: [
          // Prescription Review
          PrescriptionReviewCard(prescription: widget.prescription),

          // Signature Area
          Expanded(
            child: Signature(
              controller: _signatureController,
              backgroundColor: Colors.grey.shade100,
            ),
          ),

          // Action Buttons
          Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                ElevatedButton(
                  onPressed: () => _signatureController.clear(),
                  child: Text('Clear'),
                ),
                SizedBox(width: 16),
                ElevatedButton.icon(
                  onPressed: _handleSignPrescription,
                  icon: Icon(Icons.check),
                  label: Text('Sign Prescription'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _handleSignPrescription() async {
    final signatureBytes =
        await _signatureController.toPng();

    if (signatureBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please provide a signature')),
      );
      return;
    }

    // Convert to base64
    final base64Signature =
        'data:image/png;base64,' +
        base64Encode(signatureBytes);

    // Sign prescription via API
    final apiService = context.read<ApiService>();
    try {
      await apiService.signPrescription(
        widget.prescriptionId,
        base64Signature,
      );

      if (mounted) {
        Navigator.pop(context, true); // Return success
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }
}
```

### 2. Prescription Review Screen
```dart
class PrescriptionReviewCard extends StatelessWidget {
  final Prescription prescription;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Review Prescription',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            SizedBox(height: 16),

            // Patient Info
            _ReviewRow('Patient', prescription.patientName),
            _ReviewRow('Age', prescription.patientAge),
            _ReviewRow('Diagnosis', prescription.diagnosis),

            SizedBox(height: 16),
            Divider(),
            SizedBox(height: 16),

            // Medication Info
            _ReviewRow('Medication', prescription.medication),
            _ReviewRow('Dosage', prescription.dosage),
            _ReviewRow('Duration', prescription.duration),
            if (prescription.specialInstructions != null)
              _ReviewRow('Instructions',
                  prescription.specialInstructions!),

            SizedBox(height: 16),

            // Status
            Chip(
              label: Text('Status: ${prescription.status}'),
              backgroundColor: prescription.isSigned
                  ? Colors.green
                  : Colors.orange,
            ),
          ],
        ),
      ),
    );
  }

  Widget _ReviewRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
```

### 3. API Service Method
```dart
// In api_service.dart
Future<PrescriptionResponse> signPrescription(
  String prescriptionId,
  String signatureBase64,
) async {
  final url = Uri.parse(
      '$baseUrl/api/prescriptions/$prescriptionId/sign');

  try {
    final response = await http.put(
      url,
      headers: _authHeaders,
      body: jsonEncode({
        'doctor_signature': signatureBase64,
      }),
    );

    if (response.statusCode == 200) {
      return PrescriptionResponse.fromJson(
          jsonDecode(response.body));
    } else if (response.statusCode == 400) {
      throw Exception('Prescription already signed');
    } else if (response.statusCode == 403) {
      throw Exception('Only the prescribing doctor can sign');
    } else {
      throw Exception(_getErrorMessage(response));
    }
  } catch (e) {
    throw Exception('Error signing prescription: $e');
  }
}
```

---

## Audit Trail & Compliance

### Signature Record
```json
{
  "prescription_id": "rx-001",
  "doctor_id": "doc-123",
  "doctor_email": "dr.dupont@clinic.fr",
  "signed_at": "2026-02-26T10:05:30Z",
  "signature_image": "base64 encoded PNG",
  "patient_id": "pat-456",
  "patient_name": "Jean Dupont",
  "medication": "amoxicilline",
  "dosage": "500mg"
}
```

### Audit Log Example
```
2026-02-26 10:00:00 | Prescription created (rx-001) by Dr. Dupont
2026-02-26 10:02:15 | Prescription reviewed - medication verified
2026-02-26 10:05:30 | Prescription signed by Dr. Dupont
2026-02-26 10:06:00 | Prescription marked for delivery
2026-02-26 14:30:00 | Prescription delivered to patient
2026-02-26 14:35:00 | Prescription marked as completed
```

---

## Security Considerations

✅ **Authentication**
- Only authenticated doctors can sign
- Token-based authorization verified

✅ **Authorization**
- Only original doctor can sign their prescriptions
- Admin can sign any prescription

✅ **Validation**
- Signature image format validated (PNG only)
- File size validated (max 1MB)
- Base64 encoding validated

✅ **Audit Trail**
- Timestamp recorded with UTC timezone
- Doctor ID linked to signature
- Signature stored with prescription

✅ **Immutability**
- Cannot re-sign already signed prescriptions
- Cannot modify prescription after signing (future: use timestamps)

---

## Legal Compliance Checklist

- ✅ Signatures required for validity
- ✅ Doctor authentication enforced
- ✅ Digital signature stored
- ✅ Timestamp recorded
- ✅ Audit trail maintained
- ✅ Access control enforced
- ✅ Image validation performed
- ✅ Cannot be unsigned or re-signed

---

## Summary

**Prescriptions MUST be signed by a doctor to be legally valid:**

1. **Create** prescription (Status: draft)
2. **Review** prescription details
3. **Sign** with digital signature (Status: signed)
4. **Use** legally valid prescription

```
Draft → Review → Sign → Valid ✓
```

---

## API Reference

### Create Prescription
```
POST /api/prescriptions
Response: status='draft', is_signed=false
```

### Sign Prescription
```
PUT /api/prescriptions/{id}/sign
Request: {doctor_signature: "data:image/png;base64,..."}
Response: status='signed', is_signed=true, doctor_signed_at=<timestamp>
```

### Get Prescription
```
GET /api/prescriptions/{id}
Shows: is_signed, doctor_signed_at, status
```

---

**Status**: ✅ **IMPLEMENTED**
- Backend: Signature fields, signing endpoint, validation
- Database: doctor_signature, doctor_signed_at, is_signed fields
- Audit: Timestamp and doctor tracking
- Frontend: Ready for signature capture UI
