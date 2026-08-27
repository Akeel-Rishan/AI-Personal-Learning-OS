"""Generate and manage timezone-aware daily learning plans."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from openai import APIError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gamification import XPEvent
from app.models.learning import DailyPlan, DailyPlanItem, LearningSession
from app.models.progress import UserSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.user import User
from app.schemas.plan import (
    DailyPlanItemResponse,
    DailyPlanResponse,
    PlanCompletionSummary,
    PlanHistoryItem,
    StreakResponse,
)
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable
from app.services.roadmap_service import RoadmapService
from app.services.spaced_repetition import SpacedRepetitionScheduler


XP_VALUES = {"lesson": 20, "exercise": 30, "review": 15, "assessment": 50, "practice": 25, "project": 40}
STREAK_XP = {7: 100, 14: 200, 30: 500}


class PlanService:
    """Create focused daily work and keep roadmap, mastery, streak, and XP state aligned."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIService()
        self.sr_scheduler = SpacedRepetitionScheduler()

    async def get_or_create_today_plan(self, user_id: str) -> DailyPlan:
        existing = await self.get_today_plan(user_id)
        return existing if existing is not None else await self.generate_today_plan(user_id)

    async def generate_today_plan(self, user_id: str, force: bool = False) -> DailyPlan:
        parsed_user = self._parse_uuid(user_id)
        user_result = await self.db.execute(
            select(User).options(selectinload(User.profile)).where(User.id == parsed_user)
        )
        user = user_result.scalars().one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        plan_date = self._local_now(user.profile.timezone if user.profile else "UTC").date()
        existing = await self.get_plan_by_date(user_id, plan_date)
        if existing is not None:
            if not force:
                return existing
            if any(item.status == "completed" for item in existing.items):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A started plan cannot be regenerated")
            await self.db.delete(existing)
            await self.db.flush()

        roadmap_result = await self.db.execute(
            select(Roadmap)
            .options(
                selectinload(Roadmap.goal),
                selectinload(Roadmap.phases)
                .selectinload(RoadmapPhase.items)
                .selectinload(RoadmapItem.skill),
            )
            .where(Roadmap.user_id == parsed_user, Roadmap.status == "active")
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        roadmap = roadmap_result.scalars().unique().one_or_none()
        if roadmap is None:
            raise HTTPException(status_code=404, detail="Set up a goal and roadmap first")
        active_phase = next((phase for phase in roadmap.phases if phase.status == "active"), None)
        if active_phase is None:
            raise HTTPException(status_code=404, detail="No active roadmap phase is available")

        daily_minutes = max(15, user.profile.daily_study_minutes if user.profile else roadmap.goal.daily_study_minutes)
        roadmap_items = [
            item for item in sorted(active_phase.items, key=lambda entry: entry.order_index)
            if item.status in {"pending", "active"}
        ]
        skill_result = await self.db.execute(
            select(UserSkill).options(selectinload(UserSkill.skill)).where(UserSkill.user_id == parsed_user)
        )
        user_skills = list(skill_result.scalars())
        due_reviews = self.sr_scheduler.get_skills_due_for_review(
            [
                {
                    "skill_id": str(entry.skill_id),
                    "skill_name": entry.skill.name,
                    "mastery_score": entry.mastery_score,
                    "last_practiced_at": entry.last_practiced_at,
                    "times_practiced": entry.times_practiced,
                }
                for entry in user_skills
            ]
        )

        selected: list[dict[str, Any]] = []
        used = 0
        learning_budget = math.floor(daily_minutes * 0.60)
        for item in roadmap_items:
            minutes = max(5, item.estimated_minutes or 30)
            if used + minutes <= learning_budget:
                selected.append(self._roadmap_plan_item(item, minutes))
                used += minutes
        if not selected and roadmap_items:
            first = roadmap_items[0]
            minutes = min(daily_minutes, max(5, first.estimated_minutes or 30))
            selected.append(self._roadmap_plan_item(first, minutes))
            used += minutes

        review_budget = math.floor(daily_minutes * 0.25)
        review_used = 0
        selected_skills = {str(item.get("skill_id")) for item in selected}
        for review in due_reviews:
            if str(review["skill_id"]) in selected_skills:
                continue
            estimated_review_minutes = self.sr_scheduler.estimate_review_time_minutes(
                str(review["review_type"]), float(review["mastery_score"])
            )
            remaining_review_minutes = review_budget - review_used
            remaining_daily_minutes = daily_minutes - used
            minutes = min(estimated_review_minutes, remaining_review_minutes, remaining_daily_minutes)
            if minutes >= 5:
                selected.append(
                    {
                        "roadmap_item_id": None,
                        "skill_id": review["skill_id"],
                        "title": f"Review: {review['skill_name']}",
                        "description": f"A {review['review_type'].replace('_', ' ')} scheduled from your estimated retention.",
                        "item_type": "review",
                        "estimated_minutes": minutes,
                    }
                )
                review_used += minutes
                used += minutes

        practice_budget = math.floor(daily_minutes * 0.15)
        if practice_budget >= 20 and used + 20 <= daily_minutes and selected:
            anchor = selected[0]
            selected.append(
                {
                    "roadmap_item_id": None,
                    "skill_id": anchor.get("skill_id"),
                    "title": f"Practice: {anchor.get('skill_name') or 'today’s focus'}",
                    "description": "Apply today's concepts without step-by-step guidance.",
                    "item_type": "practice",
                    "estimated_minutes": 20,
                }
            )
            used += 20
        if not selected:
            raise HTTPException(status_code=404, detail="No learning items are available for today")

        streak = await self.get_streak_count(user_id)
        note = await self.generate_ai_daily_note(
            user.full_name.split()[0], selected, used, streak, roadmap.goal.title
        )
        plan = DailyPlan(
            user_id=parsed_user,
            plan_date=plan_date,
            status="pending",
            total_estimated_minutes=used,
            actual_minutes_spent=0,
            ai_generated_note=note,
        )
        self.db.add(plan)
        await self.db.flush()
        for index, item in enumerate(selected):
            self.db.add(
                DailyPlanItem(
                    daily_plan_id=plan.id,
                    order_index=index,
                    status="pending",
                    **{key: value for key, value in item.items() if key != "skill_name"},
                )
            )
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raced = await self.get_plan_by_date(user_id, plan_date)
            if raced is not None:
                return raced
            raise
        created = await self.get_plan_by_date(user_id, plan_date)
        assert created is not None
        return created

    async def generate_ai_daily_note(
        self,
        user_name: str,
        plan_items: list[dict[str, Any]],
        total_minutes: int,
        current_streak: int,
        goal_title: str,
    ) -> str:
        titles = [str(item["title"]) for item in plan_items]
        fallback = f"Today you'll spend {total_minutes} minutes on {titles[0]} and {max(0, len(titles) - 1)} more task{'s' if len(titles) != 2 else ''}. Keep building deliberately toward {goal_title}."
        try:
            result = await self.ai.generate_structured(
                instructions=(
                    "You are a supportive learning coach. Write a warm, specific two-sentence daily note. "
                    "Avoid generic encouragement and return strict JSON."
                ),
                prompt=(
                    f"Learner: {user_name}\nGoal: {goal_title}\nTasks: {', '.join(titles)}\n"
                    f"Planned time: {total_minutes} minutes\nCurrent streak: {current_streak} days"
                ),
                schema_name="daily_learning_note",
                schema={
                    "type": "object",
                    "properties": {"note": {"type": "string"}},
                    "required": ["note"],
                    "additionalProperties": False,
                },
                max_output_tokens=220,
            )
            note = str(result["note"]).strip()
            return note or fallback
        except (AIServiceUnavailable, AIServiceResponseError, APIError, KeyError, TypeError):
            return fallback

    async def get_plan_by_date(self, user_id: str, plan_date: date) -> DailyPlan | None:
        parsed = self._try_uuid(user_id)
        if parsed is None:
            return None
        result = await self.db.execute(
            self._plan_query().where(DailyPlan.user_id == parsed, DailyPlan.plan_date == plan_date)
        )
        return result.scalars().unique().one_or_none()

    async def get_today_plan(self, user_id: str) -> DailyPlan | None:
        timezone_name = await self._user_timezone(user_id)
        return await self.get_plan_by_date(user_id, self._local_now(timezone_name).date())

    async def get_plan_by_id(self, plan_id: str, user_id: str) -> DailyPlan | None:
        parsed_plan, parsed_user = self._try_uuid(plan_id), self._try_uuid(user_id)
        if parsed_plan is None or parsed_user is None:
            return None
        result = await self.db.execute(
            self._plan_query().where(DailyPlan.id == parsed_plan, DailyPlan.user_id == parsed_user)
        )
        return result.scalars().unique().one_or_none()

    async def update_plan_item_status(
        self,
        item_id: str,
        user_id: str,
        new_status: str,
        time_spent_minutes: int | None = None,
    ) -> DailyPlanItem:
        parsed_item, parsed_user = self._parse_uuid(item_id), self._parse_uuid(user_id)
        result = await self.db.execute(
            select(DailyPlanItem)
            .join(DailyPlan)
            .options(
                selectinload(DailyPlanItem.skill),
                selectinload(DailyPlanItem.roadmap_item),
                selectinload(DailyPlanItem.daily_plan).selectinload(DailyPlan.items),
            )
            .where(DailyPlanItem.id == parsed_item, DailyPlan.user_id == parsed_user)
        )
        item = result.scalars().unique().one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="Plan item not found")
        plan = item.daily_plan
        previous_status = item.status
        was_plan_completed = plan.status == "completed"
        now = datetime.now(timezone.utc)
        if new_status == "in_progress":
            for sibling in plan.items:
                if sibling.id != item.id and sibling.status == "in_progress":
                    sibling.status = "pending"
        item.status = new_status
        item.completed_at = now if new_status == "completed" else None

        if new_status == "completed" and previous_status != "completed":
            minutes = time_spent_minutes if time_spent_minutes is not None else item.estimated_minutes
            plan.actual_minutes_spent += max(0, minutes)
            self.db.add(
                LearningSession(
                    user_id=parsed_user,
                    roadmap_item_id=item.roadmap_item_id,
                    skill_id=item.skill_id,
                    session_type=item.item_type,
                    status="completed",
                    started_at=now - timedelta(minutes=max(0, minutes)),
                    ended_at=now,
                    duration_minutes=max(0, minutes),
                    notes=f"Daily plan item {item.id}",
                )
            )
            await self.award_xp(
                user_id,
                f"plan_item_{item.item_type}",
                XP_VALUES.get(item.item_type, 20),
                f"[plan:{plan.id}] Completed {item.title}",
            )
            if item.skill_id:
                mastery_result = await self.db.execute(
                    select(UserSkill).where(UserSkill.user_id == parsed_user, UserSkill.skill_id == item.skill_id)
                )
                user_skill = mastery_result.scalar_one_or_none()
                if user_skill:
                    user_skill.last_practiced_at = now
                    user_skill.times_practiced += 1
            if item.roadmap_item_id:
                await self._complete_linked_roadmap_item(item.roadmap_item_id)

        terminal = [entry.status in {"completed", "skipped"} for entry in plan.items]
        if terminal and all(entry.status == "completed" for entry in plan.items):
            plan.status = "completed"
        elif terminal and all(terminal):
            plan.status = "partial"
        elif any(entry.status != "pending" for entry in plan.items):
            plan.status = "in_progress"
        else:
            plan.status = "pending"

        if plan.status == "completed" and not was_plan_completed:
            await self.award_xp(user_id, "daily_plan_complete", 50, f"[plan:{plan.id}] Completed the full daily plan")
            await self.db.flush()
            streak = await self.get_streak_count(user_id)
            if streak in STREAK_XP:
                await self.award_xp(user_id, "streak_milestone", STREAK_XP[streak], f"[plan:{plan.id}] Reached a {streak}-day streak")
        await self.db.commit()
        refreshed = await self._get_item(item_id, user_id)
        assert refreshed is not None
        return refreshed

    async def get_plan_completion_summary(self, plan_id: str, user_id: str) -> PlanCompletionSummary:
        plan = await self.get_plan_by_id(plan_id, user_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.status != "completed":
            raise HTTPException(status_code=409, detail="Plan is not complete")
        xp = await self.db.scalar(
            select(func.coalesce(func.sum(XPEvent.xp_earned), 0)).where(
                XPEvent.user_id == plan.user_id,
                XPEvent.description.like(f"[plan:{plan.id}]%"),
            )
        )
        streak = await self.get_streak_count(user_id)
        skills = sorted({item.skill.name for item in plan.items if item.skill is not None})
        linked = {item.roadmap_item_id for item in plan.items if item.roadmap_item_id and item.status == "completed"}
        total_roadmap_items = await self.db.scalar(
            select(func.count(RoadmapItem.id))
            .join(RoadmapPhase)
            .join(Roadmap)
            .where(Roadmap.user_id == plan.user_id)
        )
        delta = len(linked) / total_roadmap_items * 100 if total_roadmap_items else 0.0
        return PlanCompletionSummary(
            total_items=len(plan.items),
            completed_items=sum(item.status == "completed" for item in plan.items),
            skipped_items=sum(item.status == "skipped" for item in plan.items),
            total_minutes_planned=plan.total_estimated_minutes,
            actual_minutes_spent=plan.actual_minutes_spent,
            skills_practiced=skills,
            xp_earned=int(xp or 0),
            streak_days=streak,
            is_new_streak_milestone=streak in STREAK_XP,
            roadmap_progress_delta=round(delta, 1),
            completion_message="Today's focused work is complete. Your roadmap is already reflecting the progress.",
        )

    async def get_streak_count(self, user_id: str) -> int:
        dates = await self._completed_plan_dates(user_id)
        today = self._local_now(await self._user_timezone(user_id)).date()
        cursor = today if today in dates else today - timedelta(days=1)
        streak = 0
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    async def get_streak_info(self, user_id: str) -> StreakResponse:
        dates = await self._completed_plan_dates(user_id)
        local_now = self._local_now(await self._user_timezone(user_id))
        ordered = sorted(dates)
        longest = running = 0
        previous: date | None = None
        for current in ordered:
            running = running + 1 if previous and current == previous + timedelta(days=1) else 1
            longest = max(longest, running)
            previous = current
        current_streak = await self.get_streak_count(user_id)
        return StreakResponse(
            current_streak=current_streak,
            longest_streak=longest,
            last_completed_date=max(dates) if dates else None,
            streak_at_risk=current_streak > 0 and local_now.hour >= 20 and local_now.date() not in dates,
        )

    async def get_plan_history(self, user_id: str, limit: int = 30) -> list[DailyPlan]:
        parsed = self._parse_uuid(user_id)
        result = await self.db.execute(
            self._plan_query().where(DailyPlan.user_id == parsed).order_by(DailyPlan.plan_date.desc()).limit(limit)
        )
        return list(result.scalars().unique())

    async def get_user_total_xp(self, user_id: str) -> int:
        value = await self.db.scalar(
            select(func.coalesce(func.sum(XPEvent.xp_earned), 0)).where(XPEvent.user_id == self._parse_uuid(user_id))
        )
        return int(value or 0)

    async def award_xp(self, user_id: str, event_type: str, xp_amount: int, description: str) -> XPEvent:
        event = XPEvent(
            user_id=self._parse_uuid(user_id),
            event_type=event_type,
            xp_earned=xp_amount,
            description=description[:300],
        )
        self.db.add(event)
        return event

    @classmethod
    def serialize_plan(cls, plan: DailyPlan) -> DailyPlanResponse:
        items = [cls.serialize_item(item) for item in sorted(plan.items, key=lambda entry: entry.order_index)]
        completed = sum(item.status == "completed" for item in plan.items)
        return DailyPlanResponse(
            id=str(plan.id),
            plan_date=plan.plan_date,
            status=plan.status,
            total_estimated_minutes=plan.total_estimated_minutes,
            actual_minutes_spent=plan.actual_minutes_spent,
            ai_generated_note=plan.ai_generated_note,
            items=items,
            completed_items_count=completed,
            total_items_count=len(items),
            completion_percentage=round(completed / len(items) * 100, 1) if items else 0.0,
        )

    @staticmethod
    def serialize_item(item: DailyPlanItem) -> DailyPlanItemResponse:
        return DailyPlanItemResponse(
            id=str(item.id), title=item.title, description=item.description,
            item_type=item.item_type, order_index=item.order_index,
            estimated_minutes=item.estimated_minutes, status=item.status,
            skill_id=str(item.skill_id) if item.skill_id else None,
            skill_name=item.skill.name if item.skill else None,
            roadmap_item_id=str(item.roadmap_item_id) if item.roadmap_item_id else None,
            completed_at=item.completed_at,
        )

    @classmethod
    def serialize_history(cls, plan: DailyPlan) -> PlanHistoryItem:
        completed = sum(item.status == "completed" for item in plan.items)
        return PlanHistoryItem(
            id=str(plan.id), plan_date=plan.plan_date, status=plan.status,
            completion_percentage=round(completed / len(plan.items) * 100, 1) if plan.items else 0,
            total_minutes_planned=plan.total_estimated_minutes,
            actual_minutes_spent=plan.actual_minutes_spent, items_count=len(plan.items),
        )

    async def _complete_linked_roadmap_item(self, roadmap_item_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(RoadmapItem)
            .options(
                selectinload(RoadmapItem.phase).selectinload(RoadmapPhase.items),
                selectinload(RoadmapItem.phase).selectinload(RoadmapPhase.roadmap).selectinload(Roadmap.phases),
            )
            .where(RoadmapItem.id == roadmap_item_id)
        )
        roadmap_item = result.scalars().unique().one_or_none()
        if roadmap_item is None:
            return
        now = datetime.now(timezone.utc)
        roadmap_item.status, roadmap_item.completed_at = "completed", now
        phase = roadmap_item.phase
        if phase.items and all(item.status in {"completed", "skipped"} for item in phase.items):
            phase.status, phase.completed_at = "completed", now
            await RoadmapService(self.db).unlock_next_phase(phase.roadmap)

    async def _get_item(self, item_id: str, user_id: str) -> DailyPlanItem | None:
        result = await self.db.execute(
            select(DailyPlanItem)
            .join(DailyPlan)
            .options(selectinload(DailyPlanItem.skill), selectinload(DailyPlanItem.roadmap_item))
            .where(DailyPlanItem.id == self._parse_uuid(item_id), DailyPlan.user_id == self._parse_uuid(user_id))
        )
        return result.scalars().unique().one_or_none()

    async def _completed_plan_dates(self, user_id: str) -> set[date]:
        result = await self.db.execute(
            select(DailyPlan.plan_date).where(
                DailyPlan.user_id == self._parse_uuid(user_id), DailyPlan.status == "completed"
            )
        )
        return set(result.scalars())

    async def _user_timezone(self, user_id: str) -> str:
        result = await self.db.execute(
            select(User).options(selectinload(User.profile)).where(User.id == self._parse_uuid(user_id))
        )
        user = result.scalars().one_or_none()
        return user.profile.timezone if user and user.profile else "UTC"

    @staticmethod
    def _local_now(timezone_name: str) -> datetime:
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            zone = timezone.utc
        return datetime.now(timezone.utc).astimezone(zone)

    @staticmethod
    def _roadmap_plan_item(item: RoadmapItem, minutes: int) -> dict[str, Any]:
        return {
            "roadmap_item_id": item.id,
            "skill_id": item.skill_id,
            "skill_name": item.skill.name if item.skill else None,
            "title": item.title,
            "description": item.description,
            "item_type": item.item_type if item.item_type in XP_VALUES else "lesson",
            "estimated_minutes": minutes,
        }

    @staticmethod
    def _plan_query():
        return select(DailyPlan).options(
            selectinload(DailyPlan.items).selectinload(DailyPlanItem.skill),
            selectinload(DailyPlan.items).selectinload(DailyPlanItem.roadmap_item),
        )

    @staticmethod
    def _try_uuid(value: str | None) -> uuid.UUID | None:
        try:
            return uuid.UUID(value) if value else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _parse_uuid(cls, value: str) -> uuid.UUID:
        parsed = cls._try_uuid(value)
        if parsed is None:
            raise HTTPException(status_code=400, detail="Invalid identifier")
        return parsed
