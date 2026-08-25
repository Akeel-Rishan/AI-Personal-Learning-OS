"""Password hashing and signed JWT creation/verification utilities."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


ALGORITHM = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt."""

    return password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely compare a plain-text password with a stored hash."""

    return password_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, object],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed short-lived access token."""

    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {**data, "type": "access", "exp": expires_at},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(data: dict[str, object]) -> str:
    """Create a signed refresh token with the configured lifetime."""

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(
        {**data, "type": "refresh", "exp": expires_at},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict[str, object] | None:
    """Decode and validate a token, returning None for invalid or expired tokens."""

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
    return dict(payload)

