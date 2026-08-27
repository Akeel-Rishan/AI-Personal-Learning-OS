"""FastAPI application entry point and lifecycle management."""

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import engine
from app.services.adaptive_scheduler import start_adaptive_scheduler, stop_adaptive_scheduler


class RootResponse(BaseModel):
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
    start_adaptive_scheduler()


@app.on_event("shutdown")
async def disconnect_from_database() -> None:
    """Dispose of pooled database connections during shutdown."""

    stop_adaptive_scheduler()
    await engine.dispose()


@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Return the API identity and status."""

    return RootResponse(status="ok", message="AI Learning OS API")
