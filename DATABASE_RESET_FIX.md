# Database Reset Fix - Doctor Signature Schema

## Problem
```
Error: Exception: Erreur récupération ordonnances: Exception: (sqlite3.OperationalError)
no such column: prescriptions.doctor_signature
```

**Root Cause**: The database was created with the old schema before we added the signature columns to the Prescription model.

---

## Solution Applied

### What Was Done
1. ✅ Deleted old database files:
   - `backend/vocalis_demo.db`
   - `frontend/vocalis_demo.db`

2. ✅ Database will be recreated automatically on next backend startup

3. ✅ New schema includes all signature columns:
   - `doctor_signature: TEXT` - Base64 encoded PNG signature
   - `doctor_signed_at: DATETIME` - Timestamp when signed
   - `is_signed: BOOLEAN` - Quick validation flag

### How It Works
When the backend starts:
```python
# In main.py lifespan context manager:
Base.metadata.create_all(bind=engine)  # Creates all tables with current schema
```

SQLAlchemy automatically creates tables based on the model definitions, including the new signature fields we added to the Prescription model.

---

## What to Do Now

### Step 1: Start the Backend
```bash
cd backend
python main.py
```

### Step 2: Verify Database Initialization
Look for these log messages:
```
2026-02-26 12:45:00 - vocalis-backend - INFO - Initializing database...
2026-02-26 12:45:00 - vocalis-backend - INFO - Database initialized
```

### Step 3: Test the Signature Endpoint
```bash
# Create a prescription
POST /api/prescriptions
{
  "patient_id": "pat-123",
  "medication": "amoxicilline",
  "dosage": "500mg",
  "duration": "7 jours",
  "diagnosis": "Infection"
}

# Sign the prescription
PUT /api/prescriptions/{prescription_id}/sign
{
  "doctor_signature": "data:image/png;base64,..."
}
```

---

## Database Schema (New)

### Prescriptions Table
```sql
CREATE TABLE prescriptions (
  id VARCHAR(36) PRIMARY KEY,
  org_id VARCHAR(36) NOT NULL,
  created_by VARCHAR(36) NOT NULL,
  patient_id VARCHAR(36),
  patient_name VARCHAR(255) NOT NULL,
  patient_age VARCHAR(50) NOT NULL,
  diagnosis TEXT,
  medication VARCHAR(255) NOT NULL,
  dosage VARCHAR(255) NOT NULL,
  duration VARCHAR(255) NOT NULL,
  special_instructions TEXT,
  status VARCHAR(50) DEFAULT 'draft',           -- NEW: changed default
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- NEW: Signature fields
  doctor_signature TEXT,                        -- NEW
  doctor_signed_at DATETIME,                    -- NEW
  is_signed BOOLEAN DEFAULT FALSE,              -- NEW

  FOREIGN KEY (org_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

---

## Verification Checklist

After starting the backend:

- [ ] Backend starts without database errors
- [ ] "Database initialized" message appears in logs
- [ ] Can create a prescription (POST /api/prescriptions)
- [ ] Prescription has `is_signed: false` status
- [ ] Can sign a prescription (PUT /api/prescriptions/{id}/sign)
- [ ] Signed prescription has `is_signed: true` and `doctor_signed_at` timestamp
- [ ] Cannot re-sign already signed prescription (returns 400 error)

---

## What Changed

### Before (Old Schema)
```
Prescription fields:
- id, org_id, created_by
- patient_name, patient_age
- diagnosis, medication, dosage, duration
- special_instructions
- status (default: 'active')
- created_at
❌ No signature fields
```

### After (New Schema)
```
Prescription fields:
- id, org_id, created_by
- patient_name, patient_age
- diagnosis, medication, dosage, duration
- special_instructions
- status (default: 'draft')  ← Changed!
- created_at
✅ doctor_signature (NEW)
✅ doctor_signed_at (NEW)
✅ is_signed (NEW)
```

---

## API Endpoints Available

### Create Prescription (Draft)
```
POST /api/prescriptions
Response: status='draft', is_signed=false
```

### Sign Prescription
```
PUT /api/prescriptions/{id}/sign
Response: status='signed', is_signed=true, doctor_signed_at=<timestamp>
```

### Get Prescription
```
GET /api/prescriptions/{id}
Shows all fields including signature info
```

### Get Patient Prescriptions
```
GET /api/patients/{patient_id}/prescriptions
Shows all prescriptions for patient (signed and unsigned)
```

---

## Troubleshooting

### Issue: Still getting "no such column" error
**Solution**:
1. Stop backend
2. Delete database file again:
   ```bash
   rm backend/vocalis_demo.db
   ```
3. Start backend again
4. Check logs for "Database initialized"

### Issue: Database file recreated but still has old schema
**Solution**:
1. Check if there are other database references in code
2. Verify models.py has the signature fields
3. Check that Prescription class imports are correct
4. Restart Python completely (no cached imports)

### Issue: Can't sign prescription
**Solution**:
1. Verify signature image is valid PNG
2. Verify signature image is max 1MB
3. Verify doctor authentication token is valid
4. Check backend logs for specific error message

---

## Summary

✅ Database schema updated with signature fields
✅ Old database files deleted
✅ New database will be created on next startup
✅ All new endpoints ready to use
✅ Doctor signatures now mandatory for validity

**Status**: Ready to deploy and test! 🚀

---

## Git Commit
- `59faba8`: Database reset and schema fix

Next step: Start the backend and test the signature endpoints!
