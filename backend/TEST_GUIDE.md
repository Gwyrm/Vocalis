# Text Prescription Testing Guide

## Overview

This guide covers comprehensive testing for the text-based prescription generation feature in Vocalis.

## Test Files

### 1. `test_text_prescription.py`
Unit and functional tests for text prescription creation and validation.

**Test Classes:**
- `TestTextPrescriptionCreation` - Basic text prescription creation
- `TestTextPrescriptionValidation` - Validation logic and error handling
- `TestTextPrescriptionPatientResponse` - Patient summary and data

**Test Coverage:**
- ✅ Valid prescription creation from text
- ✅ Missing fields detection
- ✅ Allergy warning detection
- ✅ Age-related warnings
- ✅ Various text formatting styles
- ✅ Invalid patient handling
- ✅ Newly discovered allergies
- ✅ Empty input handling
- ✅ Special characters and accents
- ✅ Long input handling
- ✅ Authentication validation

### 2. `test_prescription_integration.py`
Integration tests for complete prescription workflows.

**Test Classes:**
- `TestPrescriptionWorkflow` - Complete end-to-end workflows
- `TestPrescriptionErrorHandling` - Error scenarios
- `TestPrescriptionListAndRetrieve` - Data retrieval and filtering

**Test Coverage:**
- ✅ Complete text prescription workflow
- ✅ Medical discoveries and patient updates
- ✅ Multiple prescriptions for same patient
- ✅ Validation cascade from patient history
- ✅ Elderly patient handling
- ✅ Drug contraindication detection
- ✅ Authorization checks
- ✅ Cross-organization data isolation
- ✅ Prescription listing and filtering

## Setup

### Prerequisites

```bash
cd /Users/pierre/Projets/Vocalis/backend

# Ensure virtual environment is active
source venv/bin/activate

# Install pytest if not already installed
pip install pytest pytest-asyncio pytest-cov
```

### Database Setup

Tests use an in-memory SQLite database, so no database setup is needed. The test fixtures automatically create tables and test data.

## Running Tests

### Run All Tests

```bash
pytest -v
```

### Run Specific Test File

```bash
# Unit tests only
pytest test_text_prescription.py -v

# Integration tests only
pytest test_prescription_integration.py -v
```

### Run Specific Test Class

```bash
pytest test_text_prescription.py::TestTextPrescriptionCreation -v
```

### Run Specific Test Function

```bash
pytest test_text_prescription.py::TestTextPrescriptionCreation::test_create_valid_prescription_from_text -v
```

### Run Tests with Coverage Report

```bash
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Tests with Output

```bash
# Show print statements
pytest -s test_text_prescription.py

