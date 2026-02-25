# Vocalis Frontend - AI-Oriented App Implementation

## Overview

Complete Flutter frontend for the AI-oriented prescription system with voice and text input, patient management, and real-time validation.

## Architecture

### Project Structure
```
frontend/lib/
├── main.dart                              # App entry point
├── api_service.dart                       # Backend API client
├── models/
│   ├── patient.dart                       # Patient data model
│   ├── prescription.dart                  # Prescription & validation models
│   └── prescription_data.dart             # Legacy chat model
├── screens/
│   ├── patient_list_screen.dart           # Patient list & navigation
│   ├── patient_form_screen.dart           # Create/edit patient
│   ├── patient_detail_screen.dart         # Patient details & quick actions
│   ├── voice_prescription_screen.dart     # Voice recording & transcription
│   ├── text_prescription_screen.dart      # Text input & validation
│   └── validation_results_screen.dart     # Display validation results
└── chat_screen.dart                       # Legacy chat interface
```

## Features Implemented

### 1. Patient Management
- **List Screen** (`patient_list_screen.dart`)
  - Display all organization patients
  - Search and filter (ready for implementation)
  - Navigate to patient details or create new
  - Pull-to-refresh functionality

- **Form Screen** (`patient_form_screen.dart`)
  - Create new patients
  - Edit existing patient information
  - Full medical history management
  - Allergies, chronic conditions, medications
  - Date picker for birth date
  - Form validation

- **Detail Screen** (`patient_detail_screen.dart`)
  - View complete patient profile
  - Quick actions (create voice/text prescription)
  - Edit patient information
  - Display medical history
  - Patient statistics (age, conditions, allergies)

### 2. Voice Prescription
- **Voice Recording** (`voice_prescription_screen.dart`)
  - Real-time audio recording with Whisper permission handling
  - Recording timer display (MM:SS format)
  - Start/Stop/Retry controls
  - Audio file handling
  - Instructions for user guidance

### 3. Text Prescription
- **Text Input** (`text_prescription_screen.dart`)
  - Free-form text prescription entry
  - Recommended format template
  - Example prescription display
  - Real-time processing feedback
  - Clear instructions for data entry

### 4. Validation Results
- **Results Display** (`validation_results_screen.dart`)
  - Validation status (Valid/Invalid)
  - Confidence score display
  - Patient summary card
  - Prescription details (if valid)
  - Error messages with severity
  - Warning alerts with severity levels
  - Success confirmation

## Models

### Patient Model
```dart
class Patient {
  final String id;
  final String firstName;
  final String lastName;
  final DateTime dateOfBirth;
  final String? gender;
  final String? phone;
  final String? email;
  final List<String> allergies;
  final List<String> chronicConditions;
  final List<String> currentMedications;
  final String? medicalNotes;
  final DateTime createdAt;

  // Computed properties
  int get ageInYears { ... }
  String get fullName { ... }
}
```

### Prescription Validation Model
```dart
class PrescriptionValidation {
  final bool valid;
  final double confidence;
  final List<ValidationWarning> warnings;
  final List<ValidationError> errors;
}

class ValidationWarning {
  final String type;
  final String message;
  final String severity; // low, medium, high
}

class ValidationError {
  final String type;
  final String message;
  final String? field;
}
```

## API Integration

### Endpoints Used
- `POST /api/patients` - Create patient
- `GET /api/patients` - List patients
- `GET /api/patients/{id}` - Get patient details
- `PUT /api/patients/{id}` - Update patient
- `POST /api/voice/transcribe` - Transcribe audio
- `POST /api/prescriptions/voice` - Create voice prescription
- `POST /api/prescriptions/text` - Create text prescription

### Authentication
- JWT Bearer token support (via `setToken()` method)
- Token passed in all authorized requests
- Auto-loaded from SharedPreferences (ready for implementation)

### Error Handling
- Try-catch blocks on all API calls
- User-friendly error messages
- SnackBar notifications
- Retry mechanisms on failure

## UI/UX Features

### Theme
- Material Design 3
- Deep Purple primary color
- Responsive layout
- Consistent spacing and padding

### Navigation
- Stack-based navigation
- Pop with return values for refresh logic
- Back buttons on all screens
- Bottom navigation ready (for future phases)

### Feedback
- Loading spinners on processing
- SnackBar notifications for success/error
- Disabled buttons during loading
- Visual feedback for recording state

## Dependencies Added

```yaml
record: ^5.0.0           # Audio recording
intl: ^0.19.0            # Date/time formatting
shared_preferences: ^2.2.0  # Local storage (JWT)
provider: ^6.1.0         # State management (ready)
uuid: ^4.0.0             # Unique ID generation (ready)
```

## Usage Flow

