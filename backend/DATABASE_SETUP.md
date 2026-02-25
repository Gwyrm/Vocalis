# Database Setup Guide

## Phase 1: Core Setup

### Prerequisites
- PostgreSQL 12+ installed and running
- Python 3.11+

### Step 1: Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# Run these commands:
CREATE USER vocalis WITH PASSWORD 'vocalis';
CREATE DATABASE vocalis OWNER vocalis;
GRANT ALL PRIVILEGES ON DATABASE vocalis TO vocalis;
\q
```

### Step 2: Configure Environment

Copy `.env.example` to `.env` and update if needed:

```bash
cp .env.example .env
```

Default values work for local development:
- `DATABASE_URL=postgresql://vocalis:vocalis@localhost/vocalis`
- `JWT_SECRET=your-secret-key-change-in-production` (change in production!)

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

Tables will be created automatically on first startup:

```bash
python main.py
```

Or manually:

```python
from database import init_db
init_db()
```

## Database Schema

### users
```sql
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'doctor' or 'nurse'
  org_id VARCHAR(36) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  last_login TIMESTAMP,
  FOREIGN KEY (org_id) REFERENCES organizations(id)
);
```

### prescriptions
```sql
CREATE TABLE prescriptions (
  id VARCHAR(36) PRIMARY KEY,
  org_id VARCHAR(36) NOT NULL,
  created_by VARCHAR(36) NOT NULL,
  patient_name VARCHAR(255) NOT NULL,
  patient_age VARCHAR(50) NOT NULL,
  diagnosis TEXT,
  medication VARCHAR(255) NOT NULL,
  dosage VARCHAR(255) NOT NULL,
  duration VARCHAR(255) NOT NULL,
  special_instructions TEXT,
  status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'archived'
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (org_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### organizations
```sql
CREATE TABLE organizations (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  address VARCHAR(500),
  phone VARCHAR(20),
  created_at TIMESTAMP DEFAULT now()
);
```

### devices
```sql
CREATE TABLE devices (
  id VARCHAR(36) PRIMARY KEY,
  org_id VARCHAR(36) NOT NULL,
  name VARCHAR(255) NOT NULL,
  model VARCHAR(255),
  serial_number VARCHAR(255) UNIQUE,
  status VARCHAR(50) DEFAULT 'available',  -- 'available', 'assigned', 'in_use', 'maintenance'
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (org_id) REFERENCES organizations(id)
);
```

### patient_visits
```sql
CREATE TABLE patient_visits (
  id VARCHAR(36) PRIMARY KEY,
  org_id VARCHAR(36) NOT NULL,
  prescription_id VARCHAR(36) NOT NULL,
  assigned_nurse VARCHAR(36) NOT NULL,
  patient_address VARCHAR(500) NOT NULL,
  scheduled_date TIMESTAMP NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'cancelled'
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (org_id) REFERENCES organizations(id),
  FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
  FOREIGN KEY (assigned_nurse) REFERENCES users(id)
);
```

### visit_details
```sql
CREATE TABLE visit_details (
  id VARCHAR(36) PRIMARY KEY,
  visit_id VARCHAR(36) NOT NULL,
  device_id VARCHAR(36),
  nurse_notes TEXT,
  patient_signature TEXT,  -- Base64 encoded
  photos TEXT,  -- JSON array of file paths
  completed_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (visit_id) REFERENCES patient_visits(id),
  FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

### audit_logs
```sql
CREATE TABLE audit_logs (
  id VARCHAR(36) PRIMARY KEY,
  org_id VARCHAR(36) NOT NULL,
  user_id VARCHAR(36),
  action VARCHAR(255) NOT NULL,  -- 'created', 'updated', 'deleted', 'viewed'
  resource_type VARCHAR(100) NOT NULL,  -- 'prescription', 'visit', 'device'
  resource_id VARCHAR(36),
  changes TEXT,  -- JSON
  timestamp TIMESTAMP DEFAULT now(),
  FOREIGN KEY (org_id) REFERENCES organizations(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Testing

### Create First User

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "securepassword123",
    "full_name": "Dr. Jean Dupont",
    "role": "doctor"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Login

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "securepassword123"
  }'
```

### Create Prescription

```bash
curl -X POST http://localhost:8080/api/prescriptions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Jean Martin",
    "patient_age": "45",
    "diagnosis": "Hypertension",
    "medication": "Amlodipine",
    "dosage": "5mg once daily",
    "duration": "30 days",
    "special_instructions": "Take with water"
  }'
```

### List Prescriptions

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8080/api/prescriptions
```

## Production Considerations

1. **Change JWT_SECRET** to a strong random value
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** in production
4. **Set up proper backup** for PostgreSQL
5. **Configure firewall** to restrict database access
6. **Use connection pooling** for production (PgBouncer)
7. **Enable audit logging** for compliance
8. **Set up monitoring** and alerting
