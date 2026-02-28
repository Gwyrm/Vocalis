# Authentication API

## POST /api/auth/login

Login with email and password to get JWT token.

**Request:**
```json
{
  "email": "doctor@hopital-demo.fr",
  "password": "demo123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "doctor@hopital-demo.fr",
    "role": "doctor",
    "org_id": "uuid"
  }
}
```

**Error (401):**
```json
{"detail": "Invalid email or password"}
```

---

## GET /api/auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "doctor@hopital-demo.fr",
  "full_name": "Dr. Marie Dubois",
  "role": "doctor",
  "org_id": "uuid"
}
```

**Error (401):**
```json
{"detail": "Invalid or expired token"}
```