### 1. Create New Patient
```
Patient List → [Add Button] → Patient Form →
[Fill Details] → [Create] → Success → Back to List
```

### 2. Create Voice Prescription
```
Patient Detail → [Voice Button] → Voice Prescription Screen →
[Record] → [Transcribe] → Validation Results →
Success/Errors Displayed
```

### 3. Create Text Prescription
```
Patient Detail → [Text Button] → Text Prescription Screen →
[Enter Text] → [Validate] → Validation Results →
Success/Errors Displayed
```

### 4. Edit Patient
```
Patient Detail → [Edit] → Patient Form →
[Update Fields] → [Save] → Success → Back to Detail
```

## State Management

### Current Implementation
- StatefulWidgets for local state
- FutureBuilder for async operations
- setState() for simple updates

### Future Enhancement
- Provider for global state
- BLoC pattern for complex flows
- Shared user session management

## Error Handling

### API Errors
- Network connectivity errors
- 400: Bad request (validation errors)
- 401: Unauthorized (missing/invalid token)
- 404: Not found (patient doesn't exist)
- 500: Server error

### User Feedback
- Descriptive error messages
- Retry buttons on failure
- Validation messages before submission
- Loading states during processing

## Permissions Required

### Android
- `RECORD_AUDIO` - For voice recording
- `INTERNET` - For API calls
- `READ_EXTERNAL_STORAGE` - For file access

### iOS
- `NSMicrophoneUsageDescription` - For voice recording
- `NSLocalNetworkUsageDescription` - For local API access

## Testing Checklist

- [ ] Create patient with all fields
- [ ] Create patient with minimal fields
- [ ] Edit patient information
- [ ] List patients
- [ ] View patient details
- [ ] Record voice prescription
- [ ] Enter text prescription
- [ ] View validation results (valid)
- [ ] View validation results (invalid)
- [ ] Handle API errors gracefully
- [ ] Test on iOS device
- [ ] Test on Android device
- [ ] Test on web platform
- [ ] Test offline behavior
- [ ] Test with slow network

## Build & Run

### Development
```bash
cd frontend
flutter pub get
flutter run
```

### Web
```bash
flutter run -d chrome
# Or specify API URL
flutter run -d chrome --dart-define=API_URL=http://192.168.1.100:8080
```

### iOS
```bash
flutter run -d iPhone
```

### Android
```bash
flutter run -d Android
```

### Build for Release
```bash
# Web
flutter build web --dart-define=API_URL=https://api.example.com --release

# iOS
flutter build ios --release

# Android
flutter build apk --release
```

## Configuration

### Backend URL
Default: `http://127.0.0.1:8080`

Override via environment:
```bash
flutter run --dart-define=API_URL=http://192.168.1.100:8080
```

### API Timeout
Default: 30 seconds (standard http package)

## Security Considerations

- JWT tokens stored in SharedPreferences (upgrade to secure storage for production)
- HTTPS enforcement for production (update API_URL)
- Input validation on client side
- No sensitive data in logs
- API error messages sanitized

## Performance Optimization

- FutureBuilder lazy loading
- ListView with itemBuilder (not full list in memory)
- Async/await for non-blocking API calls
- Image caching ready (for future features)

## Accessibility

- Semantic labels on buttons
- Readable font sizes
- High contrast colors
- Touch target sizes (48x48 minimum)

## Localization

- All UI text in French (can be extracted for i18n)
- Date formatting via intl package
- RTL support ready

## Future Enhancements

1. **Authentication Screen**
   - Login with email/password
   - JWT token storage and refresh
   - Session management

2. **Offline Support**
   - Local SQLite database
   - Offline queue management
   - Auto-sync on reconnection

3. **Advanced Search**
   - Patient search by name
   - Filter by condition/allergy
   - Sort by date/name

4. **Prescription History**
   - View past prescriptions
   - Prescription tracking
   - PDF export

5. **Notifications**
   - Push notifications for validations
   - Appointment reminders
   - System notifications

6. **Analytics**
   - Prescription statistics
   - Patient management metrics
   - Performance analytics

7. **Internationalization**
   - Multi-language support
   - Regional settings
   - Currency/unit preferences

## Troubleshooting

### Issue: API Connection Error
**Solution**:
- Check backend is running on correct port
- Verify API_URL environment variable
- Check network connectivity

### Issue: Audio Recording Fails
**Solution**:
- Grant microphone permission
- Check device has recording capability
- Verify storage space available

### Issue: Validation Fails with 401
**Solution**:
- Set JWT token via `apiService.setToken(token)`
- Check token is valid and not expired
- Verify user has correct permissions

## Support

For issues or feature requests, contact the development team.

---

**Frontend Status**: ✅ COMPLETE & READY FOR TESTING
**Last Updated**: 2026-02-25
