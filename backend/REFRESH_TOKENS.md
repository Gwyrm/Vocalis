# JWT Refresh Tokens - Implementation Guide

## Overview

Vocalis now implements a two-token authentication system:
- **Access tokens**: Short-lived (default: 24 hours), used for API requests
- **Refresh tokens**: Long-lived (default: 7 days), used to obtain new access tokens without re-login

This system improves security and user experience by:
- Minimizing the window of exposure if access tokens are compromised
- Allowing long-lived sessions without forcing users to re-enter passwords
- Enabling immediate revocation via database lookup
- Supporting token rotation to detect replay attacks

## How It Works

### Login Flow

```
1. User submits email + password
2. Server validates credentials
3. Server generates:
   - Access token (JWT, 24 hours)
   - Refresh token (JWT, 7 days)
   - Stores refresh token in database with metadata
4. Client receives both tokens
5. Client stores refresh token securely (httpOnly cookie or secure storage)
6. Client uses access token for all API requests
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "refresh_token": "eyJhbGc...",
  "refresh_expires_in": 604800,
  "user": {
    "id": "user-123",
    "email": "doctor@hospital.fr",
    "role": "doctor",
    "org_id": "org-456"
  }
}
```

### Token Refresh Flow (Token Rotation)

```
1. Access token expires (after 24 hours)
2. Client uses refresh token to get new tokens
3. Server validates refresh token signature + database lookup
4. Server generates:
   - New access token (24 hours)
   - New refresh token (7 days, same family)
5. Old refresh token remains valid (grace period for offline clients)
6. Returns both new tokens to client
```

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc... (new)",
  "token_type": "bearer",
  "expires_in": 86400,
  "refresh_token": "eyJhbGc... (new, rotated)",
  "refresh_expires_in": 604800,
  "status": "token_rotated"
}
```

### Logout Flow (Single Device)

```
1. User clicks logout
2. Client sends refresh token to be revoked
3. Server marks token as revoked in database
4. Token becomes immediately unusable
5. User must re-login on this device
```

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully logged out"
}
```

### Logout All Devices Flow

```
1. User clicks "logout all devices"
2. Server revokes ALL refresh tokens for user
3. All other devices lose ability to refresh tokens
4. Users on other devices must re-login when access token expires
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully logged out from all devices"
}
```

## API Endpoints

### POST /api/auth/login
Login and receive access + refresh tokens.

**Rate Limit:** 5/minute per IP

**Request:**
```json
{
  "email": "user@hospital.fr",
  "password": "secure_password"
}
```

**Response:** `TokenResponse` (includes access_token, refresh_token, expires_in, etc.)

### POST /api/auth/register
Register new user and receive tokens.

**Rate Limit:** 3/minute per IP

**Request:**
```json
{
  "email": "user@hospital.fr",
  "password": "secure_password",
  "full_name": "Dr. Jean Dupont",
  "role": "doctor"
}
```

**Response:** `TokenResponse` (same as login)

### POST /api/auth/refresh
Get new access + refresh tokens using current refresh token.

**Rate Limit:** 30/minute per IP

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:** `TokenRefreshResponse` (new access_token and refresh_token)

**Error Cases:**
- 401 "Invalid or expired refresh token" - If token is invalid, expired, or revoked
- 401 "User not found or inactive" - If user was deleted/deactivated

### POST /api/auth/logout
Logout current device by revoking refresh token.

**Authentication:** Required (Bearer token)

