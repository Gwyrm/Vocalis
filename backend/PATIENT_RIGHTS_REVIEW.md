# Patient Management System - Rights & Access Control Review

**Date:** March 1, 2026
**Status:** ⚠️ CRITICAL FINDINGS - Access Control Gaps Identified

---

## Executive Summary

The patient management system has **minimal role-based access control (RBAC)**, creating security and compliance risks:

- ✅ **Organization scoping works well** - Patients properly isolated per org
- ❌ **No role enforcement** - Nurses can perform doctor-only operations
- ❌ **No creator tracking** - Can't determine who created/modified patient records
- ⚠️ **Incomplete audit trail** - Missing access logs for HIPAA compliance

---

## Current Implementation Analysis

### 1. Patient CRUD Endpoints

#### POST /api/patients (Create)
```python
async def create_patient(
    request: PatientCreate,
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
    db: Session = Depends(get_db_for_request)
)
```

**Current Behavior:**
- Any user (doctor/nurse) can create patients
- No role check
- Stores org_id but not creator_id

**Issues:**
- ❌ Nurses shouldn't typically create patient records (data integrity issue)
- ❌ No audit trail of who created the patient
- ⚠️ HIPAA requires access tracking

#### GET /api/patients (List All)
```python
async def list_patients(
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
    db: Session = Depends(get_db_for_request)
)
```

**Current Behavior:**
- Any user in org can view all patients
- Returns full patient details (allergies, conditions, medications, notes)

**Issues:**
- ⚠️ Nurses may access more patient data than needed (principle of least privilege)
- ❌ No granular access control

#### GET /api/patients/{patient_id} (Read)
```python
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
)
```

**Current Behavior:**
- Any user can view any patient details
- Full medical history visible

**Issues:**
- ⚠️ Violates least privilege principle
- ❌ Nurses only need patient info for assigned visits

#### PUT /api/patients/{patient_id} (Update)
```python
async def update_patient(
    patient_id: str,
    request: PatientUpdate,
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
)
```

**Current Behavior:**
- Any user can modify any patient record
- Updates allergies, conditions, medications, notes
- Tracks updated_at but not updated_by

**Issues:**
- ❌ Critical security issue - nurses can modify medical records
- ❌ No audit trail of who made changes
- ❌ No change history
- ⚠️ HIPAA violation risk

#### DELETE /api/patients/{patient_id} (Delete)
```python
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
)
```

**Current Behavior:**
- Any user can hard-delete patient records
- Data permanently removed

**Issues:**
- ❌ CRITICAL - No audit trail after deletion
- ❌ Violates HIPAA retention requirements
- ❌ Only doctors should be able to delete
- ⚠️ No soft-delete for audit trail

### 2. Patient-Prescription Relationship

#### GET /api/patients/{patient_id}/prescriptions
```python
async def get_patient_prescriptions(
    patient_id: str,
    current_user: User = Depends(get_current_user),  # ⚠️ Any authenticated user
)
```

**Current Behavior:**
- Any user can view all prescriptions for a patient

**Issues:**
- ⚠️ Nurses don't need all prescriptions, only assigned visits
- ❌ No filtering by nurse's role

---

## Role-Based Access Matrix (Current vs Recommended)

| Operation | Current | Should Be | Risk |
|-----------|---------|-----------|------|
| Create Patient | Any | Doctor only | ❌ HIGH |
| Read Patient | Any | Any (in org) | ⚠️ MEDIUM |
| Update Patient | Any | Doctor only | ❌ CRITICAL |
| Delete Patient | Any | Doctor only | ❌ CRITICAL |
| View Prescriptions | Any | Any (in org) | ⚠️ MEDIUM |

### Recommended Access Model

```
DOCTOR Role:
  ✓ Create patient records
  ✓ Read/update patient records
  ✓ Delete patient records (audit logged)
  ✓ View all prescriptions for patients
  ✓ Assign visits to nurses

NURSE Role:
  ✓ Read patient details (limited to assigned visits)
  ✓ Update visit notes/signature (not patient record)
  ✗ Create patient records
  ✗ Modify patient medical history
  ✗ Delete anything
  ✓ View prescriptions for assigned visits only

ADMIN Role:
  ✓ All operations
  ✓ View audit logs
  ✓ Manage access control
```

---

## Missing Audit Features

### 1. No Creator Tracking
```python
class Patient(Base):
    # Missing fields:
    created_by: str  # Who created the patient
    updated_by: str  # Who last modified
```

