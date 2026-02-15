# Vocalis Backend API - Test Examples

This document provides curl examples for testing all backend API endpoints.

## Prerequisites

```bash
# Make sure backend is running
cd backend
python main.py
# Server will start on http://localhost:8080
```

## Health Check

### Test if backend is running

```bash
curl -X GET http://localhost:8080/api/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "backend": "running",
  "model_loaded": true,
  "model_path": "/path/to/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
}
```

---

## Chat Endpoint

### Simple chat request

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour, j'\''ai besoin d'\''une ordonnance"}'
```

**Expected Response:**
```json
{
  "response": "Bonjour! Je suis là pour vous aider à rédiger une ordonnance..."
}
```

---

## Collect Prescription Info Endpoint

### Example 1: Initial request with patient name

```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {
      "patientName": null,
      "patientAge": null,
      "diagnosis": null,
      "medication": null,
      "dosage": null,
      "duration": null,
      "specialInstructions": null
    },
    "userInput": "Le patient s'\''appelle Jean Dupont"
  }'
```

**Expected Response:**
```json
{
  "status": "needs_more_info",
  "missingFields": [
    "Âge/Date de naissance",
    "Diagnostic",
    "Médicament",
    "Posologie",
    "Durée du traitement",
    "Instructions spéciales"
  ],
  "message": "Merci! J'\''ai noté que le patient s'\''appelle Jean Dupont. Quel est son âge ou sa date de naissance?",
  "collectedData": {
    "patientName": "Jean Dupont",
    "patientAge": null,
    "diagnosis": null,
    "medication": null,
    "dosage": null,
    "duration": null,
    "specialInstructions": null
  }
}
```

### Example 2: Add patient age

```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {
      "patientName": "Jean Dupont",
      "patientAge": null,
      "diagnosis": null,
      "medication": null,
      "dosage": null,
      "duration": null,
      "specialInstructions": null
    },
    "userInput": "Il a 45 ans"
  }'
```

**Expected Response:**
```json
{
  "status": "needs_more_info",
  "missingFields": [
    "Diagnostic",
    "Médicament",
    "Posologie",
    "Durée du traitement",
    "Instructions spéciales"
  ],
  "message": "Bien! Le patient a 45 ans. Quel est le diagnostic?",
  "collectedData": {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans",
    "diagnosis": null,
    "medication": null,
    "dosage": null,
    "duration": null,
    "specialInstructions": null
  }
}
```

### Example 3: Multiple fields in one message

```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {
      "patientName": "Jean Dupont",
      "patientAge": "45 ans",
      "diagnosis": null,
      "medication": null,
      "dosage": null,
      "duration": null,
      "specialInstructions": null
    },
    "userInput": "Il a une hypertension artérielle. Prescrire du Lisinopril 10mg, une fois par jour, pour 3 mois"
  }'
```

**Expected Response:**
```json
{
  "status": "needs_more_info",
  "missingFields": [
    "Instructions spéciales"
  ],
  "message": "Excellent! J'\''ai noté l'\''hypertension, le Lisinopril 10mg une fois par jour pour 3 mois. Y a-t-il des instructions spéciales?",
  "collectedData": {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans",
    "diagnosis": "Hypertension artérielle",
    "medication": "Lisinopril",
    "dosage": "10mg, une fois par jour",
    "duration": "3 mois",
    "specialInstructions": null
  }
}
```

### Example 4: Complete prescription

```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {
      "patientName": "Jean Dupont",
      "patientAge": "45 ans",
      "diagnosis": "Hypertension artérielle",
      "medication": "Lisinopril",
      "dosage": "10mg, une fois par jour",
      "duration": "3 mois",
      "specialInstructions": null
    },
    "userInput": "À prendre le matin à jeun"
  }'
```

**Expected Response:**
```json
{
  "status": "complete",
  "missingFields": [],
  "message": "Parfait! Toutes les informations ont été collectées. La prescription est prête à être générée.",
  "collectedData": {
    "patientName": "Jean Dupont",
    "patientAge": "45 ans",
    "diagnosis": "Hypertension artérielle",
    "medication": "Lisinopril",
    "dosage": "10mg, une fois par jour",
    "duration": "3 mois",
    "specialInstructions": "À prendre le matin à jeun"
  }
}
```

---

## Generate Prescription Endpoint

### Generate professional prescription from complete data

```bash
curl -X POST http://localhost:8080/api/generate-prescription \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "patientName": "Jean Dupont",
      "patientAge": "45 ans",
      "diagnosis": "Hypertension artérielle",
      "medication": "Lisinopril",
      "dosage": "10mg, une fois par jour",
      "duration": "3 mois",
      "specialInstructions": "À prendre le matin à jeun"
    }
  }'