**Rate Limit:** Not explicitly limited (normal data operation)

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully logged out"
}
```

### POST /api/auth/logout-all
Logout all devices by revoking all refresh tokens.

**Authentication:** Required (Bearer token)

**Rate Limit:** Not explicitly limited (normal data operation)

**Response:**
```json
{
  "status": "success",
  "message": "Successfully logged out from all devices"
}
```

## Security Features

### Token Rotation
- Each refresh generates a new refresh token
- All tokens in the same session belong to the "token family"
- Allows grace period for offline clients
- Future: Can detect token reuse attacks by monitoring family

### Database Validation
- Refresh tokens are stored in database (not purely stateless)
- Enables immediate revocation
- Tracks token usage (last_used_at)
- Prevents use after logout

### Token Families
- Each login session has unique token family ID
- All rotated tokens share same family
- Detects when same token used twice (attack indicator)
- Future: Auto-revoke all tokens in family if reuse detected

### Rate Limiting
- Login: 5 attempts/minute (prevent brute force)
- Register: 3/minute (prevent spam)
- Refresh: 30/minute (allow normal mobile refresh)
- Allows legitimate apps while blocking attacks

### HTTP Bearer Token
- Access tokens always sent in Authorization header
- Format: `Authorization: Bearer <token>`
- Never in URL or body parameters

## Database Schema

### RefreshToken Table
```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY,
  jti VARCHAR(255) UNIQUE,        -- JWT ID for tracking
  user_id UUID FOREIGN KEY,        -- User who owns token
  org_id UUID FOREIGN KEY,         -- Organization scoping
  token_family VARCHAR(36),        -- Family ID for rotation
  created_at TIMESTAMP,            -- When token was created
  expires_at TIMESTAMP,            -- When token expires
  revoked_at TIMESTAMP,            -- When token was revoked (NULL if not)
  last_used_at TIMESTAMP,          -- Last time token was used
  is_revoked BOOLEAN               -- Quick revocation check
);
```

**Indexes:**
- PRIMARY on `id`
- UNIQUE on `jti` (for quick lookup)
- INDEX on `(user_id, org_id, is_revoked, expires_at)` for validation queries

## Configuration

### Environment Variables

```bash
# JWT token expiration (hours)
JWT_EXPIRATION_HOURS=24

# Refresh token expiration (days)
REFRESH_TOKEN_EXPIRATION_DAYS=7
```

### Recommended Values

**Development:**
- `JWT_EXPIRATION_HOURS=24` (1 day - quick testing)
- `REFRESH_TOKEN_EXPIRATION_DAYS=7` (1 week)

**Production:**
- `JWT_EXPIRATION_HOURS=1` (1 hour - minimal exposure window)
- `REFRESH_TOKEN_EXPIRATION_DAYS=7` (1 week - reasonable session duration)
- `JWT_EXPIRATION_HOURS=24` (1 day - if server-side apps, less refresh overhead)

## Client Implementation (Flutter/Dart)

### Token Storage

**Web:**
```dart
// Use httpOnly cookies (server-set via Set-Cookie header)
// JavaScript cannot access - prevents XSS attacks
// Browser auto-includes in requests
```

**Mobile (iOS/Android):**
```dart
// Use secure storage (FlutterSecureStorage)
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final storage = FlutterSecureStorage();

// Store tokens
await storage.write(key: 'access_token', value: accessToken);
await storage.write(key: 'refresh_token', value: refreshToken);

// Retrieve tokens
String? accessToken = await storage.read(key: 'access_token');
```

### Auto-Refresh Implementation

```dart
class AuthService {
  static const String API_URL = 'http://localhost:8080';

  Future<String> getValidAccessToken() async {
    String? token = await storage.read(key: 'access_token');
    String? refreshToken = await storage.read(key: 'refresh_token');

    // Check if token is expired (via JWT decode)
    if (isTokenExpired(token)) {
      // Token expired - refresh it
      if (refreshToken != null && !isTokenExpired(refreshToken)) {
        await _refreshToken(refreshToken);
      } else {
        // Refresh token also expired - user must re-login
        throw Exception('Session expired. Please login again.');
      }
    }

    return token!;
  }

  Future<void> _refreshToken(String refreshToken) async {
    try {
      final response = await http.post(
        Uri.parse('$API_URL/api/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'refresh_token': refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        // Store new tokens
        await storage.write(
          key: 'access_token',
          value: data['access_token'],
        );
        await storage.write(
          key: 'refresh_token',
          value: data['refresh_token'],
        );
      } else {
        throw Exception('Token refresh failed');
      }
    } catch (e) {
      // Refresh failed - user must re-login
      throw Exception('Session expired. Please login again.');
    }
  }

  Future<void> logout() async {
    String? refreshToken = await storage.read(key: 'refresh_token');

    try {
      // Notify server to revoke token
      await http.post(
        Uri.parse('$API_URL/api/auth/logout'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${await getValidAccessToken()}',
        },
        body: json.encode({'refresh_token': refreshToken}),
      );
    } catch (e) {
      logger.warning('Logout API call failed: $e');
      // Continue with local logout even if server call fails
    }

    // Clear local storage
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
  }

  Future<void> logoutAllDevices() async {
    try {
      await http.post(
        Uri.parse('$API_URL/api/auth/logout-all'),
        headers: {
          'Authorization': 'Bearer ${await getValidAccessToken()}',
        },
      );
    } catch (e) {
      logger.warning('Logout all API call failed: $e');
    }

    // Clear local storage
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
  }
}
```

### API Helper with Auto-Refresh

```dart
class ApiClient {
  final AuthService authService;

