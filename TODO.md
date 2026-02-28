# Vocalis Project - TODO & Done List

## ✅ Done

### Core Features
- [x] Flutter frontend with multi-screen UI (login, patients, prescriptions)
- [x] FastAPI backend with REST API
- [x] SQLite database with SQLAlchemy ORM
- [x] User authentication with JWT tokens and bcrypt password hashing
- [x] Role-based access control (Doctor, Nurse)
- [x] Organization/multi-tenant support
- [x] Patient management (list, view, edit)
- [x] Prescription creation with text input
- [x] Prescription creation with voice input (Whisper)
- [x] LLM-powered prescription data extraction (Mistral)
- [x] Prescription confirmation/signing
- [x] Prescription history tracking per patient
- [x] Demo mode with default credentials
- [x] Token persistence (SharedPreferences)
- [x] Auto-login on app startup if token saved
- [x] Logout functionality
- [x] User profile screen (view current user info)
- [x] Session management and token validation
- [x] Error handling with 401 redirects
- [x] API error messages in French

### Bug Fixes
- [x] Remove signature pad system (replaced with confirmation button)
- [x] Allow nurses to create prescriptions (text & voice)
- [x] Fix prescriptions not appearing in patient history (missing patient_id)
- [x] Fix dosage validation crash when null
- [x] Fix readonly database error
- [x] Fix auth error callback for auto-logout
- [x] Fix Nurse account creation in vocalis.db

### Documentation
- [x] Create mkdocs configuration
- [x] Write getting-started guides (overview, installation, quickstart)
- [x] Write architecture documentation (design, database schema, API overview)
- [x] Write API endpoint documentation (auth, patients, prescriptions, users)
- [x] Write comprehensive troubleshooting guide
- [x] Create deployment guides (placeholder)
- [x] Create feature documentation (placeholder)
- [x] Create testing guides (placeholder)
- [x] Build and serve documentation locally

### Security
- [x] Replace SHA256 with bcrypt for password hashing
- [x] Implement JWT Bearer token authentication
- [x] Add input sanitization for LLM prompts
- [x] Add signature image validation (PNG format, size limits)
- [x] Implement CORS configuration
- [x] Use async HTTP (httpx) instead of synchronous requests
- [x] Validate user roles for sensitive operations
- [x] Organization isolation for data queries

### Testing
- [x] Run comprehensive backend test suite
- [x] Test authentication flows (login, token validation)
- [x] Test prescription creation (text and voice)
- [x] Test permission checks (role-based access)
- [x] Test patient history tracking
- [x] Test error handling (401, 403, validation)
- [x] Manual testing of complete pipeline

### Infrastructure
- [x] Git repository setup with meaningful commits
- [x] Database initialization scripts
- [x] Virtual environment for Python
- [x] Requirements.txt with all dependencies
- [x] Demo data seeding

---

## 📋 To-Do

### High Priority
- [x] **Prescription Editing (Draft Only)**
  - [x] Add validation to prevent editing signed prescriptions
  - [x] Create EditPrescriptionScreen UI
  - [x] Add updatePrescription endpoint to backend
  - [x] Add Edit button visible only for draft prescriptions
  - [x] Implement draft/signed status logic

- [x] **Edit Extracted Data Before Validation**
  - [x] Create EditExtractedPrescriptionScreen for LLM-extracted data
  - [x] Allow editing immediately after prescription creation
  - [x] Fix LLM extraction errors before validation
  - [x] Integrated into text and voice prescription flows

- [ ] **Profile Management**
  - [ ] Add profile update endpoint (PUT /api/users/profile)
  - [ ] Add password change endpoint (POST /api/users/change-password)
  - [ ] Create ProfileScreen UI for email/name editing
  - [ ] Create password change form with validation
  - [ ] Add "Mon Profil" menu to PatientListScreen

- [ ] **Frontend Polish**
  - [ ] Add loading spinners on slow operations
  - [ ] Add better error messages for all screens
  - [ ] Add confirmation dialogs for destructive actions
  - [ ] Improve form validation messages
  - [ ] Add success notifications

