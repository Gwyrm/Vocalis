# Quick Start Guide

Get up and running with Vocalis in 5 minutes!

## Prerequisites

- Backend running at `http://localhost:8080`
- Frontend accessible at `http://localhost:59000` (Flutter web)
- Demo credentials ready

## Step 1: Start Backend (1 minute)

```bash
cd Vocalis/backend
source venv/bin/activate
python main.py
```

Wait for:
```
INFO:     Application startup complete.
```

## Step 2: Start Frontend (1 minute)

```bash
cd Vocalis/frontend
flutter run -d chrome
```

Browser opens automatically to the login screen.

## Step 3: Login as Doctor (30 seconds)

**Email:** `doctor@hopital-demo.fr`
**Password:** `demo123`

Click "Connexion" (Login)

## Step 4: Select a Patient (30 seconds)

From the patient list, click on any patient (e.g., "Jean Dupont")

## Step 5: Create a Prescription (2 minutes)

### Via Text Input:
1. Click "Créer une ordonnance" (Create prescription)
2. Select "Texte" (Text)
3. Enter prescription:
   ```
   Amoxicilline 500mg, trois fois par jour pendant 10 jours
   ```
4. Click "Valider" (Validate)

### Via Voice Input:
1. Click "Voix" (Voice)
2. Click record button
3. Speak: "Amoxicilline 500mg, trois fois par jour pendant 10 jours"
4. Click stop, wait for transcription
5. Click "Transcrire et valider" (Transcribe and validate)

## Step 6: Confirm Prescription (30 seconds)

1. Review extracted prescription:
   - Medication: ✅ Amoxicilline
   - Dosage: ✅ 500mg
   - Duration: ✅ 10 jours

2. Click "Confirmer" (Confirm)

3. See success message: "Ordonnance confirmée"

## Step 7: View History (30 seconds)

1. Patient page shows prescription in history
2. Click on prescription to view details

## 🎉 You've Created Your First Prescription!

### What Happened:

```
┌─────────────────────────────┐
│  Natural Language Input     │
│ "Amoxicilline 500mg, ..."   │
└──────────────┬──────────────┘
               │
               ▼
       ┌──────────────────┐
       │ AI Extraction    │
       │ (LLM Parsing)    │
       └────────┬─────────┘
                │
               ▼
        ┌──────────────────┐
        │ Data Validation  │
        │ - Format check   │
        │ - Allergy check  │
        └────────┬─────────┘
                 │
                ▼
        ┌──────────────────┐
        │ Doctor Confirm   │
        └────────┬─────────┘
                 │
                ▼
        ┌──────────────────┐
        │ Saved & Signed   │
        └──────────────────┘
```

## Explore More Features

### As a Doctor:
- ✅ Create multiple prescriptions
- ✅ Confirm prescriptions (simple button)
- ✅ View patient medication history
- ✅ Manage patient information
- ✅ Logout and re-login

### As a Nurse:
1. Logout (click profile menu)
2. Login as:
   **Email:** `nurse@hopital-demo.fr`
   **Password:** `demo123`

3. You can:
   - ✅ Create prescriptions
   - ✅ View patient history
   - ❌ Cannot confirm (doctor only)

## Common Commands

```bash
# Restart backend
pkill -f "python main.py"
cd backend && python main.py

# Restart frontend
flutter clean
flutter pub get
flutter run -d chrome

# Check health
curl http://localhost:8080/api/health | jq .

# Test API directly
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hopital-demo.fr","password":"demo123"}' | jq .
```

## Next Steps

- 📖 Learn about [Text Prescriptions](../features/text-prescriptions.md)
- 📖 Learn about [Voice Prescriptions](../features/voice-prescriptions.md)
- 📚 Read [API Documentation](../architecture/api.md)
- 🧪 Check [Testing Guide](../testing/backend.md)

## Troubleshooting

**Login fails?**
- Backend not running → Start it with `python main.py`
- Wrong credentials → Use demo123
- Port 8080 in use → Kill old process

**Prescription not saving?**
- Check browser console for errors (F12)
- Verify backend is running
- Check backend logs

**Voice not working?**
- Backend must be running with Ollama
- Microphone permissions granted
- Check browser console (F12)

---

**Congratulations!** You're now ready to explore Vocalis. 🚀