  Future<Response> get(String path) async {
    final token = await authService.getValidAccessToken();

    final response = await http.get(
      Uri.parse('${AuthService.API_URL}$path'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    // Handle token expiration mid-request (race condition)
    if (response.statusCode == 401) {
      // Token might have expired - retry once
      final newToken = await authService.getValidAccessToken();
      return http.get(
        Uri.parse('${AuthService.API_URL}$path'),
        headers: {
          'Authorization': 'Bearer $newToken',
          'Content-Type': 'application/json',
        },
      );
    }

    return response;
  }

  // Similar for post(), put(), delete(), etc.
}
```

## Testing

### Manual Testing

**1. Login and Get Tokens**
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.fr",
    "password": "password123"
  }'

# Response: {"access_token": "...", "refresh_token": "...", ...}
```

**2. Use Access Token to Call API**
```bash
curl -X GET http://localhost:8080/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**3. Refresh Token (Token Rotation)**
```bash
curl -X POST http://localhost:8080/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# Response: {"access_token": "... (new)", "refresh_token": "... (new)", ...}
```

**4. Logout (Revoke Single Token)**
```bash
curl -X POST http://localhost:8080/api/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

**5. Logout All Devices**
```bash
curl -X POST http://localhost:8080/api/auth/logout-all \
  -H "Authorization: Bearer <access_token>"
```

**6. Try Revoked Token (Should Fail)**
```bash
curl -X POST http://localhost:8080/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<old_refresh_token>"}'

# Response: 401 "Invalid or revoked refresh token"
```

## Security Considerations

### Threats Mitigated

✅ **Compromised Access Token**
- Short lifetime (24 hours default)
- Attacker has limited time window
- User can logout-all to revoke remaining tokens

✅ **Compromised Refresh Token**
- Stored in database
- Can be immediately revoked
- Not exposed in logs (stored as hash in production)
- Token family tracks reuse attacks

✅ **Session Hijacking**
- Token rotation on each refresh
- Attacker using old token doesn't get new tokens
- Server detects reuse and can revoke family

❌ **XSS Attacks (mitigated via cookie flag)**
- Use httpOnly cookies (JavaScript cannot access)
- Browser auto-includes in requests
- Immune to document.cookie theft

### HTTPS Requirement

**PRODUCTION:**
- MUST use HTTPS for all requests
- Tokens transmitted in Authorization header
- Never transmit tokens in query parameters
- Redirect HTTP to HTTPS

**Development:**
- HTTP is acceptable for localhost testing
- Not recommended for public internet

### Token Expiration Cleanup

Expired tokens can be cleaned from database:

```sql
DELETE FROM refresh_tokens
WHERE expires_at < NOW() AND is_revoked = FALSE
  AND expires_at < NOW() - INTERVAL 1 DAY;  -- Keep for 1 day audit trail
```

Schedule via cron or background job (weekly).

## Troubleshooting

### "Invalid or expired refresh token"
- **Cause**: Token has expired (> 7 days old by default)
- **Solution**: User must re-login

### "User not found or inactive"
- **Cause**: User was deactivated or deleted
- **Solution**: Create new account and login

### Token not refreshing on mobile
- **Cause**: Secure storage permissions issue
- **Solution**: Check app permissions, reinstall app

### Rate limit exceeded on refresh endpoint
- **Cause**: Too many refresh attempts (> 30/minute)
- **Solution**: Check for client-side retry loops, implement exponential backoff

## Future Enhancements

- [ ] Device fingerprinting (bind tokens to devices)
- [ ] Conditional access (require re-auth for sensitive operations)
- [ ] Audit trail (log all token operations with IP)
- [ ] Token scope (different permissions per token)
- [ ] Biometric re-auth (for high-risk operations)
- [ ] Geographic anomaly detection (alert on suspicious login)
- [ ] Account recovery codes (backup authentication)
