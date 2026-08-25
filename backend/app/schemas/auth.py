"""Authentication request bodies and token response schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Validated account-registration input."""

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        """Normalize whitespace in a learner's display name."""

        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Normalize email addresses for reliable uniqueness checks."""

        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Require uppercase and numeric characters in registration passwords."""

        if not any(character.isupper() for character in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must contain at least one number")
        return value


class LoginRequest(BaseModel):
    """Credentials accepted by the login endpoint."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Normalize login email addresses."""

        return str(value).strip().lower()


class TokenResponse(BaseModel):
    """Access and refresh token pair returned by authentication operations."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    """Token response returned alongside the authenticated user."""

    user: UserResponse


class RefreshRequest(BaseModel):
    """Refresh token request body used when a cookie is unavailable."""

    refresh_token: str


class LogoutResponse(BaseModel):
    """Confirmation returned after clearing authentication cookies."""

    message: str
