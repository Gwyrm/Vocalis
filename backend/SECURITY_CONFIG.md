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

### Solution
Ensure `JWT_SECRET` environment variable is set in production.

**Generate a secure secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output:**
```
dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY=
```

**Set in production:**
```bash
export JWT_SECRET="dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY="
```

**In Docker:**
```dockerfile
ENV JWT_SECRET="dK_yZwQpL8nM3vXjF9qRsT2uWpZ-kL_cVxY="
```

**Note:** The default value is still allowed for development but should be changed in production.

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

---

## Related Security Fixes (Planned)

See `CLAUDE.md` and `CODE_REVIEW.md` for:
- [ ] Rate limiting (prevent brute force)
- [ ] JWT refresh tokens
- [ ] Token blacklist/revocation
- [ ] Request correlation IDs
- [ ] SQL injection prevention (via Pydantic)
