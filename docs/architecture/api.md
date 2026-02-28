# API Overview

Vocalis provides a REST API for all client operations.

## Base URL

```
http://localhost:8080
```

## Authentication

All endpoints (except `/api/auth/login`) require JWT Bearer token:

```
Authorization: Bearer <token>
```

## Response Format

All responses are JSON:

```json
{
  "data": {...},
  "error": null,
  "status": "success"
}
```

## Main Endpoint Categories

### Authentication (`/api/auth`)
- `POST /login` - Get JWT token
- `GET /me` - Current user info

### Patients (`/api/patients`)
- `GET /` - List all patients
- `GET /{id}` - Get patient details
- `GET /{id}/prescriptions` - Get prescription history
- `PUT /{id}` - Update patient info

### Prescriptions (`/api/prescriptions`)
- `POST /text` - Create from text
- `POST /voice` - Create from audio
- `PUT /{id}/sign` - Confirm prescription
- `GET /{id}` - Get prescription details

### Users (`/api/users`)
- `PUT /profile` - Update profile
- `POST /change-password` - Change password

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Successful request |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable - Validation failed |
| 500 | Server Error - Internal error |

## Rate Limiting

Currently no rate limiting. Future versions will implement:
- 100 requests per minute per user
- 1000 requests per minute per API key

## Pagination

List endpoints support pagination:

```
GET /api/patients?page=1&limit=10
```

---

**See detailed endpoints:**
- [Authentication](../api/authentication.md)
- [Patients](../api/patients.md)
- [Prescriptions](../api/prescriptions.md)
- [Users](../api/users.md)
