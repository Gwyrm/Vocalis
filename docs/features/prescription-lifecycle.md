# Prescription Lifecycle & Editing

Learn how prescriptions are created, edited, and finalized in Vocalis.

## Overview

Prescriptions follow a clear workflow from creation to completion:

```
Create → Review → Edit (Draft) → Sign → Locked
```

## 1. Creation Phase

Prescriptions can be created in two ways:

### Text Input
- Doctor/Nurse enters prescription in natural language
- Example: "Amoxicilline 500mg, three times daily for 10 days"
- LLM extracts structured data
- Validation identifies any issues

### Voice Input
- Doctor/Nurse records audio prescription
- Whisper transcribes audio to text
- LLM extracts medication, dosage, duration
- Same validation as text input

**Initial Status:** `draft`

## 2. Review Phase

After creation, user sees the validation results screen:

- **Extracted Data:** Medication, dosage, duration, diagnosis
- **Patient Info:** Current allergies, conditions, medications
- **Warnings:** Potential drug interactions, missing data
- **Errors:** Invalid data that must be fixed

User can:
- Review the extracted information
- Edit patient medical information (add/remove allergies, etc.)
- See success/error messages

## 3. Edit Phase (Draft Only)

Before signing, prescription is in `draft` status and **fully editable**.

### Available Actions:
- Click **"Éditer"** button on draft prescription
- Modify any field:
  - Medication name
  - Dosage instructions
  - Treatment duration
  - Diagnosis
  - Special instructions
- Click **"Enregistrer"** to save changes
- Returns to patient page with updated prescription

### Key Points:
- ✅ Draft prescriptions are **completely editable**
- ✅ Multiple edits allowed
- ✅ Changes save to database immediately
- ✅ Patient medical info can be updated simultaneously

### When You CAN Edit:
- Prescription status is **"draft"**
- You are the prescription creator (doctor/nurse who created it)
- Prescription hasn't been signed yet

### When You CANNOT Edit:
- Prescription is **"signed"** by doctor
- Prescription is **"completed"** (dispensed)
- You don't have permission (different organization)

## 4. Signing Phase

Once prescription is ready, the signing process depends on the user's role.

### Doctor: Two Signing Options

On the validation results screen, doctors see **three buttons** with two signing methods:

**Option 1: Direct Sign (Quick)**
- Click **"Signer"** button
- Signs prescription immediately
- Returns to patient record
- Use when you're confident in the prescription

**Option 2: Sign + Validate (Safe)**
- Click **"Valider"** button
- Signs and saves the prescription
- Shows full validation workflow
- Use when you want to review everything one more time

### Nurse: Single Signing Option

Nurses see **two buttons** on the validation results screen:

- Click **"Valider et enregistrer"** button
- Creates and saves the prescription
- Returns to patient record
- **Note:** Nurses cannot sign prescriptions - only doctors can

### Sign Process (Doctor):
1. Review extracted data and patient info on validation screen
2. Choose your signing method:
   - **"Signer"** for direct sign (returns immediately)
   - **"Valider"** for sign + validation (shows complete workflow)
3. Backend marks prescription as signed
4. Success message shown
5. Status changes to **"signed"**

### What Happens After Signing:
- ✅ Prescription is **locked** (read-only)
- ❌ **Edit button disappears**
- ❌ Cannot be modified
- ✅ Doctor signature timestamp is recorded
- ✅ Marked as "✓ Signée" in patient history

## 5. Completion Phase

Prescription dispensed to patient:
- Status: `completed`
- Prescription fully archived
- Historical record maintained

---

## UI & User Experience

### Validation Results Screen - Doctor

