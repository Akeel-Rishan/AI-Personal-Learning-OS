"""Scheduled adaptive scans and daily-plan refreshes for recently active learners."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.exercise import ExerciseAttempt
from app.models.learning import LearningSession
from app.models.user import User
from app.services.adaptive_engine import AdaptiveEngine
from app.services.plan_service import PlanService


logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _recent_user_ids() -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    async with AsyncSessionLocal() as db:
        ids = set((await db.scalars(select(User.id).where(User.is_active.is_(True), User.updated_at >= cutoff))).all())
        ids.update((await db.scalars(select(LearningSession.user_id).where(LearningSession.created_at >= cutoff))).all())
        ids.update((await db.scalars(select(ExerciseAttempt.user_id).where(ExerciseAttempt.created_at >= cutoff))).all())
        ids.update((await db.scalars(select(Assessment.user_id).where(Assessment.updated_at >= cutoff))).all())
        return [str(item) for item in ids]


async def run_daily_adaptation_scans() -> None:
    for user_id in await _recent_user_ids():
        try:
            async with AsyncSessionLocal() as db:
                await AdaptiveEngine(db).run_full_adaptation_scan(user_id)
        except Exception:
            logger.exception("Scheduled adaptive scan failed for user=%s", user_id)


async def ensure_daily_plans() -> None:
    for user_id in await _recent_user_ids():
        try:
            async with AsyncSessionLocal() as db:
                await PlanService(db).get_or_create_today_plan(user_id)
        except Exception:
            logger.exception("Scheduled daily-plan refresh failed for user=%s", user_id)


def start_adaptive_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(run_daily_adaptation_scans, "cron", hour=3, minute=0, id="adaptive_scan", replace_existing=True)
    scheduler.add_job(ensure_daily_plans, "cron", hour=6, minute=0, id="daily_plan_refresh", replace_existing=True)
    scheduler.start()


def stop_adaptive_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
