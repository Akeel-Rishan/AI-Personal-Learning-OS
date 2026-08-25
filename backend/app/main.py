"""FastAPI application entry point and lifecycle management."""

from typing import Literal, TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import engine


class RootResponse(TypedDict):
    """Shape returned by the root endpoint."""

    status: Literal["ok"]
    message: Literal["AI Learning OS API"]


app = FastAPI(title="AI Personal Learning OS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v1_router, prefix="/api/v1")


@app.on_event("startup")
async def connect_to_database() -> None:
    """Confirm the database is reachable when the API starts."""

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


@app.on_event("shutdown")
async def disconnect_from_database() -> None:
    """Dispose of pooled database connections during shutdown."""

    await engine.dispose()


@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Return the API identity and status."""

    return {"status": "ok", "message": "AI Learning OS API"}