```
┌────────────────────────────────┐
│ Ordonnance valide ✓            │
├────────────────────────────────┤
│ Médicament: Amoxicilline       │
│ Posologie: 500mg, 3x daily     │
│ Durée: 10 jours                │
│ Diagnostic: Bronchite          │
├────────────────────────────────┤
│ Patient Info (editable)        │
│ • Allergies: Pénicilline       │
│ • Conditions: Asthme           │
├────────────────────────────────┤
│ [Retour] [Signer] [Valider]    │ ← Doctor buttons
│                                │
│ Signer: Signer uniquement       │
│ Valider: Signer et enregistrer  │
└────────────────────────────────┘
```

### Validation Results Screen - Nurse

```
┌────────────────────────────────┐
│ Ordonnance valide ✓            │
├────────────────────────────────┤
│ Médicament: Amoxicilline       │
│ Posologie: 500mg, 3x daily     │
│ Durée: 10 jours                │
│ Diagnostic: Bronchite          │
├────────────────────────────────┤
│ Patient Info (editable)        │
│ • Allergies: Pénicilline       │
│ • Conditions: Asthme           │
├────────────────────────────────┤
│ [Retour] [Valider et          │
│          enregistrer]           │ ← Nurse buttons
└────────────────────────────────┘
```

### Draft Prescription View (Patient Record)
```
┌─────────────────────────┐
│ Amoxicilline 500mg      │
│ Dosage: 3x daily        │
│ Duration: 10 days       │
│                         │
│ Status: ⏳ À signer     │
│                         │
│ [Éditer] [Signer]       │ ← Both buttons visible
└─────────────────────────┘
```

### Signed Prescription View (Patient Record)
```
┌─────────────────────────┐
│ Amoxicilline 500mg      │
│ Dosage: 3x daily        │
│ Duration: 10 days       │
│                         │
│ Status: ✓ Signée        │
│ Signed: 28/02/2026      │
│                         │
│ (No edit button)        │ ← Read-only
└─────────────────────────┘
```

---

## Status Badges

### Draft Status
- **Badge Color:** Orange
- **Text:** "⏳ À signer" (To sign)
- **Meaning:** Prescription can still be edited
- **Actions:** Edit, Sign, Delete

### Signed Status
- **Badge Color:** Green
- **Text:** "✓ Signée" (Signed)
- **Meaning:** Prescription locked and read-only
- **Actions:** View only
- **Shows:** Signature timestamp

---

## Example Workflows

### Workflow 1: Create, Edit, Sign

```
1. Doctor clicks "Créer une ordonnance"
   ↓
2. Enters text: "Amoxicilline 500mg 3x daily for 10 days"
   ↓
3. System validates and shows results
   ↓
4. Doctor clicks "Valider et enregistrer"
   → Prescription created with status: DRAFT
   ↓
5. Doctor sees draft prescription with "Éditer" button
   ↓
6. Clicks "Éditer" to change dosage to "250mg 2x daily"
   ↓
7. Clicks "Enregistrer"
   → Prescription updated in database
   ↓
8. Doctor clicks "Signer" to finalize
   ↓
9. Confirms on validation screen
   ↓
10. Prescription signed → Status: SIGNED
    → Edit button disappears
    → Prescription locked
```

### Workflow 2: Doctor Quick Sign (New!)

```
1. Doctor creates prescription from text/voice
   ↓
2. Enters prescription details
   ↓
3. Reviews extracted data on validation screen
   ↓
4. Clicks "Signer" button
   → Prescription signed immediately
   → Returns to patient record
   → Status: SIGNED
   → Read-only
```

### Workflow 3: Doctor Sign + Validate (New!)

```
1. Doctor creates prescription from text/voice
   ↓
2. Enters prescription details
   ↓
3. Reviews extracted data on validation screen
   ↓
4. Edits patient medical info (add allergies, etc.)
   ↓
5. Clicks "Valider" button
   → Prescription signed and saved
   → Full validation workflow shown
   → Returns to patient record
   → Status: SIGNED
   → Read-only
```

### Workflow 4: Nurse Create Prescription

