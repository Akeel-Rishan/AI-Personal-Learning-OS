"""Database-backed registration and credential authentication service."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.user import User, UserProfile
from app.schemas.auth import RegisterRequest


class AuthService:
    """Encapsulate user lookup, registration, and authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_user(self, data: RegisterRequest) -> User:
        """Create a unique user and default profile in one transaction."""

        email = str(data.email).lower()
        if await self.get_user_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        user.profile = UserProfile(
            preferred_explanation_style="balanced",
            daily_study_minutes=60,
            timezone="UTC",
        )
        self.db.add(user)

        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            ) from exc

        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """Validate credentials and return an active user."""

        user = await self.get_user_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Find a user by normalized email address."""

        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email.strip().lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Find a user by UUID and eagerly load their profile."""

        try:
            parsed_user_id = uuid.UUID(user_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == parsed_user_id)
        )
        return result.scalar_one_or_none()

