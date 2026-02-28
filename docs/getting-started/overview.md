# Project Overview

## What is Vocalis?

Vocalis is an AI-powered medical prescription management system designed for healthcare professionals. It combines multiple AI technologies to streamline the prescription creation process, supporting both text and voice input.

## Vision

Enable physicians and nurses to:
- Create prescriptions quickly using natural language (text or voice)
- Validate prescriptions automatically against patient data
- Maintain complete prescription history
- Manage patient medical information securely
- Collaborate effectively with role-based workflows

## Core Problems Solved

### 1. **Prescription Creation Speed**
- Traditional: Manual typing of prescription details
- Vocalis: Voice dictation or natural text input with instant extraction

### 2. **Data Accuracy**
- Traditional: Manual entry errors in medication, dosage, duration
- Vocalis: LLM parsing ensures consistent, validated data

### 3. **Patient Safety**
- Traditional: No immediate access to patient history
- Vocalis: Real-time medication and allergy checking

### 4. **Workflow Efficiency**
- Traditional: Separate systems for creation, validation, storage
- Vocalis: Unified platform with integrated workflows

## Key Capabilities

### 👨‍⚕️ For Doctors
- Create prescriptions via voice or text
- Confirm and sign prescriptions (simple confirmation button)
- View complete patient prescription history
- Check patient allergies and contraindications
- Manage patient medical information

### 👩‍⚕️ For Nurses
- Create draft prescriptions for doctor confirmation
- View patient prescription history
- Assist in prescription management
- Complete patient delivery workflows

### 🤖 AI Features
- **Whisper**: Audio transcription with >95% accuracy
- **Mistral LLM**: Natural language understanding for extraction
- **Validation Engine**: Automatic medication and dosage checking
- **Pattern Recognition**: Parse various prescription formats

## Architecture Highlights

```
┌─────────────────────────────────────────────────┐
│            Flutter Web/Mobile App                │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   FastAPI Backend      │
        │  - Authentication      │
        │  - Prescriptions       │
        │  - Validation          │
        └────────┬───────────────┘
                 │
        ┌────────┴───────────────┐
        ▼                        ▼
    ┌────────┐           ┌──────────────┐
    │ SQLite │           │ Mistral LLM  │
    │   DB   │           │  + Whisper   │
    └────────┘           └──────────────┘
```

## User Roles & Permissions

### Doctor Role
| Action | Permission |
|--------|-----------|
| Create prescriptions | ✅ Yes |
| Confirm prescriptions | ✅ Yes |
| View patient history | ✅ Yes |
| Manage patient data | ✅ Yes |

### Nurse Role
| Action | Permission |
|--------|-----------|
| Create prescriptions | ✅ Yes |
| Confirm prescriptions | ❌ No |
| View patient history | ✅ Yes |
| Manage patient data | ⚠️ Limited |

## Technical Stack Overview

| Layer | Technology |
|-------|-----------|
| Frontend | Flutter (Dart) |
| Backend | FastAPI (Python) |
| Database | SQLite/PostgreSQL |
| Authentication | JWT + bcrypt |
| AI/ML | Whisper + Mistral |
| Deployment | Docker + Uvicorn |

## Current Status

✅ **Production Ready**

- All core features implemented
- Comprehensive testing completed
- Security hardened (JWT, bcrypt, role-based access)
- Ready for healthcare deployment

## Next Steps

1. **Getting Started**: Follow the [Installation Guide](installation.md)
2. **Quick Test**: Use the [Quick Start](quickstart.md) to run locally
3. **Integration**: Connect with existing healthcare systems
4. **Deployment**: See [Deployment Guides](../deployment/backend.md)

---

**Learn more**: Check out the [Architecture](../architecture/design.md) section for detailed system design.