```

**Expected Response:**
```json
{
  "prescription": "ORDONNANCE MÉDICALE\n\nPatient: Jean Dupont\nÂge: 45 ans\n\nDiagnostic: Hypertension artérielle\n\nMÉDICAMENT:\nLisinopril\n\nPOSOLOGIE:\n10mg, une fois par jour\n\nDURÉE:\n3 mois\n\nINSTRUCTIONS SPÉCIALES:\nÀ prendre le matin à jeun\n\nSigné le: [Date]\nMédecin: [Signature]"
}
```

### Error: Incomplete data

```bash
curl -X POST http://localhost:8080/api/generate-prescription \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "patientName": "Jean Dupont",
      "patientAge": "45 ans",
      "diagnosis": null,
      "medication": null,
      "dosage": null,
      "duration": null,
      "specialInstructions": null
    }
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": "Donnees incomples. Manquant: Diagnostic, Médicament, Posologie, Durée du traitement, Instructions spéciales"
}
```

---

## Generate PDF Endpoint

### Generate PDF with prescription and signature

First, you'll need a base64-encoded signature. Here's an example with a simple placeholder:

```bash
curl -X POST http://localhost:8080/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "content": "ORDONNANCE MÉDICALE\n\nPatient: Jean Dupont\nÂge: 45 ans\n\nDiagnostic: Hypertension artérielle\n\nMÉDICAMENT:\nLisinopril\n\nPOSOLOGIE:\n10mg, une fois par jour\n\nDURÉE:\n3 mois",
    "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
  }'
```

**Expected Response:**
- Binary PDF file (application/pdf)
- Will contain the prescription content with signature

---

## Error Scenarios

### Missing Required Field

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required"
    }
  ]
}
```

### Model Not Loaded

If the model fails to load, endpoints will return:

```json
{
  "detail": "Le modele n'est pas encore charge. Veuillez patienter."
}
```

**HTTP Status Code:** 503 Service Unavailable

---

## Complete Workflow Example

Here's a complete example showing the full prescription workflow:

### Step 1: Collect patient name
```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{"currentData": {}, "userInput": "Patient: Marie Curie"}'
```

### Step 2: Collect age
```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{"currentData": {"patientName": "Marie Curie"}, "userInput": "35 ans"}'
```

### Step 3: Collect diagnosis and medication
```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{"currentData": {"patientName": "Marie Curie", "patientAge": "35 ans"}, "userInput": "Diabète type 2. Prescrire Metformine 500mg"}'
```

### Step 4: Collect remaining info
```bash
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{"currentData": {"patientName": "Marie Curie", "patientAge": "35 ans", "diagnosis": "Diabète type 2", "medication": "Metformine", "dosage": "500mg"}, "userInput": "Deux fois par jour, 6 mois, avec les repas"}'
```

### Step 5: Generate prescription
```bash
curl -X POST http://localhost:8080/api/generate-prescription \
  -H "Content-Type: application/json" \
  -d '{"data": {"patientName": "Marie Curie", "patientAge": "35 ans", "diagnosis": "Diabète type 2", "medication": "Metformine", "dosage": "500mg, deux fois par jour", "duration": "6 mois", "specialInstructions": "Avec les repas"}}'
```

### Step 6: Generate PDF (with signature)
```bash
curl -X POST http://localhost:8080/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"content": "[prescription content from step 5]", "signature_base64": "[base64 signature]"}' \
  -o prescription.pdf
```

---

## Tips for Testing

1. **Use jq for pretty JSON output:**
   ```bash
   curl ... | jq .
   ```

2. **Save response to file:**
   ```bash
   curl -X POST ... -o response.json
   ```

3. **Test with Postman/Insomnia:**
   - Import these examples into your REST client
   - Create environment variables for base URL

4. **Monitor logs:**
   ```bash
   # In another terminal
   tail -f backend.log
   ```

5. **Test with different data:**
   - Try special characters (accents, symbols)
   - Try very long descriptions
   - Try different languages

---

## API Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Prescription generated |
| 400 | Bad Request | Incomplete data |
| 422 | Validation Error | Missing required field |
| 503 | Service Unavailable | Model not loaded |
| 500 | Server Error | Unexpected exception |

---

Generated: 2026-02-15
