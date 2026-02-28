# User Roles & Permissions

Vocalis supports two user roles with different capabilities: **Doctor** and **Nurse**.

## Role Overview

| Feature | Doctor | Nurse |
|---------|--------|-------|
| Create prescriptions | ✅ | ✅ |
| Edit draft prescriptions | ✅ | ✅ |
| Sign prescriptions | ✅ | ❌ |
| View organization prescriptions | ✅ | ✅ |
| Access validation results | ✅ | ✅ |
| Edit patient medical info | ✅ | ✅ |
| Quick sign (Signer button) | ✅ | ❌ |
| Full validation (Valider button) | ✅ | ❌ |
| Save prescription (Valider button) | ✅ | ✅ |

---

## Doctor Permissions

### What Doctors Can Do:

**Prescription Creation:**
- ✅ Create prescriptions from text input
- ✅ Create prescriptions from voice input
- ✅ Specify patient, medication, dosage, duration, diagnosis

**Prescription Editing:**
- ✅ Edit draft prescriptions (any field)
- ✅ Cannot edit signed prescriptions
- ✅ Can delete draft prescriptions

**Prescription Signing:**
- ✅ Sign prescriptions directly with **"Signer"** button (quick)
- ✅ Sign prescriptions with full validation using **"Valider"** button
- ✅ Both methods mark prescription as signed
- ✅ Signature timestamp is recorded

**Validation Results Screen:**
- ✅ See three buttons: "Retour", "Signer", "Valider"
- ✅ Review extracted data from AI
- ✅ Edit patient allergies, conditions, medications
- ✅ See validation warnings and errors

**Patient Management:**
- ✅ View all patients in organization
- ✅ Edit patient medical information
- ✅ Add/remove allergies and conditions
- ✅ Add/remove current medications

---

## Nurse Permissions

### What Nurses Can Do:

**Prescription Creation:**
- ✅ Create prescriptions from text input
- ✅ Create prescriptions from voice input
- ✅ Specify patient, medication, dosage, duration, diagnosis

**Prescription Editing:**
- ✅ Edit draft prescriptions (any field)
- ✅ Cannot edit signed prescriptions
- ✅ Can delete draft prescriptions

**Validation Results Screen:**
- ✅ See two buttons: "Retour", "Valider et enregistrer"
- ✅ Review extracted data from AI
- ✅ Edit patient allergies, conditions, medications
- ✅ Save and finalize prescription
- ❌ Cannot directly sign prescriptions

**Patient Management:**
- ✅ View all patients in organization
- ✅ Edit patient medical information
- ✅ Add/remove allergies and conditions
- ✅ Add/remove current medications

**Prescription Signing:**
- ❌ Cannot sign prescriptions (doctors only)
- ⚠️ Prescriptions created by nurses remain in **DRAFT** status
- ⚠️ Doctor must sign before prescription is final

---

## Validation Results Screen - Role-Based UI

### Doctor Interface

```
Buttons Available:
┌─────────────────────────────────────┐
│ [Retour au patient]                 │
│ [Signer]        [Valider]           │
│                                     │
│ Signer: Signer uniquement            │
│ Valider: Signer et enregistrer       │
└─────────────────────────────────────┘

Button Actions:
- Retour: Back to patient without signing
- Signer: Sign immediately and return
- Valider: Sign with full validation workflow
```

### Nurse Interface

```
Buttons Available:
┌─────────────────────────────────────┐
│ [Retour au patient]                 │
│ [Valider et enregistrer]             │
└─────────────────────────────────────┘

Button Actions:
- Retour: Back to patient without saving
- Valider et enregistrer: Save prescription (awaits doctor signature)
```

---

## Workflow Examples

### Doctor Workflow: Quick Sign

```
1. Doctor creates prescription (voice/text)
2. Reviews validation results
3. Clicks "Signer" button
   → Prescription signed immediately
   → Returns to patient record
   → Status: SIGNED (locked)
```

### Doctor Workflow: Full Validation

```
1. Doctor creates prescription (voice/text)
2. Reviews validation results
3. Reviews and edits patient medical info
4. Clicks "Valider" button
   → Prescription signed with full validation
   → Returns to patient record
   → Status: SIGNED (locked)
```