- [ ] **Backend Improvements**
  - [ ] Add rate limiting for login attempts
  - [ ] Add audit logging (user actions)
  - [ ] Add password strength requirements
  - [ ] Add token refresh mechanism
  - [ ] Add password reset via email

### Medium Priority
- [ ] **Prescription Features**
  - [ ] Add prescription PDF export
  - [ ] Add prescription sharing capability
  - [ ] Add prescription editing (draft mode)
  - [ ] Add prescription notes field
  - [ ] Add medication interactions checking

- [ ] **Data Management**
  - [ ] Add patient photo/avatar
  - [ ] Add prescription attachments (lab results, images)
  - [ ] Add prescription templates for common medications
  - [ ] Add medication database integration
  - [ ] Add allergy warnings

- [ ] **User Experience**
  - [ ] Add dark mode support
  - [ ] Add internationalization (i18n)
  - [ ] Add offline capability for mobile
  - [ ] Add search/filter for patients
  - [ ] Add sort options for prescription lists

### Low Priority (Future Enhancements)
- [ ] **Analytics & Reporting**
  - [ ] Dashboard with prescription statistics
  - [ ] Usage reports by doctor/nurse
  - [ ] Patient outcome tracking
  - [ ] Prescription fill rate tracking

- [ ] **Advanced Features**
  - [ ] Real-time collaboration on prescriptions
  - [ ] AI-powered medication suggestions
  - [ ] Integration with external APIs (pharmacies, insurance)
  - [ ] Video consultation support
  - [ ] Mobile app push notifications

- [ ] **DevOps & Deployment**
  - [ ] Docker containerization
  - [ ] CI/CD pipeline (GitHub Actions)
  - [ ] Automated testing
  - [ ] Production database (PostgreSQL)
  - [ ] Cloud deployment (AWS/GCP/Azure)

---

## 🚧 In Progress

- mkdocs documentation (served locally at http://127.0.0.1:8000)

---

## 🐛 Known Issues & Limitations

### Current Limitations
- Database: SQLite (single-user, not suitable for production)
- Model: TinyLlama 1.1B (smaller model, less accurate than larger ones)
- Authentication: No password reset mechanism
- UI: Text-based only, no image support for prescriptions
- Performance: Voice processing takes 2-5 seconds

### Potential Issues
- [ ] Large prescription lists may be slow (needs pagination)
- [ ] No backup mechanism for database
- [ ] Voice input accuracy depends on audio quality
- [ ] LLM sometimes misses dosage or duration fields
- [ ] No concurrent request handling optimization

---

## 📊 Project Stats

### Code
- **Backend Files**: 5 main files (main.py, database.py, models.py, schemas.py, auth.py, voice_utils.py, llm_utils.py)
- **Frontend Files**: 12+ screens, 4+ providers, 3+ services
- **Documentation**: 20+ markdown files
- **Total Commits**: 30+

### Test Coverage
- Backend: ~30 individual tests (100% passing)
- Frontend: Manual testing completed
- Integration: Full pipeline tested

### Features Implemented
- 15+ REST endpoints
- 8+ screens in Flutter
- 5+ user roles/permissions
- 3+ prescription creation methods

---

## 🎯 Next Steps (Recommended Order)

1. **Profile Management** (High Priority)
   - Implement PUT /api/users/profile
   - Implement POST /api/users/change-password
   - Create ProfileScreen UI
   - Integrate with menu

2. **Frontend Polish** (High Priority)
   - Add comprehensive error handling
   - Improve form validation
   - Add loading states
   - Better user feedback

3. **Prescription PDF Export** (Medium Priority)
   - Generate printable PDFs
   - Add signature field to PDF
   - Email/share capability

4. **Database Migration** (Future)
   - Move to PostgreSQL
   - Implement connection pooling
   - Add proper backup strategy

5. **Deployment** (Future)
   - Containerize with Docker
   - Setup CI/CD
   - Deploy to production

---

## 📝 Last Updated
- **Date**: 2026-02-28
- **Last Commit**: ab48973 (docs: Add comprehensive MkDocs documentation)
- **Branch**: main
- **Status**: ✅ Stable - All core features working, ready for profile management phase