### 2. No Change History
```python
class PatientChangeLog(Base):
    patient_id: str
    changed_by: str
    field_name: str  # allergies, conditions, etc.
    old_value: str
    new_value: str
    changed_at: datetime
```

### 3. No Access Logs
```python
class AccessLog(Base):
    user_id: str
    patient_id: str
    action: str  # read, create, update, delete
    timestamp: datetime
```

---

## Security Issues Identified

### Issue #1: Unauthorized Data Modification ❌ CRITICAL
**Severity:** Critical
**HIPAA Risk:** Yes
**Exploitability:** Trivial (any nurse can modify)

```bash
# A nurse can do this (shouldn't be allowed):
curl -X PUT http://localhost:8080/api/patients/patient-123 \
  -H "Authorization: Bearer <nurse_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "allergies": ["added-by-nurse"],
    "medical_notes": "changed-notes"
  }'
```

**Impact:**
- Data integrity compromised
- Medical record falsification possible
- Compliance violations

---

### Issue #2: Permanent Data Deletion ❌ CRITICAL
**Severity:** Critical
**HIPAA Risk:** Yes
**Exploitability:** Trivial

```bash
# Any user can permanently delete:
curl -X DELETE http://localhost:8080/api/patients/patient-123 \
  -H "Authorization: Bearer <user_token>"
```

**Impact:**
- No audit trail after deletion
- Violates HIPAA retention requirements
- Evidence destruction

---

### Issue #3: Information Disclosure ⚠️ MEDIUM
**Severity:** Medium
**HIPAA Risk:** Yes (access without need)
**Exploitability:** Trivial

Nurses can view all patient records in organization, even if not assigned to that patient's care.

---

### Issue #4: Missing Change Tracking ⚠️ MEDIUM
**Severity:** Medium
**HIPAA Risk:** Yes
**Exploitability:** N/A (already built-in gap)

Cannot determine:
- Who modified a patient record
- When modifications were made
- What changed
- Why it changed

---

## Compliance Issues

### HIPAA Violations
1. **Access Control (164.312(a)(2)(i))**
   - ❌ No role-based access control
   - ❌ Users have access to patient data beyond what's needed

2. **Audit Controls (164.312(b))**
   - ❌ No access logs
   - ❌ No modification audit trail
   - ❌ No deletion records

3. **Integrity (164.312(c)(2))**
   - ❌ No mechanism to verify accuracy of patient data
   - ❌ Anyone can modify without approval

4. **Documentation (164.308(a)(7)(ii)(B))**
   - ❌ Cannot document who accessed what when

### GDPR Violations (if applicable)
1. **Purpose Limitation**
   - Data accessed beyond stated purpose
2. **Data Minimization**
   - Nurses get full records vs limited needed data
3. **Accountability**
   - No logs of data access/modification

---

## Recommendations

### Phase 1: Immediate (Before Production) 🔴
**Priority:** CRITICAL - Must implement before any HIPAA-covered use

1. **Add Role Enforcement**
   ```python
   @app.post("/api/patients", response_model=PatientResponse)
   async def create_patient(
       request: PatientCreate,
       current_user: User = Depends(get_doctor),  # CHANGED: Doctor only
       db: Session = Depends(get_db_for_request)
   ):
   ```

2. **Add Creator Tracking to Patient Model**
   ```python
   class Patient(Base):
       # ... existing fields ...
       created_by = Column(String(36), ForeignKey("users.id"))
       updated_by = Column(String(36), ForeignKey("users.id"))
       created_by_user = relationship("User", foreign_keys=[created_by])
       updated_by_user = relationship("User", foreign_keys=[updated_by])
   ```

3. **Implement Soft Deletes**
   ```python
   class Patient(Base):
       # ... existing fields ...
       deleted_at = Column(DateTime, nullable=True)
       deleted_by = Column(String(36), ForeignKey("users.id"))

   # In queries: filter(Patient.deleted_at == None)
   ```

4. **Create Access Log Table**
   ```python
   class PatientAccessLog(Base):
       __tablename__ = "patient_access_logs"
       id = Column(String(36), primary_key=True)
       user_id = Column(String(36), ForeignKey("users.id"))
       patient_id = Column(String(36), ForeignKey("patients.id"))
       action = Column(String(50))  # read, create, update, delete
       accessed_at = Column(DateTime, default=datetime.utcnow)
   ```

### Phase 2: Short-term (Within 2 weeks)
1. **Implement Change History**
   - Track field-level changes
   - Store old/new values
   - Enable audit trail queries

2. **Add Access Logging Middleware**
   - Log all patient access
   - Include IP address, timestamp, user
   - Implement retention policy

