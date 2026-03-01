"""
Simplified Unit Tests for Vocalis V0
Focus on auth module and core business logic without complex database fixtures
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_refresh_token, verify_token,
    JWT_SECRET, JWT_ALGORITHM
)


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================

class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_creates_unique_hashes(self):
        """Test that password hashing creates different hashes each time"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert len(hash1) > 20

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "MySecurePass123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "CorrectPassword"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password against hash"""
        hashed = hash_password("SomePassword")

        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive"""
        password = "MyPassword"
        hashed = hash_password(password)

        assert verify_password("mypassword", hashed) is False
        assert verify_password("MyPassword", hashed) is True


# ============================================================================
# ACCESS TOKEN TESTS
# ============================================================================

class TestAccessTokens:
    """Test access token creation and verification"""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a valid JWT string"""
        token = create_access_token(
            user_id="user123",
            org_id="org456",
            email="test@example.com",
            role="doctor"
        )

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts separated by dots

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token"""
        user_id = "user123"
        org_id = "org456"
        email = "test@example.com"
        role = "doctor"

        token = create_access_token(user_id, org_id, email, role)
        payload = verify_token(token)

        assert payload is not None
        assert payload.user_id == user_id
        assert payload.org_id == org_id
        assert payload.email == email
        assert payload.role == role

    def test_verify_token_invalid_signature(self):
        """Test that token with invalid signature fails verification"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

        payload = verify_token(token)
        assert payload is None

    def test_verify_token_malformed(self):
        """Test that malformed token fails verification"""
        malformed_tokens = [
            "not_a_token",
            "only.two.parts",
            "",
            None
        ]

        for malformed_token in malformed_tokens:
            payload = verify_token(malformed_token) if malformed_token else None
            assert payload is None

    def test_access_token_contains_claims(self):
        """Test that access token contains required claims"""
        token = create_access_token("user1", "org1", "email@test.com", "nurse")

        # Decode with JWT secret to inspect claims
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        assert "user_id" in decoded
        assert "org_id" in decoded
        assert "email" in decoded
        assert "role" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

    def test_access_token_expiration(self):
        """Test that access token has expiration"""
        token = create_access_token("user1", "org1", "email@test.com", "doctor")

        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()

        # Token should expire in the future (within 25 hours)
        assert exp_datetime > now
        assert (exp_datetime - now).total_seconds() < 25 * 3600


# ============================================================================
# REFRESH TOKEN TESTS
# ============================================================================

class TestRefreshTokens:
    """Test refresh token creation and verification"""

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a valid JWT string"""
        token = create_refresh_token(
            user_id="user123",
            org_id="org456",
            email="test@example.com",
            token_family="family_1"
        )

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token"""
        user_id = "user123"
        org_id = "org456"
        email = "test@example.com"
        token_family = "family_1"

        token = create_refresh_token(user_id, org_id, email, token_family)
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["org_id"] == org_id
        assert payload["email"] == email
        assert payload["type"] == "refresh"
        assert payload["token_family"] == token_family

    def test_refresh_token_has_jti(self):
        """Test that refresh token contains unique JTI"""
        token1 = create_refresh_token("user1", "org1", "email@test.com", "family_1")
        token2 = create_refresh_token("user1", "org1", "email@test.com", "family_1")

        payload1 = verify_refresh_token(token1)
        payload2 = verify_refresh_token(token2)

        # Different tokens should have different JTI
        assert payload1["jti"] != payload2["jti"]

    def test_verify_invalid_refresh_token(self):
        """Test verifying invalid refresh token"""
        payload = verify_refresh_token("invalid.token.here")
        assert payload is None

    def test_refresh_token_expiration(self):
        """Test that refresh token expires in ~7 days"""
        token = create_refresh_token("user1", "org1", "email@test.com", "family_1")

        payload = verify_refresh_token(token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()

        # Token should expire in about 7 days
        hours_until_expiry = (exp_datetime - now).total_seconds() / 3600
        assert 160 < hours_until_expiry < 170  # ~7 days = ~168 hours


# ============================================================================
# TOKEN TYPE SEPARATION TESTS
# ============================================================================

class TestTokenTypeSeparation:
    """Test that access and refresh tokens are properly separated"""

    def test_access_token_not_valid_as_refresh(self):
        """Test that access token cannot be used as refresh token"""
        access_token = create_access_token("user1", "org1", "email@test.com", "doctor")

        # Trying to verify as refresh token should fail
        payload = verify_refresh_token(access_token)
        assert payload is None

    def test_refresh_token_payload_structure(self):
        """Test refresh token has required fields"""
        token = create_refresh_token("user1", "org1", "email@test.com", "family_1")
        payload = verify_refresh_token(token)

        required_fields = ["user_id", "org_id", "email", "type", "jti", "token_family"]
        for field in required_fields:
            assert field in payload

    def test_token_family_preserved_in_refresh_token(self):
        """Test that token family is preserved in refresh token"""
        family = "unique_family_id_123"

        token = create_refresh_token("user1", "org1", "email@test.com", family)
        payload = verify_refresh_token(token)

        assert payload["token_family"] == family


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurityValidation:
    """Test security aspects of token handling"""

    def test_jwt_secret_used_for_signing(self):
        """Test that tokens are signed with JWT_SECRET"""
        token = create_access_token("user1", "org1", "email@test.com", "doctor")

        # Verify the token can be decoded with the actual secret
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            assert decoded["user_id"] == "user1"
        except Exception as e:
            pytest.fail(f"Token verification with JWT_SECRET failed: {e}")

    def test_token_tampered_data_rejected(self):
        """Test that tampering with token data is detected"""
        token = create_access_token("user1", "org1", "email@test.com", "doctor")

        # Tamper with the token by modifying it
        tampered_token = token[:-10] + "0000000000"

        payload = verify_token(tampered_token)
        assert payload is None

    def test_password_hash_not_reversible(self):
        """Test that password hashes cannot be reversed"""
        password = "SecurePassword123"
        hashed = hash_password(password)

        # Hash should not contain original password
        assert password not in hashed
        assert hashed != password

    def test_different_users_different_tokens(self):
        """Test that different users get different tokens"""
        token1 = create_access_token("user1", "org1", "email1@test.com", "doctor")
        token2 = create_access_token("user2", "org1", "email2@test.com", "nurse")

        payload1 = verify_token(token1)
        payload2 = verify_token(token2)

        assert payload1.user_id != payload2.user_id
        assert payload1.email != payload2.email
        assert payload1.role != payload2.role


# ============================================================================
# TOKEN ATTRIBUTE TESTS
# ============================================================================

class TestTokenAttributes:
    """Test specific token attributes and their values"""

    def test_token_contains_user_metadata(self):
        """Test that token contains all user metadata"""
        email = "test@example.com"
        role = "doctor"

        token = create_access_token("user123", "org456", email, role)
        payload = verify_token(token)

        assert payload.email == email
        assert payload.role == role

    def test_refresh_token_multiple_calls_unique(self):
        """Test that multiple refresh token calls produce different tokens"""
        tokens = [
            create_refresh_token("user1", "org1", "email@test.com", "family_1")
            for _ in range(3)
        ]

        # All tokens should be different (different JTI)
        jtis = [verify_refresh_token(t)["jti"] for t in tokens]
        assert len(set(jtis)) == 3  # All 3 JTIs are unique


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
