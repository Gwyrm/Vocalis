# Demo Data Seeding Guide

This document explains how to populate your Vocalis database with realistic demo data for presentations and testing.

## Overview

The `seed_demo_data.py` script creates a complete demo environment with:
- **1 Demo Organization**: Hôpital Saint-Louis Demo
- **2 Demo Users**: Doctor + Nurse with demo credentials
- **5 Demo Patients**: With realistic medical histories
- **11 Demo Prescriptions**: Various medications and conditions
- **5 Demo Devices**: Common medical devices (blood pressure monitors, glucose meters, etc.)
- **4 Demo Patient Visits**: Different statuses (pending, in_progress, completed)
- **3 Demo Nurse Locations**: GPS location history

## Running the Script

### Prerequisites
1. Backend environment is set up with dependencies installed
2. Database connection is configured (PostgreSQL or SQLite)
3. Tables are created (they're auto-created if needed)

### Steps

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Run the seed script
python seed_demo_data.py
```

### Output

You should see output like:
```
Creating demo organization...
✓ Organization created: Hôpital Saint-Louis Demo
Creating demo users...
✓ Doctor user created: doctor@hopital-demo.fr
✓ Nurse user created: nurse@hopital-demo.fr
Creating demo patients...
✓ 5 demo patients created
Creating demo prescriptions...
✓ 11 demo prescriptions created
Creating demo devices...
✓ 5 demo devices created
Creating demo patient visits...
✓ 4 demo patient visits created
Creating demo nurse locations...
✓ 3 demo nurse locations created

============================================================
✅ DEMO DATA SUCCESSFULLY CREATED!
============================================================

Demo Organization: Hôpital Saint-Louis Demo
Demo Doctor: doctor@hopital-demo.fr / Password: demo123
Demo Nurse: nurse@hopital-demo.fr / Password: demo123
Demo Patients: 5
Demo Prescriptions: 11
Demo Devices: 5
Demo Visits: 4

You can now login to present the app!
============================================================
```

## Demo Credentials

### Doctor Account
- **Email**: `doctor@hopital-demo.fr`
- **Password**: `demo123`
- **Name**: Dr. Marie Dubois
- **Permissions**: Create prescriptions, manage patients, view nurse locations

### Nurse Account
- **Email**: `nurse@hopital-demo.fr`
- **Password**: `demo123`
- **Name**: Infirmière Sophie Martin
- **Permissions**: View assigned visits, complete visits, record GPS locations

## Demo Data Details

### Demo Patients (5 patients)

#### 1. Jean Dupont
- **Age**: 59 years old
- **Conditions**: Hypertension, Diabetes type 2
- **Allergies**: Penicillin, Latex
- **Current Medications**: Metoprolol, Metformin
- **Prescriptions**: 3 (Metoprolol, Metformin, Amoxicillin)
- **Status**: Active patient with completed prescriptions

#### 2. Marie Martin
- **Age**: 46 years old
- **Conditions**: Asthma, GERD
- **Allergies**: Aspirin
- **Current Medications**: Albuterol, Omeprazole
- **Prescriptions**: 2 (Albuterol, Omeprazole)
- **Status**: Well-controlled asthma

#### 3. Pierre Bernard
- **Age**: 69 years old
- **Conditions**: Rheumatoid Arthritis, Hypercholesterolemia
- **Allergies**: None
- **Current Medications**: Methotrexate, Atorvastatin
- **Prescriptions**: 2 (Methotrexate, Atorvastatin)
- **Status**: In-progress visit, good treatment response

#### 4. Isabelle Rousseau
- **Age**: 32 years old
- **Conditions**: Chronic Migraines
- **Allergies**: Sulfonamides
- **Current Medications**: Propranolol, Sumatriptan
- **Prescriptions**: 2 (Propranolol for prevention, Sumatriptan for acute)
- **Status**: Pending visit scheduled

#### 5. Claude Leclerc
- **Age**: 54 years old
- **Conditions**: Atrial Fibrillation, Heart Failure
- **Allergies**: None
- **Current Medications**: Warfarin, Digoxin, Furosemide
- **Prescriptions**: 2 (Warfarin, Digoxin)
- **Status**: Requires close monitoring

### Demo Prescriptions (11 total)

Prescriptions are distributed across patients with:
- **Active status**: Current medications being used
- **Completed status**: Past prescriptions (shown in history)
- **Realistic details**: Dosages, durations, special instructions
- **Medical context**: Linked to patient conditions and allergies
- **Doctor attribution**: All created by demo doctor

### Demo Devices (5 total)

1. **Electronic Blood Pressure Monitor** - Omron M3
2. **Glucose Meter** - Accu-Chek Guide
3. **Pulse Oximeter** - Nonin PalmSat
4. **Infrared Thermometer** - Braun ThermoScan
5. **Peak Flow Meter** - AirZone

### Demo Visits (4 total)

#### Visit 1: Jean Dupont - Completed
- Status: Completed 3 days ago
- Notes: Blood pressure follow-up at home
- Device: Tensiomètre

#### Visit 2: Marie Martin - Completed
- Status: Completed 5 days ago
- Notes: Asthma control check, good adherence

#### Visit 3: Pierre Bernard - In Progress
- Status: In progress since 1 day ago
- Notes: Arthritis follow-up, physical therapy recommended

#### Visit 4: Isabelle Rousseau - Pending
- Status: Scheduled for 2 days from now
- Notes: Awaiting nurse visit

### Demo Locations (Nurse GPS History)

3 location entries showing nurse's daily movement:
- **Paris Centre** - 2 days ago
- **Marais** - 1 day ago
- **Belleville** - Today

## Presentation Workflow

### 1. Login as Doctor
```
Email: doctor@hopital-demo.fr
Password: demo123
```
- View patient list (5 patients)
- Click on a patient to see:
  - Medical information (allergies, conditions, medications)
  - **Prescription history** (all past and current prescriptions)
  - Options to create new voice/text prescriptions
- View nurse locations on map

### 2. Login as Nurse
```
Email: nurse@hopital-demo.fr
Password: demo123
```
- View assigned visits (4 visits in various statuses)
- Complete a visit:
  - Record device reading
  - Add notes
  - Capture patient signature
  - Mark as completed

### 3. Feature Highlights

**Patient Management**
- Rich patient profiles with medical history
- Allergy and condition tracking
- Current medication list

**Prescription System**
- Voice-to-text prescription creation
- Manual text prescription input
- Medication validation (allergies, interactions)
- Full prescription history per patient
- Status tracking (active, completed, archived)

**Visit Management**
- Nurse assignment and scheduling
- Visit status workflow
- Device integration for readings
- Visit completion with notes and signatures

**Mobile Features**
- GPS location tracking for nurses
- Photo attachments
- Offline-first capability
- Real-time sync

## Database Cleanup

To reset and recreate demo data:

```bash
# Option 1: Delete the database file (for SQLite)
rm backend/vocalis_demo.db

# Option 2: Manually delete tables via database tool
# Then run: python seed_demo_data.py

# Option 3: Run script again (it will use existing org/users/patients)
# Script checks for existing data and appends
```

## Customization

To customize demo data, edit `seed_demo_data.py`:

1. **Change patient names**: Modify `patients_data` list
2. **Add more prescriptions**: Add items to `prescriptions_data`
3. **Change organization name**: Edit `Organization(name="...")`
4. **Adjust timestamps**: Modify `days_ago` values for visits/locations
5. **Add more devices**: Extend `devices_data`

## Notes

- **Patient IDs**: Generated as UUIDs, unique per run
- **Timestamps**: Based on current time, can be adjusted in script
- **Backward compatible**: Existing patient_id foreign keys are nullable
- **Medical data**: Sample data is realistic but fictional
- **Passwords**: All demo users use simple password "demo123" for demo purposes

## Troubleshooting

### Script fails with database error
```
Error: Could not connect to database
Solution: Ensure database environment variables are set correctly
```

### Duplicate data created
```
Solution: Script uses UUIDs, so running multiple times creates duplicates
Delete data or modify script to check for existing org
```

### Missing imports
```
Error: ModuleNotFoundError
Solution: Activate virtual environment and install requirements.txt
```

## Next Steps for Presentation

1. ✅ Run `python seed_demo_data.py`
2. ✅ Start backend: `python main.py`
3. ✅ Launch frontend: `flutter run`
4. ✅ Login with demo credentials
5. ✅ Navigate to patient list
6. ✅ Click on a patient to show:
   - Medical profile
   - **Prescription history section** (newest feature!)
   - Create new prescription options
7. ✅ Demo voice/text prescription creation
8. ✅ Show prescription validation with medication checking
9. ✅ Demonstrate prescription history updates

Enjoy your presentation! 🎉
