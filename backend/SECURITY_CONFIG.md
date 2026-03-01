# Security Configuration Guide

This document explains critical security configurations for the Vocalis backend.

## CORS Configuration

### Issue Fixed
The original CORS configuration allowed **all origins** (`allow_origins=["*"]`), which is a security risk:
- Opens door to CSRF attacks
- Allows any website to make requests to your API
- Not suitable for production environments

### Solution Implemented

CORS origins are now configurable via the `CORS_ORIGINS` environment variable:

**Environment Variable Format:**
```bash
# Single origin
CORS_ORIGINS=http://localhost:3000

# Multiple origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://app.example.com
```

**Default Behavior (if `CORS_ORIGINS` not set):**
```
Development defaults to:
- http://localhost:3000
- http://localhost:8080
- http://127.0.0.1:3000
- http://127.0.0.1:8080
- http://localhost:5900 (Flutter web)
- http://127.0.0.1:5900 (Flutter web)
```

### Configuration Examples

#### Local Development
```bash
# .env file
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### Production (Single Domain)
```bash
# Must use HTTPS in production
CORS_ORIGINS=https://app.example.com
```

#### Production (Multiple Domains)
```bash
# Web app, admin panel, mobile API gateway
CORS_ORIGINS=https://app.example.com,https://admin.example.com,https://api.example.com
```

### CORS Methods & Headers (Restricted)

Previously: `allow_methods=["*"]`, `allow_headers=["*"]`
Now: Explicit whitelist

**Allowed HTTP Methods:**
- GET
- POST
- PUT
- DELETE
- OPTIONS (for preflight)

**Allowed Request Headers:**
- Content-Type
- Authorization

**Exposed Response Headers:**
- Content-Length

**Preflight Caching:** 3600 seconds (1 hour)

### Credentials
- `allow_credentials=True` - Allows cookies/auth headers in cross-origin requests
- Only safe because origins are restricted

---

## JWT Secret Configuration

### Issue
Default secret is visible in code:
```python
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
```

### Solution Implemented

**Environment-based validation** with startup checks:

1. **Development mode** (default)
   - Uses default secret if JWT_SECRET not set
   - Logs warning about insecure configuration
   - Allows development without setup

2. **Production mode** (ENVIRONMENT=production)
   - **REQUIRES** JWT_SECRET environment variable
   - Fails at startup if not set
   - Prevents accidental deployment with weak secret

### Configuration

**Set environment:**
```bash
# Development (default)
export ENVIRONMENT=development

# Production (requires JWT_SECRET)
export ENVIRONMENT=production
```

**Generate a secure secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output:**
```
dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY=
```

**Set JWT secret in development:**
```bash
export JWT_SECRET="dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY="
python main.py
```

**Set JWT secret in production:**
```bash
export ENVIRONMENT=production
export JWT_SECRET="dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY="
python main.py
```

**In Docker:**
```dockerfile
# Build
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Run with secrets (from compose or env)
CMD ["python", "main.py"]
```

**Docker Compose example:**
```yaml
services:
  vocalis-backend:
    image: vocalis:latest
    environment:
      ENVIRONMENT: production
      JWT_SECRET: ${JWT_SECRET}  # From .env or host
      CORS_ORIGINS: https://app.example.com
      DATABASE_URL: postgresql://...
    ports:
      - "8080:8080"
```

### Startup Validation

The system validates JWT configuration on startup:

**Development mode (logs warning):**
```
WARNING:vocalis-backend:Using default JWT secret (development mode).
This is INSECURE for production. Set JWT_SECRET environment variable for production deployments.
```

**Production mode with missing secret (FAILS):**
```
CRITICAL:vocalis-backend:SECURITY ERROR: JWT_SECRET environment variable not set in production!
This uses an insecure default secret that is visible in code.
Generate a secure secret and set the JWT_SECRET environment variable.

Traceback:
  ValueError: SECURITY ERROR: JWT_SECRET environment variable not set in production!
```

**Production mode with secret set (SUCCESS):**
```
INFO:vocalis-backend:JWT secret configured from environment variable (secure)
```

### Key Features

✅ **Automatic validation at startup**
- Checks environment (development/production)
- Validates secret strength
- Fails fast on misconfiguration

✅ **Prevents accidental insecurity**
- Production deployment without secret fails
- No silent failures
- Clear error messages

✅ **Development-friendly**
- No secret required for local testing
- Warnings to remind about production setup

✅ **Environment-aware**
- Different behavior based on ENVIRONMENT variable
- Easy multi-environment deployment
- Clear separation of concerns

---

## Database Configuration

### Development (SQLite)
```bash
DATABASE_URL=sqlite:///./vocalis.db
```

### Production (PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@host:5432/vocalis
```

