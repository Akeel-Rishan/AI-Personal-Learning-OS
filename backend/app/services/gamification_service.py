"""XP levels, achievements, streaks, and privacy-aware leaderboards."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment
from app.models.exercise import ExerciseAttempt
from app.models.gamification import Achievement, UserAchievement, XPEvent
from app.models.learning import DailyPlan, DailyPlanItem
from app.models.progress import UserSkill
from app.models.project import UserProject
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.user import User


ACHIEVEMENT_ICONS = {
    "First Step": "🚀", "Week Warrior": "🔥", "Month Master": "🏆",
    "Skill Unlocked": "🔓", "10 Skills Strong": "💪", "Project Builder": "🛠️",
    "Assessment Ace": "🎯",
}


class GamificationService:
    """Calculate rewards without storing redundant level or streak state."""

    def __init__(self, db: AsyncSession | None) -> None:
        self.db = db

    @staticmethod
    def _threshold_for_level(level: int) -> int:
        """XP at the start of a level; level 1 starts at zero."""
        if level <= 1:
            return 0
        previous = level - 1
        return 100 * previous * (previous + 1) // 2

    @classmethod
    def calculate_level(cls, total_xp: int) -> dict[str, object]:
        """Pure, monotonic level calculation capped at level 100."""
        xp = max(0, int(total_xp))
        level = min(100, max(1, int((math.sqrt(1 + 8 * xp / 100) - 1) // 2) + 1))
        current = cls._threshold_for_level(level)
        next_threshold = cls._threshold_for_level(level + 1) if level < 100 else current
        progress = max(0, xp - current)
        needed = max(0, next_threshold - xp)
        span = max(1, next_threshold - current)
        titles = [(5, "Beginner"), (10, "Student"), (20, "Learner"), (30, "Practitioner"), (50, "Developer"), (70, "Expert"), (90, "Master"), (100, "Grandmaster")]
        title = next(name for ceiling, name in titles if level <= ceiling)
        return {
            "level": level, "total_xp": xp, "xp_for_current_level": current,
            "xp_for_next_level": next_threshold, "xp_progress": progress,
            "xp_needed": needed, "progress_percentage": 100.0 if level == 100 else round(progress / span * 100, 1),
            "level_title": title,
        }

    def _require_db(self) -> AsyncSession:
        if self.db is None:
            raise RuntimeError("A database session is required for this operation")
        return self.db

    async def get_user_xp_summary(self, user_id: str) -> dict[str, object]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        total = int(await db.scalar(select(func.coalesce(func.sum(XPEvent.xp_earned), 0)).where(XPEvent.user_id == parsed)) or 0)
        rows = (await db.execute(select(XPEvent.event_type, func.sum(XPEvent.xp_earned)).where(XPEvent.user_id == parsed).group_by(XPEvent.event_type))).all()
        recent = list((await db.execute(select(XPEvent).where(XPEvent.user_id == parsed).order_by(XPEvent.created_at.desc()).limit(5))).scalars())
        return {
            **self.calculate_level(total),
            "xp_breakdown": {event_type: int(value or 0) for event_type, value in rows},
            "recent_xp_events": [{"event_type": item.event_type, "xp_earned": item.xp_earned, "description": item.description, "created_at": item.created_at} for item in recent],
        }

    async def get_xp_history(self, user_id: str, days: int = 30) -> list[dict[str, object]]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        today, start = datetime.now(timezone.utc).date(), datetime.now(timezone.utc).date() - timedelta(days=days - 1)
        rows = (await db.execute(select(func.date(XPEvent.created_at), func.sum(XPEvent.xp_earned), func.count(XPEvent.id)).where(XPEvent.user_id == parsed, XPEvent.created_at >= datetime.combine(start, time.min, timezone.utc)).group_by(func.date(XPEvent.created_at)))).all()
        values = {day: (int(xp or 0), int(count or 0)) for day, xp, count in rows}
        return [{"date": day, "xp_earned": values.get(day, (0, 0))[0], "events_count": values.get(day, (0, 0))[1]} for day in (start + timedelta(days=index) for index in range((today - start).days + 1))]

    async def award_xp(self, user_id: str, event_type: str, xp_amount: int, description: str | None = None) -> XPEvent:
        """Grant XP through one path so every reward performs a level-up check."""
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        old_xp = int(await db.scalar(select(func.coalesce(func.sum(XPEvent.xp_earned), 0)).where(XPEvent.user_id == parsed)) or 0)
        event = XPEvent(user_id=parsed, event_type=event_type, xp_earned=max(0, int(xp_amount)), description=description)
        db.add(event)
        await db.flush()
        await self.process_level_up(user_id, old_xp, old_xp + event.xp_earned)
        return event

    async def get_streak_info(self, user_id: str) -> dict[str, object]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        dates = set((await db.execute(select(DailyPlan.plan_date).join(DailyPlanItem).where(DailyPlan.user_id == parsed, DailyPlanItem.status == "completed").distinct())).scalars())
        today = datetime.now(timezone.utc).date()
        cursor = today if today in dates else today - timedelta(days=1)
        current_dates: list[date] = []
        while cursor in dates:
            current_dates.append(cursor); cursor -= timedelta(days=1)
        longest = running = 0; previous: date | None = None
        for activity_date in sorted(dates):
            running = running + 1 if previous and activity_date == previous + timedelta(days=1) else 1
            longest = max(longest, running); previous = activity_date
        current = len(current_dates)
        milestones = (7, 14, 30, 60, 100)
        next_milestone = next((item for item in milestones if item > current), 100)
        return {
            "current_streak": current, "longest_streak": longest,
            "streak_start_date": min(current_dates) if current_dates else None,
            "last_activity_date": max(dates) if dates else None,
            "streak_at_risk": current > 0 and datetime.now().hour >= 18 and today not in dates,
            "streak_frozen": False, "milestone_next": next_milestone,
            "days_to_milestone": max(0, next_milestone - current),
        }

    async def _metrics(self, user_id: str) -> dict[str, float]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        attempts = int(await db.scalar(select(func.count(ExerciseAttempt.id)).where(ExerciseAttempt.user_id == parsed, ExerciseAttempt.is_correct.is_not(None))) or 0)
        mastered = int(await db.scalar(select(func.count(UserSkill.id)).where(UserSkill.user_id == parsed, UserSkill.mastery_score >= .8)) or 0)
        roadmap_projects = int(await db.scalar(select(func.count(RoadmapItem.id)).join(RoadmapPhase).join(Roadmap).where(Roadmap.user_id == parsed, RoadmapItem.item_type == "project", RoadmapItem.status == "completed")) or 0)
        built_projects = int(await db.scalar(select(func.count(UserProject.id)).where(UserProject.user_id == parsed, UserProject.status == "completed")) or 0)
        projects = roadmap_projects + built_projects
        best_assessment = float(await db.scalar(select(func.coalesce(func.max(Assessment.score_percentage), 0)).where(Assessment.user_id == parsed, Assessment.status == "completed")) or 0)
        streak = float((await self.get_streak_info(user_id))["current_streak"])
        return {"attempts": attempts, "mastered": mastered, "projects": projects, "best_assessment": best_assessment, "streak": streak}

    @staticmethod
    def _achievement_value(name: str, metrics: dict[str, float]) -> float:
        return {
            "First Step": metrics["attempts"], "Week Warrior": metrics["streak"],
            "Month Master": metrics["streak"], "Skill Unlocked": metrics["mastered"],
            "10 Skills Strong": metrics["mastered"], "Project Builder": metrics["projects"],
            "Assessment Ace": metrics["best_assessment"],
        }.get(name, 0)

    async def check_and_award_achievements(self, user_id: str) -> list[UserAchievement]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        metrics = await self._metrics(user_id)
        achievements = list((await db.execute(select(Achievement))).scalars())
        earned_ids = set((await db.execute(select(UserAchievement.achievement_id).where(UserAchievement.user_id == parsed))).scalars())
        awarded: list[UserAchievement] = []
        for achievement in achievements:
            if achievement.id in earned_ids or self._achievement_value(achievement.name, metrics) < achievement.condition_value:
                continue
            award = UserAchievement(user_id=parsed, achievement_id=achievement.id)
            award.achievement = achievement
            db.add(award)
            await self.award_xp(user_id, "achievement_earned", achievement.xp_reward, f"Achievement unlocked: {achievement.name}")
            awarded.append(award)
        if awarded:
            await db.flush()
        return awarded

    async def calculate_achievement_progress(self, user_id: str, achievement: Achievement) -> tuple[float, str]:
        metrics = await self._metrics(user_id)
        value = self._achievement_value(achievement.name, metrics)
        target = max(1, achievement.condition_value)
        progress = min(1.0, value / target)
        if achievement.achievement_type == "streak": label = f"{int(value)} / {target} days"
        elif achievement.achievement_type == "skill": label = f"{int(value)} / {target} skills"
        elif achievement.achievement_type == "assessment": label = f"Best score: {round(value)}% / {target}%"
        elif achievement.achievement_type == "project": label = f"{int(value)} / {target} projects"
        else: label = f"{int(value)} / {target} completed"
        return round(progress, 3), label

    async def get_user_achievements(self, user_id: str) -> dict[str, object]:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        achievements = list((await db.execute(select(Achievement).order_by(Achievement.created_at))).scalars())
        earned_rows = list((await db.execute(select(UserAchievement).options(selectinload(UserAchievement.achievement)).where(UserAchievement.user_id == parsed))).scalars())
        earned_by_id = {row.achievement_id: row for row in earned_rows}
        earned, locked = [], []
        for achievement in achievements:
            base = {"id": str(achievement.id), "name": achievement.name, "description": achievement.description, "icon": achievement.icon or ACHIEVEMENT_ICONS.get(achievement.name, "🏅"), "achievement_type": achievement.achievement_type, "xp_reward": achievement.xp_reward}
            row = earned_by_id.get(achievement.id)
            if row: earned.append({**base, "earned_at": row.earned_at, "progress": 1.0, "progress_label": "Completed"})
            else:
                progress, label = await self.calculate_achievement_progress(user_id, achievement)
                locked.append({**base, "earned_at": None, "progress": progress, "progress_label": label})
        total = len(achievements)
        return {"earned": earned, "locked": locked, "total_earned": len(earned), "total_available": total, "completion_percentage": round(len(earned) / total * 100, 1) if total else 0}

    async def process_level_up(self, user_id: str, old_xp: int, new_xp: int) -> dict[str, object] | None:
        db, parsed = self._require_db(), self._parse_uuid(user_id)
        old, new = self.calculate_level(old_xp), self.calculate_level(new_xp)
        if int(new["level"]) <= int(old["level"]): return None
        bonus = 50 * int(new["level"])
        db.add(XPEvent(user_id=parsed, event_type="level_up_bonus", xp_earned=bonus, description=f"Reached level {new['level']} — {new['level_title']}"))
        return {"leveled_up": True, "old_level": old["level"], "new_level": new["level"], "new_title": new["level_title"], "bonus_xp": bonus}

    async def get_leaderboard(self, user_id: str) -> list[dict[str, object]]:
        db, current = self._require_db(), self._parse_uuid(user_id)
        rows = (await db.execute(select(User, func.coalesce(func.sum(XPEvent.xp_earned), 0).label("total_xp")).outerjoin(XPEvent, XPEvent.user_id == User.id).group_by(User.id).order_by(func.coalesce(func.sum(XPEvent.xp_earned), 0).desc()))).all()
        ranked: list[dict[str, object]] = []
        for rank, (user, total) in enumerate(rows, 1):
            if rank > 10 and user.id != current: continue
            parts = user.full_name.strip().split()
            anonymous = parts[0] + (f" {parts[-1][0]}." if len(parts) > 1 else "")
            streak = int((await self.get_streak_info(str(user.id)))["current_streak"])
            ranked.append({"rank": rank, "user_name": anonymous, "level": self.calculate_level(int(total))["level"], "total_xp": int(total), "streak": streak, "is_current_user": user.id == current})
        return ranked

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID:
        try: return uuid.UUID(value)
        except ValueError as exc: raise HTTPException(status_code=422, detail="Invalid identifier") from exc
