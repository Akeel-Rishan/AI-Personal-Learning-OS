"""JWT authentication routes for registration, sessions, and current user data."""

from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse, UserWithProfileResponse
from app.services.auth_service import AuthService


router = APIRouter()


def _create_token_pair(user: User) -> tuple[str, str]:
    """Create access and refresh tokens containing the required identity claims."""

    claims: dict[str, object] = {"sub": user.email, "user_id": str(user.id)}
    return create_access_token(claims), create_refresh_token(claims)


def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set signed tokens in HTTP-only cookies without exposing refresh tokens to JavaScript."""

    secure = settings.environment.lower() == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _auth_response(user: User, access_token: str, refresh_token: str) -> AuthResponse:
    """Build the common register/login response."""

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def _parse_login_request(request: Request) -> LoginRequest:
    """Accept JSON credentials and OAuth2 form credentials on the same endpoint."""

    try:
        if "application/x-www-form-urlencoded" in request.headers.get("content-type", ""):
            form = await request.form()
            return LoginRequest(
                email=str(form.get("username") or form.get("email") or ""),
                password=str(form.get("password") or ""),
            )
        return LoginRequest.model_validate(await request.json())
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address and password",
        ) from exc


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Register a learner and immediately establish an authenticated session."""

    user = await AuthService(db).register_user(payload)
    access_token, refresh_token = _create_token_pair(user)
    _set_token_cookies(response, access_token, refresh_token)
    return _auth_response(user, access_token, refresh_token)


@router.post(
    "/login",
    response_model=AuthResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "password": {"type": "string", "format": "password"},
                        },
                    }
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {"type": "string", "format": "email"},
                            "password": {"type": "string", "format": "password"},
                        },
                    }
                },
            },
        }
    },
)
async def login(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Authenticate JSON or OAuth2-form credentials and return signed tokens."""

    payload = await _parse_login_request(request)
    user = await AuthService(db).authenticate_user(str(payload.email), payload.password)
    access_token, refresh_token = _create_token_pair(user)
    _set_token_cookies(response, access_token, refresh_token)
    return _auth_response(user, access_token, refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: Annotated[RefreshRequest | None, Body()] = None,
    refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    """Rotate a valid refresh token and issue a new token pair."""

    refresh_token = payload.refresh_token if payload is not None else refresh_cookie
    token_payload = decode_token(refresh_token) if refresh_token else None
    if token_payload is None or token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = token_payload.get("user_id")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await AuthService(db).get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    new_access_token, new_refresh_token = _create_token_pair(user)
    _set_token_cookies(response, new_access_token, new_refresh_token)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    """Clear authentication cookies."""

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserWithProfileResponse)
async def current_user(
    user: Annotated[User, Depends(get_current_active_user)],
) -> UserWithProfileResponse:
    """Return the authenticated learner and profile."""

    return UserWithProfileResponse.model_validate(user)
