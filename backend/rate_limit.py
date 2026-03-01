"""Rate limiting configuration for Vocalis API"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("vocalis-backend")

# Initialize rate limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom error handler for rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": "error",
            "detail": "Too many requests. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
        },
    )


# ============================================================================
# Rate Limit Definitions
# ============================================================================

# Authentication endpoints - Strict limits to prevent brute force
LOGIN_LIMIT = "5/minute"  # 5 attempts per minute per IP
REGISTER_LIMIT = "3/minute"  # 3 registrations per minute per IP
PASSWORD_CHANGE_LIMIT = "5/hour"  # 5 attempts per hour per IP
REFRESH_TOKEN_LIMIT = "30/minute"  # 30 refresh attempts per minute per IP (moderate - normal usage)

# Chat/LLM endpoints - Moderate limits to prevent abuse
CHAT_LIMIT = "20/minute"  # 20 messages per minute per user
PDF_GENERATION_LIMIT = "10/minute"  # 10 PDF generations per minute per user
VOICE_TRANSCRIPTION_LIMIT = "10/minute"  # 10 voice uploads per minute per user

# Data endpoints - Standard limits
DATA_CREATION_LIMIT = "100/minute"  # Create operations
DATA_READ_LIMIT = "300/minute"  # Read operations (higher - mostly GET)
DATA_UPDATE_LIMIT = "100/minute"  # Update operations
DATA_DELETE_LIMIT = "50/minute"  # Delete operations

# WebSocket - No rate limit (handled differently)
# Offline sync - Moderate limits
OFFLINE_SYNC_LIMIT = "10/minute"  # Sync operations

# ============================================================================
# Rate Limit Groups
# ============================================================================

class RateLimits:
    """Centralized rate limit constants"""

    # Authentication (strict - prevent brute force)
    AUTH_LOGIN = LOGIN_LIMIT
    AUTH_REGISTER = REGISTER_LIMIT
    AUTH_PASSWORD = PASSWORD_CHANGE_LIMIT
    AUTH_REFRESH = REFRESH_TOKEN_LIMIT

    # Chat & LLM (moderate - prevent free API abuse)
    CHAT_MESSAGE = CHAT_LIMIT
    PDF_GENERATE = PDF_GENERATION_LIMIT
    VOICE_TRANSCRIBE = VOICE_TRANSCRIPTION_LIMIT

    # Data operations (standard)
    DATA_CREATE = DATA_CREATION_LIMIT
    DATA_READ = DATA_READ_LIMIT
    DATA_UPDATE = DATA_UPDATE_LIMIT
    DATA_DELETE = DATA_DELETE_LIMIT

    # Special operations
    OFFLINE_SYNC = OFFLINE_SYNC_LIMIT


# ============================================================================
# Documentation
# ============================================================================

RATE_LIMIT_DOCS = {
    "login": {
        "limit": LOGIN_LIMIT,
        "reason": "Prevent brute force password attacks",
        "response": 429,
    },
    "register": {
        "limit": REGISTER_LIMIT,
        "reason": "Prevent account creation spam",
        "response": 429,
    },
    "chat": {
        "limit": CHAT_LIMIT,
        "reason": "Prevent free LLM API abuse",
        "response": 429,
    },
    "pdf": {
        "limit": PDF_GENERATION_LIMIT,
        "reason": "Prevent resource exhaustion",
        "response": 429,
    },
    "data_create": {
        "limit": DATA_CREATION_LIMIT,
        "reason": "Prevent bulk data injection",
        "response": 429,
    },
}
