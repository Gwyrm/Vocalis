"""Authentication utilities for Vocalis"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging

logger = logging.getLogger("vocalis-backend")

# Configuration
_DEFAULT_JWT_SECRET = "your-secret-key-change-in-production"
JWT_SECRET = os.getenv("JWT_SECRET", _DEFAULT_JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Password hashing - use argon2 for secure password storage (more reliable than bcrypt)
# Falls back to pbkdf2 if argon2 unavailable
try:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except Exception:
    # Fallback to pbkdf2 if argon2 not available
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class TokenData:
    """Token payload data"""
    def __init__(self, user_id: str, org_id: str, email: str, role: str):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role


def hash_password(password: str) -> str:
    """Hash a password using argon2 or pbkdf2"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def create_access_token(user_id: str, org_id: str, email: str, role: str) -> str:
    """Create a JWT access token"""
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        email = payload.get("email")
        role = payload.get("role")

        if not all([user_id, org_id, email, role]):
            return None

        return TokenData(user_id=user_id, org_id=org_id, email=email, role=role)
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def validate_jwt_secret() -> bool:
    """
    Validate JWT secret configuration for security.

    Returns:
        True if secret is valid for current environment

    Raises:
        ValueError if JWT secret is insecure in production
    """
    is_using_default = JWT_SECRET == _DEFAULT_JWT_SECRET
    is_production = ENVIRONMENT in ["production", "prod"]

    if is_production and is_using_default:
        error_msg = (
            "SECURITY ERROR: JWT_SECRET environment variable not set in production! "
            "This uses an insecure default secret that is visible in code. "
            "Generate a secure secret and set the JWT_SECRET environment variable. "
            "\n\nGenerate a secure secret with: "
            "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
        logger.critical(error_msg)
        raise ValueError(error_msg)

    if is_using_default:
        logger.warning(
            "Using default JWT secret (development mode). "
            "This is INSECURE for production. "
            "Set JWT_SECRET environment variable for production deployments."
        )
    else:
        logger.info("JWT secret configured from environment variable (secure)")

    return True
