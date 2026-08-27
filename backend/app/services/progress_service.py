"""Mastery trends, activity analytics, learning velocity, and predictions."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment
from app.models.exercise import ExerciseAttempt
from app.models.goal import Goal, GoalSkill
from app.models.learning import DailyPlan, DailyPlanItem, LearningSession
from app.models.progress import SkillHistory, UserSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.skill import Skill
from app.services.gamification_service import GamificationService
from app.services.spaced_repetition import SpacedRepetitionScheduler


class ProgressService:
    """Read-only analytics derived from transactional learning records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _user_skills(self, user_id: str) -> list[UserSkill]:
        return list((await self.db.execute(select(UserSkill).options(selectinload(UserSkill.skill), selectinload(UserSkill.history)).where(UserSkill.user_id == self._parse_uuid(user_id)))).scalars().unique())

    async def get_skill_mastery_history(self, user_id: str, skill_id: str | None = None, days: int = 30) -> list[dict[str, object]]:
        skills = await self._user_skills(user_id)
        if skill_id:
            parsed_skill = self._parse_uuid(skill_id)
            skills = [item for item in skills if item.skill_id == parsed_skill]
        today, start = datetime.now(timezone.utc).date(), datetime.now(timezone.utc).date() - timedelta(days=days - 1)
        result: list[dict[str, object]] = []
        for user_skill in skills:
            ordered = sorted(user_skill.history, key=lambda item: item.recorded_at)
            before = [item for item in ordered if item.recorded_at.date() < start]
            value = float(before[-1].mastery_score) if before else 0.0
            by_day: dict[date, float] = {}
            for item in ordered:
                if start <= item.recorded_at.date() <= today:
                    by_day[item.recorded_at.date()] = float(item.mastery_score)
            for index in range(days):
                current = start + timedelta(days=index)
                if current in by_day: value = by_day[current]
                result.append({"date": current, "skill_id": str(user_skill.skill_id), "skill_name": user_skill.skill.name, "mastery_score": round(value, 4), "mastery_percentage": round(value * 100)})
        return result

    async def get_overall_progress_summary(self, user_id: str) -> dict[str, object]:
        parsed, skills = self._parse_uuid(user_id), await self._user_skills(user_id)
        scores = [float(item.mastery_score) for item in skills]
        total_minutes = int(await self.db.scalar(select(func.coalesce(func.sum(LearningSession.duration_minutes), 0)).where(LearningSession.user_id == parsed, LearningSession.status == "completed")) or 0)
        completed_exercises = int(await self.db.scalar(select(func.count(func.distinct(ExerciseAttempt.exercise_id))).where(ExerciseAttempt.user_id == parsed, ExerciseAttempt.is_correct.is_(True))) or 0)
        assessments = int(await self.db.scalar(select(func.count(Assessment.id)).where(Assessment.user_id == parsed, Assessment.status == "completed")) or 0)
        total_roadmap = int(await self.db.scalar(select(func.count(RoadmapItem.id)).join(RoadmapPhase).join(Roadmap).where(Roadmap.user_id == parsed)) or 0)
        complete_roadmap = int(await self.db.scalar(select(func.count(RoadmapItem.id)).join(RoadmapPhase).join(Roadmap).where(Roadmap.user_id == parsed, RoadmapItem.status == "completed")) or 0)
        activity_dates = set((await self.db.execute(select(DailyPlan.plan_date).join(DailyPlanItem).where(DailyPlan.user_id == parsed, DailyPlanItem.status == "completed").distinct())).scalars())
        first_candidates = [item for item in [await self.db.scalar(select(func.min(LearningSession.started_at)).where(LearningSession.user_id == parsed)), await self.db.scalar(select(func.min(ExerciseAttempt.created_at)).where(ExerciseAttempt.user_id == parsed))] if item]
        streak = await GamificationService(self.db).get_streak_info(user_id)
        strongest = max(skills, key=lambda item: item.mastery_score) if skills else None
        weakest = min(skills, key=lambda item: item.mastery_score) if skills else None
        return {
            "total_skills_tracked": len(skills), "skills_mastered": sum(score >= .8 for score in scores),
            "skills_in_progress": sum(.3 <= score < .8 for score in scores), "skills_not_started": sum(score < .3 for score in scores),
            "average_mastery": round(sum(scores) / len(scores), 4) if scores else 0,
            "strongest_skill": {"name": strongest.skill.name, "mastery": strongest.mastery_score} if strongest else None,
            "weakest_skill": {"name": weakest.skill.name, "mastery": weakest.mastery_score} if weakest else None,
            "total_study_minutes": total_minutes, "total_exercises_completed": completed_exercises,
            "total_assessments_completed": assessments, "roadmap_progress": round(complete_roadmap / total_roadmap * 100, 1) if total_roadmap else 0,
            "days_learning": max(0, (datetime.now(timezone.utc).date() - min(first_candidates).date()).days + 1) if first_candidates else 0,
            "active_days": len(activity_dates), "current_streak": streak["current_streak"], "longest_streak": streak["longest_streak"],
        }

    async def _period_metrics(self, user_id: str, start: datetime, end: datetime) -> dict[str, object]:
        parsed = self._parse_uuid(user_id)
        histories = list((await self.db.execute(select(SkillHistory).join(UserSkill).where(UserSkill.user_id == parsed, SkillHistory.recorded_at < end).order_by(SkillHistory.user_skill_id, SkillHistory.recorded_at))).scalars())
        gained = 0.0; previous: dict[uuid.UUID, float] = {}
        for entry in histories:
            old = previous.get(entry.user_skill_id)
            if old is not None and entry.recorded_at >= start: gained += max(0.0, entry.mastery_score - old)
            previous[entry.user_skill_id] = entry.mastery_score
        sessions = list((await self.db.execute(select(LearningSession).where(LearningSession.user_id == parsed, LearningSession.status == "completed", LearningSession.started_at >= start, LearningSession.started_at < end))).scalars())
        attempts = list((await self.db.execute(select(ExerciseAttempt).where(ExerciseAttempt.user_id == parsed, ExerciseAttempt.is_correct.is_not(None), ExerciseAttempt.created_at >= start, ExerciseAttempt.created_at < end))).scalars())
        active_dates = {item.started_at.date() for item in sessions} | {item.created_at.date() for item in attempts}
        return {"gained": gained, "active_days": len(active_dates), "exercises": len(attempts), "minutes": sum(int(item.duration_minutes or 0) for item in sessions)}

    async def get_learning_velocity(self, user_id: str, period_days: int = 14) -> dict[str, object]:
        now = datetime.now(timezone.utc); current_start = now - timedelta(days=period_days); previous_start = current_start - timedelta(days=period_days)
        current = await self._period_metrics(user_id, current_start, now); previous = await self._period_metrics(user_id, previous_start, current_start)
        active = int(current["active_days"]); current_rate = float(current["gained"]) / active if active else 0
        previous_active = int(previous["active_days"]); previous_rate = float(previous["gained"]) / previous_active if previous_active else 0
        comparison = ((current_rate - previous_rate) / previous_rate * 100) if previous_rate else (100.0 if current_rate else 0.0)
        trend = "increasing" if comparison > 10 else "decreasing" if comparison < -10 else "stable"
        parsed = self._parse_uuid(user_id)
        remaining_rows = (await self.db.execute(select(UserSkill.mastery_score).join(GoalSkill, GoalSkill.skill_id == UserSkill.skill_id).join(Goal).where(UserSkill.user_id == parsed, Goal.user_id == parsed, Goal.status == "active"))).scalars()
        remaining = sum(max(0.0, 1 - float(score)) for score in remaining_rows)
        weeks = round(remaining / (current_rate * 7)) if current_rate > 0 and remaining else None
        return {"mastery_gained_this_period": round(float(current["gained"]), 4), "mastery_per_active_day": round(current_rate, 4), "active_days_this_period": active, "exercises_per_day": round(int(current["exercises"]) / active, 2) if active else 0, "minutes_per_day": round(int(current["minutes"]) / active, 1) if active else 0, "velocity_trend": trend, "velocity_vs_last_period": round(comparison, 1), "estimated_goal_completion_weeks": weeks}

    async def get_skill_category_breakdown(self, user_id: str) -> list[dict[str, object]]:
        grouped: dict[str, list[UserSkill]] = defaultdict(list)
        for item in await self._user_skills(user_id): grouped[item.skill.category].append(item)
        result = []
        for category in ("programming", "data-science", "ml", "mathematics", "devops"):
            items = grouped.get(category, []); average = sum(item.mastery_score for item in items) / len(items) if items else 0
            result.append({"category": category, "average_mastery": round(average, 4), "mastery_percentage": round(average * 100), "skills_count": len(items), "skills_mastered": sum(item.mastery_score >= .8 for item in items), "skills": [{"name": item.skill.name, "mastery": item.mastery_score} for item in items]})
        return result

    async def get_activity_heatmap(self, user_id: str, weeks: int = 26) -> list[dict[str, object]]:
        parsed = self._parse_uuid(user_id); today = datetime.now(timezone.utc).date(); start = today - timedelta(days=weeks * 7 - 1)
        item_rows = (await self.db.execute(select(DailyPlan.plan_date, func.count(DailyPlanItem.id)).join(DailyPlanItem).where(DailyPlan.user_id == parsed, DailyPlanItem.status == "completed", DailyPlan.plan_date >= start).group_by(DailyPlan.plan_date))).all()
        minute_rows = (await self.db.execute(select(func.date(LearningSession.started_at), func.sum(LearningSession.duration_minutes)).where(LearningSession.user_id == parsed, LearningSession.status == "completed", LearningSession.started_at >= datetime.combine(start, time.min, timezone.utc)).group_by(func.date(LearningSession.started_at)))).all()
        counts = {day: int(value) for day, value in item_rows}; minutes = {day: int(value or 0) for day, value in minute_rows}
        result = []
        for index in range(weeks * 7):
            day = start + timedelta(days=index); count, duration = counts.get(day, 0), minutes.get(day, 0)
            intensity = 4 if count >= 7 or duration >= 90 else 3 if count >= 5 or duration >= 60 else 2 if count >= 3 or duration >= 30 else 1 if count or duration else 0
            result.append({"date": day, "completed_items": count, "study_minutes": duration, "intensity": intensity})
        return result

    async def get_skill_breakdown_table(self, user_id: str) -> list[dict[str, object]]:
        parsed, skills = self._parse_uuid(user_id), await self._user_skills(user_id)
        priorities = dict((await self.db.execute(select(GoalSkill.skill_id, GoalSkill.priority_order).join(Goal).where(Goal.user_id == parsed, Goal.status == "active"))).all())
        now = datetime.now(timezone.utc); scheduler = SpacedRepetitionScheduler(); result = []
        for item in skills:
            recent = [entry for entry in item.history if entry.recorded_at >= now - timedelta(days=7)]
            baseline = min(recent, key=lambda entry: entry.recorded_at).mastery_score if recent else item.mastery_score
            change = float(item.mastery_score - baseline); days_ago = (now.date() - item.last_practiced_at.date()).days if item.last_practiced_at else None
            score = float(item.mastery_score); level = "Mastered" if score >= .85 else "Advanced" if score >= .7 else "Developing" if score >= .45 else "Beginner" if score >= .2 else "Not Started"
            review_due = bool(item.last_practiced_at and days_ago is not None and days_ago >= scheduler.get_review_interval_days(score))
            result.append({"skill_id": str(item.skill_id), "skill_name": item.skill.name, "skill_slug": item.skill.slug, "category": item.skill.category, "mastery_score": score, "mastery_percentage": round(score * 100), "mastery_level": level, "times_practiced": item.times_practiced, "times_correct": item.times_correct, "accuracy_rate": round(item.times_correct / max(1, item.times_correct + item.times_incorrect) * 100, 1), "last_practiced_days_ago": days_ago, "mastery_7d_change": round(change, 4), "mastery_trend": "new" if not item.history else "up" if change > .005 else "down" if change < -.005 else "stable", "review_due": review_due, "priority": priorities.get(item.skill_id, 9999)})
        result.sort(key=lambda entry: (int(entry.pop("priority")), -float(entry["mastery_score"])))
        return result

    async def get_time_distribution(self, user_id: str, days: int = 30) -> dict[str, object]:
        parsed = self._parse_uuid(user_id); start = datetime.now(timezone.utc) - timedelta(days=days)
        sessions = list((await self.db.execute(select(LearningSession).where(LearningSession.user_id == parsed, LearningSession.status == "completed", LearningSession.started_at >= start))).scalars())
        hours = [0] * 24; weekdays = [0] * 7; grid = [[0] * 24 for _ in range(7)]
        for session in sessions:
            duration = int(session.duration_minutes or 0); hours[session.started_at.hour] += duration; weekdays[session.started_at.weekday()] += duration; grid[session.started_at.weekday()][session.started_at.hour] += duration
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        durations = [int(item.duration_minutes or 0) for item in sessions]
        return {"by_hour": [{"hour": index, "minutes": value} for index, value in enumerate(hours)], "by_day_of_week": [{"day": names[index], "minutes": value} for index, value in enumerate(weekdays)], "peak_study_hour": max(range(24), key=hours.__getitem__) if sessions else 0, "peak_study_day": names[max(range(7), key=weekdays.__getitem__)] if sessions else "No activity", "morning_learner": sum(hours[6:12]) > sum(hours[12:]), "average_session_minutes": round(sum(durations) / len(durations), 1) if durations else 0, "longest_session_minutes": max(durations, default=0), "grid": [{"day": names[day], "hour": hour, "minutes": grid[day][hour]} for day in range(7) for hour in range(24)]}

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID:
        try: return uuid.UUID(value)
        except ValueError as exc: raise HTTPException(status_code=422, detail="Invalid identifier") from exc