### Nurse Workflow: Create Prescription

```
1. Nurse creates prescription (voice/text)
2. Reviews validation results
3. Reviews and edits patient medical info
4. Clicks "Valider et enregistrer" button
   → Prescription saved
   → Returns to patient record
   → Status: DRAFT (awaits doctor signature)
```

### Doctor Workflow: Sign Nurse's Prescription

```
1. Doctor views patient detail page
2. Sees draft prescription created by nurse
3. Clicks "Signer" to finalize
   → Signs prescription
   → Status: SIGNED (locked)
```

---

## Permission Matrix

### By Feature

#### Create Prescription
| Role | Text | Voice | Voice (Web) |
|------|------|-------|------------|
| Doctor | ✅ | ✅ | ✅ |
| Nurse | ✅ | ✅ | ✅ |

#### Manage Prescription
| Role | View | Edit Draft | Delete Draft | Sign |
|------|------|-----------|--------------|------|
| Doctor | ✅ | ✅ | ✅ | ✅ |
| Nurse | ✅ | ✅ | ✅ | ❌ |

#### Manage Patient
| Role | View | Edit | Add Allergy | Remove Allergy |
|------|------|------|-------------|----------------|
| Doctor | ✅ | ✅ | ✅ | ✅ |
| Nurse | ✅ | ✅ | ✅ | ✅ |

---

## Organization Scoping

All data is scoped to the organization:
- ✅ Doctors see only their organization's patients and prescriptions
- ✅ Nurses see only their organization's patients and prescriptions
- ✅ Cannot access data from other organizations
- ✅ Cannot sign prescriptions from other organizations

---

## Common Scenarios

### Scenario 1: Doctor Creates and Signs
```
Doctor: Create prescription
Doctor: Review validation results
Doctor: Click "Signer" for quick sign
Result: Prescription signed immediately
```

### Scenario 2: Nurse Creates, Doctor Signs
```
Nurse: Create prescription
Nurse: Review validation results
Nurse: Click "Valider et enregistrer" to save
↓
Doctor: View patient record
Doctor: See draft prescription
Doctor: Click "Signer" to sign
Result: Prescription signed by doctor
```

### Scenario 3: Doctor Edits and Signs
```
Doctor: Create prescription
Doctor: Review validation results
Doctor: Click "Valider" for full validation
Doctor: See patient medical info
Doctor: Add allergy information
Doctor: Confirm to sign
Result: Prescription signed with updated patient info
```

---

## API-Level Permissions

### Authentication Required
All endpoints require JWT token with valid user role

### Doctor Endpoints
- POST /api/prescriptions (doctor only)
- PUT /api/prescriptions/{id}/sign (doctor only)
- PUT /api/prescriptions/{id} (edit draft)

### Nurse Endpoints
- POST /api/prescriptions (nurse allowed)
- Cannot access /api/prescriptions/{id}/sign
- PUT /api/prescriptions/{id} (edit draft)

### Shared Endpoints
- GET /api/patients (organization scoped)
- GET /api/prescriptions (organization scoped)
- PUT /api/patients/{id} (organization scoped)

---

## Best Practices by Role

### For Doctors:
- ✅ Use "Signer" for quick prescriptions you're confident in
- ✅ Use "Valider" when you need to review patient medical history
- ✅ Review nurse-created prescriptions before signing
- ✅ Document special instructions clearly
- ❌ Don't skip the validation review entirely

### For Nurses:
- ✅ Create prescriptions from voice input when possible
- ✅ Review and correct extracted data before validation
- ✅ Update patient medical information when new data is discovered
- ✅ Communicate with doctors about prescriptions awaiting signature
- ❌ Don't create invalid prescriptions (doctors will reject)
- ❌ Don't attempt to sign prescriptions (permission denied)

---

## Related Documentation

- [Prescription Lifecycle](./prescription-lifecycle.md) - Full prescription workflow
- [Authentication](../api/authentication.md) - Login and token management
- [API Reference](../api/prescriptions.md) - Complete API documentation
