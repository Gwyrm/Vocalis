# Rate Limiting Configuration

This document explains the rate limiting implementation for the Vocalis API.

## Overview

Rate limiting protects the API from:
- **Brute force attacks** - Password guessing on login
- **API abuse** - Free LLM service exploitation
- **Resource exhaustion** - Denial of Service (DoS) attacks
- **Spam** - Bulk account creation or data injection

## Rate Limits

### Authentication Endpoints (Strict Limits)

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /api/auth/login` | **5/minute** per IP | Prevent brute force password attacks |
| `POST /api/auth/register` | **3/minute** per IP | Prevent spam account creation |
| `PUT /api/auth/change-password` | 5/hour per user | Prevent password change spam |

**Example:** An attacker trying to brute force a password can only make 5 login attempts per minute.

### Chat & LLM Endpoints (Moderate Limits)

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /api/chat` | **20/minute** per IP | Prevent free LLM service abuse |
| `POST /api/generate-pdf` | **10/minute** per user | Prevent resource exhaustion |
| `POST /api/voice/transcribe` | **10/minute** per user | Prevent audio processing spam |

**Example:** A user can send at most 20 chat messages per minute.

### Data Endpoints (Standard Limits)

| Operation | Limit | Purpose |
|-----------|-------|---------|
| Create (POST) | 100/minute per IP | Prevent bulk data injection |
| Read (GET) | 300/minute per IP | Allow normal browsing |
| Update (PUT) | 100/minute per IP | Prevent data corruption spam |
| Delete (DELETE) | 50/minute per IP | Prevent mass deletion |

### Special Endpoints

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /api/offline-sync/push` | 10/minute per user | Prevent sync spam |

## How It Works

### Rate Limit Tracking

- **Key function:** Remote IP address (for unauthenticated endpoints)
- **Storage:** In-memory (per process)
- **Window:** Fixed time windows (minute, hour)

```python
# Authentication endpoints use IP-based limiting
limiter.limit("5/minute")  # 5 requests per minute per IP

# Authenticated endpoints also use IP
limiter.limit("20/minute")  # 20 requests per minute per IP
```

### Rate Limit Headers

When making requests, responses include rate limit information:

```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1640000000
```

### Rate Limit Exceeded Response

**Status:** `429 Too Many Requests`

**Response Body:**
```json
{
  "status": "error",
  "detail": "Too many requests. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

**Headers:**
```
Retry-After: 23
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000023
```

## Configuration

### Adjusting Rate Limits

Edit `rate_limit.py` to modify limits:

```python
# Authentication endpoints - Strict limits to prevent brute force
LOGIN_LIMIT = "5/minute"  # Increase to 10/minute if needed
REGISTER_LIMIT = "3/minute"  # Increase to 5/minute if needed

# Chat/LLM endpoints - Moderate limits to prevent abuse
CHAT_LIMIT = "20/minute"  # Increase to 30/minute if needed
PDF_GENERATION_LIMIT = "10/minute"  # Increase to 20/minute if needed
```

### Production Recommendations

1. **Monitor rate limit hits**
   ```python
   # In rate_limit.py error handler
   logger.warning(f"Rate limit exceeded for {ip}: {path}")
   ```

2. **Adjust based on usage patterns**
   - Start strict, relax if legitimate users complain
   - Keep authentication limits strict always

3. **Consider per-user limits**
   ```python
   # For premium users, increase limits
   if user.tier == "premium":
       limiter.limit("100/minute")
   ```

4. **Use distributed rate limiting in production**
   ```python
   # Use Redis for multi-process deployments
   limiter = Limiter(
       key_func=get_remote_address,
       storage_uri="redis://localhost:6379"
   )
   ```

## Implementation Details

### Endpoints with Rate Limiting

```python
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    ...

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(
    request: ChatRequest,
    http_request: Request,  # Required by slowapi
    current_user: User = Depends(get_current_user)
):
    """Chat endpoint with LLM (authenticated users only)"""
    ...
```

**Note:** Endpoints with rate limiting need a `Request` parameter for slowapi to work:
```python
async def endpoint(..., http_request: Request, ...):
    # Use http_request parameter (required even if not used in function)
    ...
```

### Error Handling

```python
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return await rate_limit_error_handler(request, exc)
```

## Testing Rate Limits

### Test Login Brute Force Protection

```bash
# Script to test rate limiting
#!/bin/bash

for i in {1..10}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"user@example.com","password":"wrong"}' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

Expected: Requests 1-5 return 200/401, requests 6-10 return 429

### Test Chat Rate Limiting

```bash
# Test chat endpoint rate limiting
for i in {1..25}; do
  curl -X POST http://localhost:8080/api/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"message":"test"}' \
    -w "\nStatus: %{http_code}\n" 2>/dev/null
done
```

Expected: Requests 1-20 succeed, requests 21-25 return 429

### Monitor Rate Limit Logs

```bash
# Watch for rate limit errors in logs
tail -f logs/vocalis-backend.log | grep "Rate limit exceeded"
```

## Troubleshooting

### Users Getting 429 Errors

**Cause:** Rate limit too strict
**Solution:** Increase limit in `rate_limit.py` and redeploy

```python
LOGIN_LIMIT = "10/minute"  # Increased from 5
```

### Rate Limiting Not Working

**Check:**
1. Is `slowapi` installed? `pip install slowapi`
2. Is the decorator applied to endpoint?
3. Is the `Request` parameter present?

```python
@app.post("/api/endpoint")
@limiter.limit("10/minute")  # ✅ Decorator present
async def endpoint(
    data: MyRequest,
    http_request: Request,  # ✅ Request parameter present
    ...
):
    ...
```

### Production Deployment with Multiple Workers

**Issue:** Rate limits reset per worker (Gunicorn/Uvicorn)

**Solution:** Use Redis backend

```python
# rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",  # Use Redis
    strategy="fixed-window"
)
```

**Docker Compose example:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  vocalis-backend:
    environment:
      REDIS_URL: redis://redis:6379
```

## Security Best Practices

1. **Keep authentication limits strict**
   - Always use 5/minute or stricter for login
   - Never relax below 3/minute

2. **Monitor for attacks**
   ```python
   # Log suspicious patterns
   if request_count_this_minute > LIMIT * 3:
       logger.critical(f"Potential attack from {ip}")
   ```

3. **Combine with other security measures**
   - CAPTCHA after repeated failed attempts
   - IP blocking after excessive violations
   - Account lockout after N failed logins

4. **Transparent communication**
   - Include rate limit info in API docs
   - Provide clear error messages
   - Show retry information in headers

## Metrics & Monitoring

### Log Format

```
2026-03-01 16:00:00,123 - vocalis-backend - WARNING - Rate limit exceeded for 192.168.1.1: /api/auth/login
```

### What to Track

1. **Limit violations by endpoint**
   ```python
   metrics.counter("rate_limit.exceeded", tags=["endpoint:/api/auth/login"])
   ```

2. **Top IPs triggering limits**
   ```python
   metrics.gauge("rate_limit.violators", value=5)
   ```

3. **Legitimate user reports**
   - User tickets about 429 errors
   - Increase limit if >5% users affected

## Future Enhancements

- [ ] Per-user tier-based rate limits
- [ ] Redis backend for distributed deployments
- [ ] Dynamic rate limit adjustment
- [ ] Rate limit bypass for whitelisted IPs
- [ ] Graduated rate limit increases for new users
- [ ] CAPTCHA integration after X failures