**Security notes:**
- Use strong passwords
- Don't commit .env file to git
- Use environment-specific connection strings
- Enable SSL for remote PostgreSQL connections

---

## Ollama Configuration

### Base URL
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

**Security considerations:**
- Only expose on localhost in development
- Use firewall rules to restrict access in production
- Consider authentication/reverse proxy for remote Ollama

### Model
```bash
OLLAMA_MODEL=mistral
```

### Timeout
```bash
OLLAMA_TIMEOUT=120  # seconds
```

---

## Environment Variables Checklist

### Development
- [ ] `DATABASE_URL` - Set to SQLite or local PostgreSQL
- [ ] `JWT_SECRET` - Can use default for development
- [ ] `CORS_ORIGINS` - Set to localhost origins
- [ ] `OLLAMA_BASE_URL` - Set to local Ollama
- [ ] `OLLAMA_MODEL` - Mistral or desired model

### Production
- [ ] `DATABASE_URL` - Production PostgreSQL with strong password
- [ ] `JWT_SECRET` - Generated secret key (required!)
- [ ] `CORS_ORIGINS` - HTTPS origins only (required!)
- [ ] `OLLAMA_BASE_URL` - Secure Ollama endpoint
- [ ] `OLLAMA_MODEL` - Verified model name
- [ ] All `.env` values set - No defaults used

---

## Security Best Practices

### 1. Environment Variables
```bash
# DON'T commit .env files
echo ".env" >> .gitignore

# DO use .env.example with defaults
cp .env.example .env

# DO set real values in production
export JWT_SECRET="..."
export CORS_ORIGINS="..."
```

### 2. CORS Headers Validation
The API logs CORS configuration on startup:
```
CORS origins from environment: ['https://app.example.com']
CORS middleware configured with 1 allowed origin(s)
```

Verify this matches your expected origins!

### 3. HTTPS in Production
CORS only protects from browser-based attacks. Always:
- [ ] Use HTTPS (TLS/SSL)
- [ ] Use security headers (HSTS, CSP, etc.)
- [ ] Validate JWT tokens
- [ ] Use rate limiting

### 4. Docker Deployment
```dockerfile
# Don't set secrets in Dockerfile
# ARG JWT_SECRET  # ❌ Wrong - visible in layers

# Use environment variables at runtime
# docker run -e JWT_SECRET="..." -e CORS_ORIGINS="..." vocalis:latest
```

---

## Testing CORS Configuration

### Test Allowed Origin
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8080/api/prescriptions
```

Expected response includes:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Test Blocked Origin
```bash
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8080/api/prescriptions
```

Expected: No `Access-Control-Allow-Origin` header

---

---

## Rate Limiting Configuration

Rate limiting protects the API from brute force attacks, API abuse, and DoS attacks.

### Default Rate Limits

**Authentication (Strict):**
- Login: 5 attempts/minute per IP
- Register: 3 attempts/minute per IP

**Chat & LLM (Moderate):**
- Chat: 20 messages/minute per IP
- PDF Generation: 10/minute per user
- Voice Transcription: 10/minute per user

**Data Operations (Standard):**
- Create: 100/minute per IP
- Read: 300/minute per IP
- Update: 100/minute per IP
- Delete: 50/minute per IP

### When Rate Limited

**Response Status:** 429 Too Many Requests

**Response Body:**
```json
{
  "status": "error",
  "detail": "Too many requests. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

**Response Headers:**
```
Retry-After: 23
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000023
```

### Production Configuration

For distributed deployments with multiple workers, use Redis:

```bash
export REDIS_URL=redis://localhost:6379
```

In Docker:
```dockerfile
ENV REDIS_URL=redis://redis:6379
```

See `RATE_LIMITING.md` for complete configuration guide.

---

## Monitoring

### Log Output on Startup
```
INFO:vocalis-backend:CORS origins from environment: ['https://app.example.com']
INFO:vocalis-backend:CORS middleware configured with 1 allowed origin(s)
```

### What to Monitor
1. **CORS rejected requests** - Check for unexpected origins
2. **JWT errors** - May indicate token tampering
3. **Failed requests** - Track 403 errors (forbidden)
4. **Rate limit violations** - Check for brute force attempts or API abuse

---

## Related Security Fixes (Planned)

See `CLAUDE.md` and `CODE_REVIEW.md` for:
- [ ] Rate limiting (prevent brute force)
- [ ] JWT refresh tokens
- [ ] Token blacklist/revocation
- [ ] Request correlation IDs
- [ ] SQL injection prevention (via Pydantic)
