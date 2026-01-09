"""Shared utilities for v2 API endpoints."""
from typing import Optional
from jose import JWTError, jwt
from config.settings import settings


def get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    """Extract username from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Username if token is valid, None otherwise
    """
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("user_name")
    except JWTError:
        return None


def normalize_optional(value: Optional[str]) -> Optional[str]:
    """Normalize optional string value (strip whitespace, convert empty to None).
    
    Args:
        value: String value to normalize
        
    Returns:
        Normalized string or None
    """
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None

