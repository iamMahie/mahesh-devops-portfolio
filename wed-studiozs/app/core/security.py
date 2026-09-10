"""Password hashing (bcrypt) and JWT issuing/decoding."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError

_BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Return a salted bcrypt hash. bcrypt only reads the first 72 bytes."""
    payload = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(payload, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        payload = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(payload, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, *, expires_minutes: int | None = None) -> tuple[str, int]:
    """Return `(token, expires_in_seconds)` for the given subject (admin email)."""
    ttl = timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(ttl.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Access token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Could not validate credentials.") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise AuthenticationError("Malformed access token.")
    return payload


def slugify(value: str) -> str:
    """ASCII, lowercase, hyphenated slug used for portfolio URLs."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    slug = re.sub(r"[-\s]+", "-", normalized)
    return slug or "portfolio"
