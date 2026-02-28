# Vocalis - AI Medical Prescription System

Welcome to the Vocalis documentation. Vocalis is a modern medical AI assistant platform designed to help physicians create, manage, and track medical prescriptions using both text and voice input.

## 🎯 Key Features

- **🗣️ Voice Input**: Transcribe prescription dictation using Whisper AI
- **📝 Text Input**: Create prescriptions via natural language text
- **🤖 AI Processing**: LLM-powered prescription extraction and validation
- **👥 Multi-User**: Support for doctors and nurses with role-based access
- **📱 Cross-Platform**: Flutter frontend for web, iOS, Android, and desktop
- **🔐 Security**: JWT authentication with bcrypt password hashing
- **📊 Prescription History**: Complete patient prescription tracking
- **⚡ Real-time**: Instant confirmation and validation

## 📚 Documentation Sections

### Getting Started
- [Overview](getting-started/overview.md) - Project vision and goals
- [Installation](getting-started/installation.md) - Setup instructions
- [Quick Start](getting-started/quickstart.md) - Get running in 5 minutes

### Architecture
- [System Design](architecture/design.md) - Component overview
- [Database](architecture/database.md) - Data model and schema
- [API](architecture/api.md) - REST API structure

### API Documentation
- [Authentication](api/authentication.md) - Login, tokens, permissions
- [Patients](api/patients.md) - Patient management endpoints
- [Prescriptions](api/prescriptions.md) - Prescription CRUD operations
- [Users](api/users.md) - User profile and settings

### Features
- [Text Prescriptions](features/text-prescriptions.md) - Natural language input
- [Voice Prescriptions](features/voice-prescriptions.md) - Audio transcription
- [Prescription History](features/history.md) - Patient tracking
- [User Roles](features/user-roles.md) - Permissions and access control

### Testing & Deployment
- [Backend Testing](testing/backend.md) - API test suite
- [Manual Testing](testing/manual.md) - Testing procedures
- [Backend Deployment](deployment/backend.md) - Production setup
- [Frontend Deployment](deployment/frontend.md) - Web & mobile builds

## 🚀 Quick Links

**Demo Credentials:**
```
Doctor Account:
  Email: doctor@hopital-demo.fr
  Password: demo123

Nurse Account:
  Email: nurse@hopital-demo.fr
  Password: demo123
```

**Backend API**: `http://localhost:8080`

**Frontend**: Built with Flutter (web, iOS, Android, macOS, Windows, Linux)

## 💻 Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite / PostgreSQL
- **Authentication**: JWT + bcrypt
- **AI/ML**:
  - Whisper (audio transcription)
  - Mistral LLM (prescription parsing)
- **Deployment**: Uvicorn

### Frontend
- **Framework**: Flutter (Dart)
- **State Management**: Provider
- **Storage**: SharedPreferences
- **HTTP**: http package

## 📖 How to Use This Documentation

1. **New to Vocalis?** Start with [Getting Started](getting-started/overview.md)
2. **Want to set up?** Follow [Installation](getting-started/installation.md)
3. **Need API docs?** Check [API Documentation](architecture/api.md)
4. **Testing the system?** See [Testing Guide](testing/backend.md)
5. **Deploying?** Read [Deployment Guides](deployment/backend.md)

## 🤝 Support

For issues, questions, or contributions, refer to the [Troubleshooting](troubleshooting.md) guide or check the GitHub repository.

---

**Status**: ✅ Production Ready | **Version**: 1.0.0