```
1. Nurse creates prescription from text/voice
   ↓
2. Enters prescription details
   ↓
3. Reviews extracted data on validation screen
   ↓
4. Edits patient medical info if needed
   ↓
5. Clicks "Valider et enregistrer" button
   → Prescription created and saved
   → Returns to patient record
   → Status: DRAFT (waiting for doctor signature)
   → Can be edited
   → Marked as created by nurse
```

### Workflow 5: Attempt to Edit Signed Prescription

```
1. Doctor tries to edit a SIGNED prescription
   ↓
2. API returns: 403 Forbidden
   Message: "Only draft prescriptions can be edited"
   ↓
3. User sees error message
   → Cannot proceed
   → Must create new prescription if changes needed
```

---

## Best Practices

### ✅ Do:
- Review extracted data carefully before signing
- Use the edit feature to correct mistakes in drafts
- Sign prescriptions only when all data is correct
- Document special instructions for patient safety
- **Doctors:** Use "Signer" for quick sign when confident
- **Doctors:** Use "Valider" for full review when uncertain
- **Nurses:** Review and edit patient info before validation

### ❌ Don't:
- Sign prescriptions with incomplete information
- Attempt to edit signed prescriptions (not allowed)
- Skip the validation review step
- Create multiple prescriptions for same patient without reason
- **Nurses:** Attempt to use the "Signer" button (doctors only)

---

## Permissions

### Doctor Can:
- Create prescriptions (text, voice)
- Edit draft prescriptions
- Sign prescriptions
- View all organization prescriptions

### Nurse Can:
- Create prescriptions (text, voice)
- Edit draft prescriptions
- View organization prescriptions
- **Cannot sign** prescriptions

---

## Technical Details

### Draft Prescription Endpoint
```
PUT /api/prescriptions/{id}

Only allowed if status == "draft"
Returns 403 if status == "signed"
```

### Editing Fields
All fields are optional:
- `medication` - Medication name
- `dosage` - Dosage instructions
- `duration` - Treatment duration
- `diagnosis` - Clinical diagnosis
- `special_instructions` - Special notes for patient

### Validation
- Input is sanitized to prevent injection
- Maximum 200 chars for medication/dosage/duration
- Maximum 500 chars for diagnosis/instructions
- Errors prevent saving and show user feedback

---

## Common Questions

**Q: What's the difference between "Signer" and "Valider" buttons?**
A:
- **"Signer"** - Quick sign only. Signs prescription immediately and returns to patient record. Use when you're confident.
- **"Valider"** - Signs and validates. Shows full workflow with patient info review. Use for safety.

**Q: When should I use "Signer" vs "Valider"?**
A:
- Use **"Signer"** when prescription details are correct and you just need to finalize
- Use **"Valider"** when you want to review patient allergies/conditions before signing
- Both buttons result in a signed prescription - it's about your workflow preference

**Q: Can I edit a prescription after signing?**
A: No. Once signed, prescriptions are locked and read-only. Create a new prescription if changes are needed.

**Q: How many times can I edit a draft?**
A: Unlimited. Draft prescriptions can be edited as many times as needed before signing.

**Q: What happens if I sign by mistake?**
A: Currently, there's no "unsign" feature. Create a new prescription instead.

**Q: Can a nurse sign prescriptions?**
A: No. Only doctors can sign. Nurses can create, edit drafts, and validate prescriptions. The doctor must sign.

**Q: Are edit changes saved immediately?**
A: Yes. Changes save to database when you click "Enregistrer".

**Q: Why can't I see the "Signer" button?**
A: The "Signer" button only appears for doctors. If you're logged in as a nurse, you'll only see "Valider et enregistrer". Only doctors can directly sign prescriptions.

---

## Related Documentation

- [Prescriptions API](../api/prescriptions.md) - Complete API reference
- [Authentication](../api/authentication.md) - User roles and permissions
- [System Design](../architecture/design.md) - Architecture overview
- [Troubleshooting](../troubleshooting.md) - Common issues
