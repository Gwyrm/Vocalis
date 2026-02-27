# Demo Database Setup

## Overview

Vocalis now maintains **separate databases** for demo and production accounts to keep test data isolated from real user data.

- **demo.db** - Demo account test data (doctor@hopital-demo.fr)
- **vocalis.db** - Production user data and real prescriptions

## How It Works

When a user logs in, the system automatically selects the correct database:

```
User Login
  ↓
Check Email
  ├→ demo@hopital-demo.fr → Use demo.db
  └→ Any other email → Use vocalis.db
  ↓
Load User from Selected Database
  ↓
Create JWT Token
  ↓
All Subsequent Requests Use Same Database
```

## Database Files

### Production Database (`vocalis.db`)
- Used by all regular user accounts
- Persists user-created patients, prescriptions, and visit data
- Should be backed up regularly

### Demo Database (`demo.db`)
- Used only by demo account
- Can be reset anytime by deleting the file
- Comes with pre-seeded demo data:
  - 1 Demo Organization
  - 1 Demo User (doctor)
  - 5 Sample Patients
  - Multiple Demo Prescriptions

## Resetting Demo Database

To clear demo data and start fresh:

```bash
# Delete the demo database
rm backend/demo.db

# Restart the backend
# The database will be recreated on first login with demo account
```

## Implementation Details

### Files Modified

**backend/database.py**
- Two SQLAlchemy engines: `prod_engine` and `demo_engine`
- `get_db_for_user(email)` dependency selects correct database
- Both databases initialized with same schema on startup

**backend/main.py**
- Login endpoint checks user email and routes to correct database
- `get_current_user()` dependency uses correct database for token verification
- All subsequent endpoints automatically use correct database via token email

### Technical Details

```python
# Database selection logic
DEMO_ACCOUNT_EMAIL = "doctor@hopital-demo.fr"

if user_email.lower() == DEMO_ACCOUNT_EMAIL.lower():
    # Use demo database
    db = DemoSessionLocal()
else:
    # Use production database
    db = ProdSessionLocal()
```

## Testing

### Test Demo Account
```bash
# Login with demo credentials
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hopital-demo.fr",
    "password": "demo123"
  }'

# Token will use demo.db for all subsequent requests
```

### Test Production Account (if created)
```bash
# Login with regular account
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "regular@example.com",
    "password": "password123"
  }'

# Token will use vocalis.db for all subsequent requests
```

## Seeding Demo Data

To reseed the demo database with fresh data:

```bash
cd backend
python3 seed_demo_data.py

# This recreates demo.db with sample data
```

## Important Notes

⚠️ **Data Isolation**: Changes to demo account data do NOT affect production users and vice versa

✅ **Automatic**: No configuration needed - database selection is automatic based on email

✅ **Transparent**: Applications and API calls work the same way - database switching is hidden

## Future Enhancements

- Multi-organization support (each org gets separate database shard)
- Database backup automation
- Demo data reset endpoint (admin only)
- Analytics on demo vs production usage
