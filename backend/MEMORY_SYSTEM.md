# Vocalis Backend - Memory & Data Collection System

## How It Works

The backend now properly extracts and remembers patient information throughout the conversation.

### Flow Diagram

```
User Message
    ↓
Backend extracts information via LLM
    ↓
Stores extracted data in session memory
    ↓
Checks what information is missing
    ↓
Confirms with user and asks for missing info
    ↓
Repeats until all required fields are collected
```

### Detailed Process

#### 1. User Sends Message
```
User: "Je m'appelle Jean Dupont, 45 ans"
```

#### 2. Backend Extraction (extract_prescription_data_from_message)
The LLM analyzes the message and extracts structured data:
- Uses lower temperature (0.1) for consistency
- Expects JSON output
- Handles markdown code blocks
- Validates extracted values

```python
extracted = {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans"
}
```

#### 3. Memory Storage
Extracted data is stored in the session's `PrescriptionData` object:
```python
current_data.patientName = "Jean Dupont"
current_data.patientAge = "45 ans"
```

#### 4. Validation
Check what information is missing:
```python
missing = current_data.get_missing_required_fields()
# Returns: ["Diagnostic", "Médicament", "Posologie", ...]
```

#### 5. AI Response
The backend builds a prompt that includes:
- What was collected so far
- What's still missing
- The latest user input

The LLM responds naturally:
```
Backend: "Merci! J'ai noté que vous vous appelez Jean Dupont, 45 ans.
Pouvez-vous me dire quel est votre diagnostic?"
```

#### 6. Next Iteration
User responds with more info, and the cycle repeats.

---

## Required Fields

The system collects these 7 fields:

| Field | Example | Status |
|-------|---------|--------|
| patientName | Jean Dupont | Required |
| patientAge | 45 ans | Required |
| diagnosis | Hypertension | Required |
| medication | Lisinopril | Required |
| dosage | 10mg, 1x/jour | Required |
| duration | 3 mois | Required |
| specialInstructions | Matin à jeun | Required |

---

## API Endpoints

### POST /api/collect-prescription-info

**Request:**
```json
{
  "currentData": {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans",
    "diagnosis": null,
    "medication": null,
    "dosage": null,
    "duration": null,
    "specialInstructions": null
  },
  "userInput": "J'ai une hypertension artérielle"
}
```

**Response:**
```json
{
  "status": "needs_more_info",
  "missingFields": [
    "Médicament",
    "Posologie",
    "Durée du traitement",
    "Instructions spéciales"
  ],
  "message": "Je comprends que vous avez une hypertension. Quel médicament prescrivez-vous?",
  "collectedData": {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans",
    "diagnosis": "Hypertension artérielle",
    "medication": null,
    "dosage": null,
    "duration": null,
    "specialInstructions": null
  }
}
```

---

## Key Improvements

### 1. Better Extraction Prompt
```
"Tu es un assistant medical. Extrait UNIQUEMENT les informations
medicales du message et retourne JSON."
```

- More direct and simple
- Clear expectation (JSON only)
- Lower temperature for consistency

### 2. Memory Persistence
Each request includes `currentData` which contains all previously collected info:
- Nothing is lost
- LLM sees the full context
- User can provide info in any order

### 3. Validation Loop
After extraction, the system:
1. Checks completeness
2. Identifies missing fields
3. Builds a prompt that includes missing fields
4. LLM naturally asks for what's missing

### 4. Flexible Input
Users can provide info in multiple ways:
```
"Jean Dupont, 45 ans, hypertension"          ✓
"Je m'appelle Jean, j'ai 45 ans"             ✓
"Patient: Jean Dupont\nAge: 45 ans"          ✓
"Jean Dupont 45 hypertension"                ✓
```

All formats are understood by the LLM.

---

## Testing

### Run Extraction Tests
```bash
cd backend
source venv/bin/activate
python test_extraction.py
```

This will test:
- Name and age extraction
- Diagnosis and medication extraction
- Dosage and duration extraction
- Complete data extraction
- Missing fields validation
- Prompt building

### Run Full Tests
```bash
pytest test_main.py test_advanced.py -v
```

---

## Debugging

### Check Extraction Logs
```bash
cd backend
PYTHONUNBUFFERED=1 python main.py 2>&1 | grep -i "extract"
```

### Test Extraction Manually
```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {},
    "userInput": "Je mappelle Jean Dupont et j'ai 45 ans"
  }' | jq .
```

### Check Missing Fields
The response will show:
```json
{
  "status": "needs_more_info",
  "missingFields": [
    "Diagnostic",
    "Médicament",
    "Posologie",
    "Durée du traitement",
    "Instructions spéciales"
  ]
}
```

---

## How Frontend Uses This

The Flutter app (chat_screen.dart):

1. **Sends message** to `/api/collect-prescription-info`
2. **Receives response** with updated data
3. **Stores data** in `_prescriptionData`
4. **Updates UI** with AI response
5. **Shows progress** when all fields collected

```dart
final response = await _apiService.collectPrescriptionInfo(
  _prescriptionData,  // Current state
  message,            // New user input
);

// Update stored data
_prescriptionData = PrescriptionData.fromJson(response['collectedData']);

// Display AI response
_messages.add({'role': 'assistant', 'content': response['message']});

// Check if complete
if (response['status'] == 'complete') {
  // Show generate prescription button
}
```

---

## Complete Workflow Example

### Message 1
```
User: "Je m'appelle Jean Dupont, 45 ans"
Backend extracts: {patientName, patientAge}
Backend responds: "Merci Jean! Quel est votre diagnostic?"
```

### Message 2
```
User: "Hypertension artérielle"
Backend extracts: {diagnosis}
Backend responds: "Quel médicament?"
```

### Message 3
```
User: "Lisinopril, 10mg une fois par jour"
Backend extracts: {medication, dosage}
Backend responds: "Pour combien de temps?"
```

### Message 4
```
User: "3 mois"
Backend extracts: {duration}
Backend responds: "Y a-t-il des instructions spéciales?"
```

### Message 5
```
User: "À prendre le matin à jeun"
Backend extracts: {specialInstructions}
Backend status: COMPLETE
Backend responds: "Toutes les informations sont collectées!"
```

### Then:
```
User clicks "Generate Prescription"
→ /api/generate-prescription
→ AI generates professional prescription
→ User can edit and sign
→ PDF is generated
```

---

Generated: 2026-02-15
