# Installation Guide

Get Vocalis running on your system in a few simple steps.

## Prerequisites

### Backend Requirements
- Python 3.11 or higher
- pip (Python package manager)
- SQLite3 (usually included with Python)
- 2GB RAM minimum
- Ollama (for LLM) - optional, can be installed separately

### Frontend Requirements
- Flutter SDK 3.11+
- Dart 3.11+
- A modern web browser (Chrome, Firefox, Safari, Edge)

### System Requirements
- macOS 10.15+, Linux, or Windows 10+
- 4GB RAM recommended
- 2GB free disk space

## Backend Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Vocalis/backend
```

### 2. Create Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `python-jose` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `whisper` - Audio transcription
- `httpx` - Async HTTP client
- `uvicorn` - ASGI server

### 4. Setup Ollama (LLM)

**Option A: Using Ollama (Recommended)**

```bash
# Install Ollama from https://ollama.ai
ollama pull mistral
```

**Option B: Using Docker**

```bash
docker run -d -p 11434:11434 ollama/ollama
docker exec ollama ollama pull mistral
```

### 5. Run Backend Server

```bash
cd backend
python main.py
```

Backend will start at: `http://localhost:8080`

**Health Check:**
```bash
curl http://localhost:8080/api/health
```

Expected response:
```json
{
  "status": "ok",
  "backend": "running",
  "database": "connected",
  "ollama_available": true
}
```

## Frontend Setup

### 1. Install Flutter

```bash
# Install Flutter from https://flutter.dev/docs/get-started/install
flutter --version  # Verify installation
```

### 2. Get Dependencies

```bash
cd Vocalis/frontend
flutter pub get
```

### 3. Run on Web

```bash
flutter run -d chrome
```

**Or for production:**

```bash
flutter build web --release
```

### 4. Run on Mobile (iOS/Android)

```bash
# iOS
flutter run -d ios

# Android
flutter run -d android
```

### 5. Run on Desktop

```bash
# macOS
flutter run -d macos

# Windows
flutter run -d windows

# Linux
flutter run -d linux
```

## Docker Setup (Optional)

### Build and Run with Docker

```bash
# Backend
cd backend
docker build -t vocalis-backend .
docker run -p 8080:8080 vocalis-backend

# Frontend
cd ../frontend
docker build -t vocalis-frontend .
docker run -p 3000:80 vocalis-frontend
```

## Verify Installation

### Backend

```bash
# Test health endpoint
curl http://localhost:8080/api/health

# Test login endpoint
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hopital-demo.fr","password":"demo123"}'
```

### Frontend

```bash
# Browser should open automatically with: http://localhost:59000
```

## Environment Variables

### Backend (.env file)

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=sqlite:///./vocalis.db
DEMO_DATABASE_URL=sqlite:///./demo.db

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:*,http://127.0.0.1:*

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_TIMEOUT=120.0

# LLM Model
LLM_MODEL=mistral
```

### Frontend (lib/main.dart)

```dart
// API_URL is defined via command line:
final apiUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://localhost:8080',
);
```

## Troubleshooting

### Backend Issues

**Port 8080 already in use:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>
```

**Ollama not found:**
- Install Ollama from https://ollama.ai
- Verify it's running: `curl http://localhost:11434`

**Database locked:**
```bash
# Remove lock file
rm *.db-shm *.db-wal
```

### Frontend Issues

**Flutter not found:**
```bash
flutter doctor  # Check installation
export PATH="$PATH:$HOME/flutter/bin"  # Add to PATH
```

**Port 8080 in use (frontend trying to connect):**
- Backend should be running on 8080
- Or change API_URL in code

**Dependencies not resolving:**
```bash
flutter clean
flutter pub get
```

## Demo Data

Default accounts available after first run:

```
Doctor:
  Email: doctor@hopital-demo.fr
  Password: demo123

Nurse:
  Email: nurse@hopital-demo.fr
  Password: demo123
```

## Next Steps

✅ **Installation complete!**

- [Quick Start](quickstart.md) - Create your first prescription
- [API Documentation](../architecture/api.md) - Explore endpoints
- [Testing Guide](../testing/backend.md) - Run tests

---

**Need help?** Check the [Troubleshooting](../troubleshooting.md) guide.
