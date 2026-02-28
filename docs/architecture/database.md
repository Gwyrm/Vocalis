# Database Schema

Vocalis uses SQLite for data persistence with the following schema.

## Tables Overview

### Users
Stores user accounts and authentication information.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| email | String | Unique email address |
| password_hash | String | Bcrypt hashed password |
| full_name | String | User's full name |
| role | Enum | DOCTOR or NURSE |
| org_id | UUID | Organization ID (foreign key) |
| is_active | Boolean | Account status |
| last_login | DateTime | Last login timestamp |
| created_at | DateTime | Creation timestamp |

### Patients
Patient medical information.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| org_id | UUID | Organization ID (foreign key) |
| first_name | String | Patient first name |
| last_name | String | Patient last name |
| date_of_birth | Date | Date of birth |
| gender | String | M/F/Other |
| phone | String | Contact phone |
| email | String | Contact email |
| address | String | Home address |
| allergies | Text | JSON array of allergies |
| chronic_conditions | Text | JSON array of conditions |
| current_medications | Text | JSON array of medications |
| medical_notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Prescriptions
Prescription records.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| patient_id | UUID | Patient ID (foreign key) |
| created_by | UUID | Doctor ID (foreign key) |
| org_id | UUID | Organization ID (foreign key) |
| patient_name | String | Patient name (denormalized) |
| patient_age | String | Patient age at creation |
| diagnosis | String | Clinical diagnosis |
| medication | String | Medication name |
| dosage | String | Dosage information |
| duration | String | Treatment duration |
| special_instructions | String | Special instructions |
| status | String | draft/signed/completed |
| is_signed | Boolean | Signature status |
| doctor_signed_at | DateTime | Signature timestamp |
| created_at | DateTime | Creation timestamp |

### Organizations
Organization/clinic information.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Organization name |
| address | String | Organization address |
| phone | String | Contact phone |
| created_at | DateTime | Creation timestamp |

## Relationships

```
Organizations (1) ←──→ (Many) Users
              │
              └─────→ Patients
                        │
                        └─→ Prescriptions

Users (1) ←─── (Many) Prescriptions
```

## Indexes

For optimal query performance:

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(org_id);
CREATE INDEX idx_patients_org ON patients(org_id);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_created_by ON prescriptions(created_by);
CREATE INDEX idx_prescriptions_created_at ON prescriptions(created_at);
```

## Data Types

### JSON Fields

Stored as TEXT but contain JSON:

```json
allergies: ["Penicillin", "Aspirin"]
chronic_conditions: ["Diabetes", "Hypertension"]
current_medications: ["Metformin", "Lisinopril"]
```

---

**Next:** See [Architecture](design.md) for system overview
