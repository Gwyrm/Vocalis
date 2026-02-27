# Device Delivery Workflow Implementation

## Overview
Complete workflow for doctors to prescribe devices and nurses to deliver/install them at patient homes.

## Architecture

```
DOCTOR WORKFLOW:
  1. Create Prescription
  2. Assign Devices (quantity, instructions)
  3. Sign Prescription

SYSTEM:
  1. Create PatientVisit (assigns nurse)
  2. Link PrescriptionDevices to visit

NURSE WORKFLOW:
  1. View My Deliveries (list of visits with devices)
  2. Start Delivery (mark in_progress)
  3. Confirm Device Installation
     - Scan/enter device serial number
     - Record installation details
  4. Get Patient Signature
  5. Complete Delivery

DATABASE:
  - PrescriptionDevice: prescription -> devices
  - VisitDetail: tracks device_serial_installed
```

## Completed - Phase 1 & 2

### ✅ Database Models
- `PrescriptionDevice` table (links prescriptions to devices)
- Extended `Device` model (added description)
- Extended `VisitDetail` model (device_serial_installed, installation_confirmed, installation_timestamp)

### ✅ Backend API Endpoints
```
POST   /api/prescriptions/{id}/devices              - Assign device to prescription
GET    /api/prescriptions/{id}/devices              - Get devices for prescription
DELETE /api/prescriptions/{id}/devices/{device_id}  - Remove device from prescription
```

## To Implement - Phase 3: Frontend

### 1. Doctor UI - Device Assignment (Update PrescriptionForm)

**File**: `frontend/lib/screens/prescription_creation_screen.dart`

```dart
// Add device selection section in form:
- List of available devices from /api/devices
- For each device:
  * Device name + model
  * Quantity selector
  * Optional instructions text field
  * Add/Remove button
- Display selected devices with ability to edit quantities
```

### 2. Nurse Delivery Screen - List View

**File**: `frontend/lib/screens/nurse/nurse_deliveries_screen.dart`

**Features**:
- Shows list of assigned patient visits with "pending" or "in_progress" status
- For each delivery, display:
  * Patient name
  * Address
  * Scheduled date
  * Devices to deliver (count)
  * Current status badge
- Filter/sort by status, date, priority
- Action button: "Start Delivery" or "Resume Delivery"

**API Call**:
```
GET /api/patient-visits?role=nurse&status=pending,in_progress
```

### 3. Nurse Delivery Detail Screen

**File**: `frontend/lib/screens/nurse/delivery_detail_screen.dart`

**Sections**:

1. **Patient Information** (read-only)
   - Name, Age, Address, Phone
   - Contact info displayed prominently

2. **Devices Section**
   - List of devices to deliver (from /api/prescriptions/{id}/devices)
   - For each device:
     * Device name + model
     * Serial number (expected/template)
     * Quantity
     * Special instructions

3. **Device Installation Tracking**
   - For each device:
     * Checkbox: "Device present"
     * Text field: "Enter serial number" (validate it matches device)
     * Checkbox: "Installation complete"
     * Notes field for installation details
     * Optional: "Take photo" button

4. **Patient Verification**
   - Signature capture (existing feature)
   - Optional notes from nurse

5. **Actions**
   - "Mark In Progress" button (if pending)
   - "Complete Delivery" button
   - "Cancel" button

**API Calls**:
```
GET    /api/patient-visits/{id}
GET    /api/prescriptions/{id}/devices
PUT    /api/patient-visits/{id}/status (update to in_progress)
POST   /api/patient-visits/{id}/complete (with device_serial_installed in payload)
```

### 4. Navigation Updates

**File**: `frontend/lib/main.dart`

```dart
// Add role-based navigation:
if (authProvider.isAuthenticated) {
  final userRole = authProvider.currentUser?.role;

  if (userRole == 'doctor') {
    return DoctorDashboard();  // Existing
  } else if (userRole == 'nurse') {
    return NurseDeliveriesScreen();  // NEW
  } else if (userRole == 'admin') {
    return AdminDashboard();
  }
}
```

### 5. Update API Models (Frontend)

**File**: `frontend/lib/models/prescription.dart`

Add:
```dart
class PrescriptionDevice {
  String id;
  String device_id;
  String device_name;
  String? model;
  int quantity;
  String? instructions;
  String priority;
}

class Prescription {
  // ... existing fields ...
  List<PrescriptionDevice> devices; // NEW
}
```

### 6. Update ApiService

**File**: `frontend/lib/api_service.dart`

Add methods:
```dart
Future<List<PrescriptionDevice>> getPrescriptionDevices(String prescriptionId) async
Future<void> assignDeviceToPrescription(String prescriptionId, ...) async
Future<void> removeDeviceFromPrescription(String prescriptionId, String deviceId) async
Future<PatientVisit> getVisitDetails(String visitId) async
Future<void> completeDeviceDelivery(String visitId, String deviceSerial, String notes) async
```

## Example Workflow

### Doctor Creates Prescription with Devices

```
1. Fill prescription form:
   - Patient: Jean Dupont
   - Medication: Metoprolol
   - Dosage: 100mg

2. Add devices:
   - Device 1: Oxygen Monitor (serial: OM-12345)
     * Quantity: 1
     * Instructions: "Use with calibration strip daily"
   - Device 2: Blood Pressure Cuff (serial: BP-67890)
     * Quantity: 1
     * Instructions: "Measure morning and evening"

3. Sign prescription

System creates PatientVisit for nurse with these devices
```

### Nurse Delivers & Installs Devices

```
1. See "Jean Dupont - 15 Rue de la Paix" in delivery list
2. Click to open delivery details
3. For Oxygen Monitor:
   - Confirm device present (checkbox)
   - Enter actual serial: OM-12345 (auto-validated)
   - Confirm installation (checkbox)
   - Notes: "Device tested, calibration done"
4. For Blood Pressure Cuff:
   - Confirm device present (checkbox)
   - Enter actual serial: BP-67890 (auto-validated)
   - Confirm installation (checkbox)
   - Notes: "Patient shown how to use"
5. Get signature from Jean Dupont
6. Click "Complete Delivery"

System marks devices as "delivered" and visit as "completed"
```

## Testing Plan

### Backend Testing
```bash
# Create prescription
POST /api/prescriptions {patient_id, medication, dosage, duration}

# Assign device
POST /api/prescriptions/{id}/devices {device_id, quantity, instructions}

# Get devices
GET /api/prescriptions/{id}/devices

# Nurse gets deliveries
GET /api/patient-visits?role=nurse

# Complete delivery
POST /api/patient-visits/{id}/complete {device_serial_installed, nurse_notes, patient_signature}
```

### Frontend Testing
1. Login as doctor → Create prescription → Assign devices → Sign
2. Logout, login as nurse → See delivery list → Open delivery → Confirm devices → Get signature → Complete
3. Verify device status changed to "delivered"

## Success Criteria

✅ Doctors can assign multiple devices to prescriptions
✅ Nurses see list of deliveries with device details
✅ Nurses can confirm device installation with serial numbers
✅ System tracks which devices were actually installed
✅ Patients sign off on device delivery
✅ Visit marked complete after all devices installed

## Future Enhancements

- QR code scanning for device serial numbers
- Photo documentation of installation
- Device maintenance scheduling
- Return/pickup workflow for devices
- Multi-language device instructions
- Integration with IoT device activation