3. **Patient-Nurse Assignment**
   - Link nurses to specific patients
   - Filter access based on assignment
   - Track care team membership

### Phase 3: Medium-term (Within 1 month)
1. **Audit Dashboard**
   - View access logs
   - Detect suspicious access patterns
   - Export compliance reports

2. **Data Retention Policy**
   - Define retention periods
   - Implement automated cleanup
   - Archive old records

3. **Encryption at Rest**
   - Encrypt sensitive patient fields
   - Key management system
   - Field-level encryption for PII

---

## Implementation Examples

### Example 1: Fixed Create Patient Endpoint
```python
@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(
    request: PatientCreate,
    current_user: User = Depends(get_doctor),  # ✅ Doctor only
    db: Session = Depends(get_db_for_request)
):
    """Create a new patient (Doctor only)"""

    patient = Patient(
        id=str(uuid.uuid4()),
        org_id=current_user.org_id,
        created_by=current_user.id,  # ✅ Track creator
        updated_by=current_user.id,
        # ... rest of fields
    )

    db.add(patient)
    db.commit()

    # ✅ Log access
    log_patient_access(db, current_user.id, patient.id, "create")

    logger.info(f"Patient created by {current_user.email}")
    return PatientResponse.from_orm(patient)
```

### Example 2: Fixed Delete Patient (Soft Delete)
```python
@app.delete("/api/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_doctor),  # ✅ Doctor only
    db: Session = Depends(get_db_for_request)
):
    """Delete patient (Soft delete - Doctor only)"""

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.org_id == current_user.org_id,
        Patient.deleted_at == None  # ✅ Only soft-deleted
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ✅ Soft delete
    patient.deleted_at = datetime.utcnow()
    patient.deleted_by = current_user.id
    db.commit()

    # ✅ Log access
    log_patient_access(db, current_user.id, patient.id, "delete")

    return {"message": "Patient deleted successfully"}
```

### Example 3: Nurse-Limited Patient View
```python
@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_request)
):
    """Get patient details (limited for nurses)"""

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.org_id == current_user.org_id,
        Patient.deleted_at == None
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ✅ Nurses can only view if assigned to a visit
    if current_user.role == UserRole.NURSE:
        assigned_visit = db.query(PatientVisit).filter(
            PatientVisit.prescription_id == db.query(Prescription).filter(
                Prescription.patient_id == patient_id
            ).first().id,
            PatientVisit.assigned_nurse == current_user.id
        ).first()

        if not assigned_visit:
            raise HTTPException(status_code=403, detail="Not assigned to this patient")

    # ✅ Log access
    log_patient_access(db, current_user.id, patient.id, "read")

    return PatientResponse.from_orm(patient)
```

---

## Testing Checklist

- [ ] Nurse cannot create patients
- [ ] Nurse cannot update patient records
- [ ] Nurse cannot delete patients
- [ ] Nurse can only view patients with assigned visits
- [ ] Doctor can create/read/update/delete patients
- [ ] All patient operations logged with user ID
- [ ] Deleted patients marked soft-deleted, not hard-deleted
- [ ] Access logs show who accessed what when
- [ ] HIPAA audit reports can be generated

---

## Risk Assessment

| Issue | Severity | HIPAA | Timeline | Status |
|-------|----------|-------|----------|--------|
| No role enforcement | 🔴 CRITICAL | Yes | Phase 1 | ⚠️ TODO |
| No creator tracking | 🔴 CRITICAL | Yes | Phase 1 | ⚠️ TODO |
| No soft delete | 🔴 CRITICAL | Yes | Phase 1 | ⚠️ TODO |
| No access logs | 🟠 HIGH | Yes | Phase 1 | ⚠️ TODO |
| No change history | 🟡 MEDIUM | Yes | Phase 2 | ⚠️ TODO |
| No access limits for nurses | 🟡 MEDIUM | Yes | Phase 2 | ⚠️ TODO |

---

## Next Steps

1. **Review & Approve** - Stakeholders review this assessment
2. **Prioritize** - Choose implementation order based on risk/effort
3. **Implement Phase 1** - Critical fixes before any HIPAA use
4. **Test Thoroughly** - Security & compliance testing
5. **Document** - Update API docs with new access controls
6. **Train** - Educate users on new role-based access

---

## Questions for Product/Compliance

1. Should patients be modifiable after initial creation?
2. Can nurses update patient records during visits?
3. What's the data retention policy?
4. Do you need role-based access or org-wide visibility?
5. Who should approve patient deletions?
6. What audit trail is required for compliance?

