"""Asynchronous SQLAlchemy engine, sessions, and request dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for future database models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and close it after the request."""

    async with AsyncSessionLocal() as session:
        yield session