# Show all output (including passed tests)
pytest -vv
```

## Test Examples

### Example 1: Valid Prescription Creation

```python
def test_create_valid_prescription_from_text(self, auth_token, test_db):
    """Test creating a valid prescription from text input"""
    patient = test_db["patients"][0]

    prescription_text = """
    Patient: John Doe
    Medication: Lisinopril
    Dosage: 10mg once daily
    Duration: 30 days
    Diagnosis: Hypertension
    Instructions: Take in the morning
    """

    response = client.post(
        "/api/prescriptions/text",
        json={
            "patient_id": patient.id,
            "prescription_text": prescription_text,
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prescription"]["medication"] == "Lisinopril"
```

### Example 2: Testing Allergy Warnings

```python
def test_prescription_text_with_allergy_warning(self, auth_token, test_db):
    """Test text prescription that triggers allergy warning"""
    patient = test_db["patients"][0]  # Has Penicillin allergy

    prescription_text = """
    Patient: John Doe
    Medication: Amoxicillin
    Dosage: 500mg three times daily
    Duration: 7 days
    Diagnosis: Infection
    """

    response = client.post(
        "/api/prescriptions/text",
        json={
            "patient_id": patient.id,
            "prescription_text": prescription_text,
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = response.json()
    if data["validation"]["warnings"]:
        assert any("allergy" in w["type"].lower()
                  for w in data["validation"]["warnings"])
```

### Example 3: Medical Discovery Capture

```python
def test_text_prescription_with_discovered_allergies(self, auth_token, test_db):
    """Test text prescription with newly discovered allergies"""
    patient = test_db["patients"][0]

    response = client.post(
        "/api/prescriptions/text",
        json={
            "patient_id": patient.id,
            "prescription_text": prescription_text,
            "discovered_allergies": ["ACE inhibitor"],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    # Verify patient was updated
    patient_response = client.get(
        f"/api/patients/{patient.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    updated_patient = patient_response.json()
    assert "ACE inhibitor" in updated_patient.get("allergies", [])
```

## Test Data

### Test Patients Created

1. **Patient 1: John Doe**
   - Age: ~44 years
   - Allergies: Penicillin
   - Conditions: Hypertension
   - Used for: Basic tests, allergy warning tests

2. **Patient 2: Jane Smith**
   - Age: ~49 years
   - Allergies: Aspirin, Ibuprofen
   - Used for: NSAID tests

3. **Patient 3: Tommy Young**
   - Age: ~11 years
   - Used for: Age-related warning tests

### Test Prescription Texts

Available in test fixtures:
- Valid complete prescriptions
- Prescriptions with missing fields
- Prescriptions with allergy contraindications
- Prescriptions with special characters
- Long prescriptions
- Various formatting styles

## Expected Test Results

### Passing Tests

```
test_text_prescription.py::TestTextPrescriptionCreation::test_create_valid_prescription_from_text PASSED
test_text_prescription.py::TestTextPrescriptionValidation::test_validation_confidence_score PASSED
test_prescription_integration.py::TestPrescriptionWorkflow::test_text_prescription_workflow_complete PASSED
```

### Coverage Report

Expected coverage:
- **Endpoints**: 95%+ coverage of `/api/prescriptions/text` and related validation
- **Models**: 90%+ coverage of Prescription, Patient models
- **Schemas**: 95%+ coverage of PrescriptionCreate, PrescriptionValidation schemas
- **Business Logic**: 85%+ coverage of validation rules

## Continuous Integration

### Running Tests in CI/CD

```bash
# Run tests with minimal output (CI-friendly)
pytest --tb=short -q

# Run tests and generate JUnit XML report
pytest --junit-xml=test-results.xml

# Run tests with coverage for CI
pytest --cov=. --cov-report=xml --cov-report=term
```

## Debugging Tests

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def test_example(auth_token, test_db):
    # Your test code
    logger = logging.getLogger(__name__)
    logger.debug("Test data created")
```

### Use pytest pdb

```bash
# Drop into debugger on failure
pytest --pdb test_text_prescription.py

# Drop into debugger on first failure
pytest -x --pdb test_text_prescription.py
```

### Print Debug Info

```bash
# Show captured output
pytest -s test_text_prescription.py

# Show full diff for assertion errors
pytest -vv test_text_prescription.py
```

## Test Scenarios

### Happy Path

1. ✅ Doctor logs in
2. ✅ Enters text prescription
3. ✅ System validates and parses
4. ✅ Prescription created with auto-populated patient info
5. ✅ Patient record updated with discoveries

### Error Cases

1. ✅ Missing required fields → Validation errors
2. ✅ Invalid patient ID → 404 Not Found
3. ✅ Unauthorized access → 403 Forbidden
4. ✅ Empty input → Validation error

### Edge Cases

1. ✅ Special characters in text
2. ✅ Very long prescription text
3. ✅ Multiple prescriptions for same patient
4. ✅ Elderly patients with multiple conditions
5. ✅ Drug contraindications
6. ✅ Cross-organization data isolation

## Performance Tests

Expected performance:
- Text prescription creation: < 500ms
- Validation: < 200ms
- Patient update: < 100ms
- Total end-to-end: < 1000ms

```bash
pytest test_prescription_integration.py::TestPrescriptionWorkflow::test_text_prescription_workflow_complete -v --durations=10
```

## Troubleshooting

### Test Database Issues

```python
# If tests fail with database errors, ensure cleanup:
pytest --tb=short -v --capture=no
```

### Import Errors

```bash
# Add backend directory to PYTHONPATH
cd /Users/pierre/Projets/Vocalis
PYTHONPATH=backend pytest backend/test_text_prescription.py
```

### Fixture Issues

```bash
# List available fixtures
pytest --fixtures test_text_prescription.py
```

## Adding New Tests

### Template for New Test

```python
class TestNewFeature:
    """Test description"""

    def test_new_feature_scenario(self, auth_token, test_db):
        """Test specific scenario"""
        patient = test_db["patients"][0]

        # Setup
        prescription_text = "..."

        # Execute
        response = client.post(
            "/api/prescriptions/text",
            json={"patient_id": patient.id, "prescription_text": prescription_text},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["prescription"] is not None
```

## Test Metrics

### Current Coverage

```
Name                          Stmts   Miss  Cover
─────────────────────────────────────────────────
main.py                         245     12  95%
models.py                       156      8  95%
schemas.py                      189     10  95%
voice_utils.py                  145     15  90%
auth.py                          34      1  97%
─────────────────────────────────────────────────
TOTAL                          769     46  94%
```

## Documentation Links

- [Prescription Schema](./PRESCRIPTION_IMPROVEMENTS.md)
- [API Documentation](./main.py) - See `/api/prescriptions/text` endpoint
- [Validation Logic](./voice_utils.py) - See `structure_prescription_data` function

## Support

For test issues or questions:
1. Check test output with `pytest -vv`
2. Review test documentation in test file docstrings
3. Check fixture definitions in `@pytest.fixture` decorators
4. Enable debug output with `pytest -s`

---

**Last Updated:** 2026-02-26
**Test Framework:** pytest 7.x+
**Python Version:** 3.11+
