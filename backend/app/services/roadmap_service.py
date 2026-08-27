"""Generate and manage graph-aware personalized learning roadmaps."""

from __future__ import annotations

import json
import math
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from openai import APIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.goal import Goal, GoalSkill
from app.models.progress import UserSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.skill import Skill
from app.schemas.roadmap import (
    PhaseProgressResponse,
    RoadmapItemResponse,
    RoadmapItemUpdateResponse,
    RoadmapPhaseResponse,
    RoadmapProgressResponse,
    RoadmapResponse,
)
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable


class RoadmapService:
    """Roadmap generation, ownership, progression, and adaptation operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIService()

    async def generate_roadmap(self, user_id: str, goal_id: str) -> Roadmap:
        existing = await self.get_roadmap_by_goal(goal_id, user_id)
        if existing is not None:
            return existing
        parsed_user = self._parse_uuid(user_id)
        parsed_goal = self._parse_uuid(goal_id)
        result = await self.db.execute(
            select(Goal)
            .options(
                selectinload(Goal.goal_skills)
                .selectinload(GoalSkill.skill)
                .selectinload(Skill.prerequisites)
            )
            .where(Goal.id == parsed_goal, Goal.user_id == parsed_user)
        )
        goal = result.scalars().unique().one_or_none()
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        links = sorted(goal.goal_skills, key=lambda link: link.priority_order)
        if not links:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Generate the goal skill plan first")

        skill_ids = [link.skill_id for link in links]
        mastery_rows = await self.db.execute(
            select(UserSkill).where(UserSkill.user_id == parsed_user, UserSkill.skill_id.in_(skill_ids))
        )
        mastery = {str(row.skill_id): row.mastery_score for row in mastery_rows.scalars()}
        skills = [self._skill_dict(link.skill, link.priority_order) for link in links]
        included = {str(link.skill_id) for link in links}
        prerequisites = {
            str(link.skill_id): [str(item.id) for item in link.skill.prerequisites if str(item.id) in included]
            for link in links
        }
        ordered = self.topological_sort_skills(skills, prerequisites)
        phases = self.group_skills_into_phases(ordered, mastery, goal.daily_study_minutes)
        total_weeks = sum(phase["estimated_weeks"] for phase in phases)
        metadata = await self.generate_roadmap_metadata(
            phases, goal.title, mastery, goal.daily_study_minutes, total_weeks
        )

        now = datetime.now(timezone.utc)
        roadmap = Roadmap(
            user_id=parsed_user,
            goal_id=parsed_goal,
            status="active",
            total_phases=len(phases),
            current_phase_index=0,
            estimated_weeks=total_weeks,
            ai_generated_summary=metadata["summary"],
        )
        self.db.add(roadmap)
        await self.db.flush()
        for phase_index, phase_data in enumerate(phases):
            phase_meta = metadata["phases"][phase_index]
            phase = RoadmapPhase(
                roadmap_id=roadmap.id,
                title=phase_meta["title"],
                description=phase_meta["description"],
                order_index=phase_index,
                status="active" if phase_index == 0 else "locked",
                estimated_weeks=phase_data["estimated_weeks"],
                started_at=now if phase_index == 0 else None,
            )
            self.db.add(phase)
            await self.db.flush()
            item_index = 0
            for skill in phase_data["skills"]:
                for item in self.generate_items_for_skill(
                    skill, mastery.get(str(skill["skill_id"]), 0.0), phase_index
                ):
                    self.db.add(
                        RoadmapItem(
                            phase_id=phase.id,
                            skill_id=self._parse_uuid(str(skill["skill_id"])),
                            order_index=item_index,
                            status="pending",
                            **item,
                        )
                    )
                    item_index += 1
        await self.db.commit()
        created = await self.get_roadmap_by_goal(goal_id, user_id)
        if created is None:
            raise HTTPException(status_code=500, detail="Roadmap was not saved")
        return created

    @staticmethod
    def topological_sort_skills(
        skills: list[dict[str, Any]],
        prerequisites: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        """Use stable Kahn ordering and append cyclic nodes in their original order."""

        skill_by_id = {str(skill.get("skill_id", skill.get("id"))): skill for skill in skills}
        order = {skill_id: index for index, skill_id in enumerate(skill_by_id)}
        in_degree = {skill_id: 0 for skill_id in skill_by_id}
        dependents: dict[str, list[str]] = defaultdict(list)
        for skill_id in skill_by_id:
            for prerequisite in prerequisites.get(skill_id, []):
                if prerequisite in skill_by_id and prerequisite != skill_id:
                    in_degree[skill_id] += 1
                    dependents[prerequisite].append(skill_id)
        queue = deque(sorted((key for key, value in in_degree.items() if value == 0), key=order.get))
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        while queue:
            skill_id = queue.popleft()
            if skill_id in seen:
                continue
            seen.add(skill_id)
            result.append(skill_by_id[skill_id])
            for dependent in sorted(dependents[skill_id], key=order.get):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        result.extend(skill_by_id[skill_id] for skill_id in skill_by_id if skill_id not in seen)
        return result

    def group_skills_into_phases(
        self,
        ordered_skills: list[dict[str, Any]],
        user_mastery: dict[str, float],
        daily_minutes: int,
    ) -> list[dict[str, Any]]:
        weekly_minutes = max(105, daily_minutes * 7)
        maximum_minutes = weekly_minutes * 3
        phases: list[dict[str, Any]] = []
        current: list[dict[str, Any]] = []
        current_minutes = 0
        for skill in ordered_skills:
            mastery = user_mastery.get(str(skill["skill_id"]), 0.0)
            minutes = sum(item["estimated_minutes"] for item in self.generate_items_for_skill(skill, mastery, len(phases)))
            category_changed = current and current[-1]["category"] != skill["category"]
            should_split = len(current) >= 5 or (current_minutes + minutes > maximum_minutes) or (category_changed and len(current) >= 3)
            if should_split:
                phases.append(self._phase_dict(current, current_minutes, weekly_minutes, len(phases)))
                current, current_minutes = [], 0
            current.append(skill)
            current_minutes += minutes
        if current:
            phases.append(self._phase_dict(current, current_minutes, weekly_minutes, len(phases)))
        return phases

    @staticmethod
    def generate_items_for_skill(
        skill: dict[str, Any], mastery_score: float, phase_index: int
    ) -> list[dict[str, Any]]:
        del phase_index
        name = str(skill["name"])
        description = str(skill.get("description") or f"Build practical confidence with {name}.")
        if mastery_score >= 0.75:
            templates = [("review", f"Refresh {name}", 15), ("assessment", f"Quick check: {name}", 10)]
        elif mastery_score >= 0.5:
            templates = [
                ("lesson", f"Focused lesson: {name}", 30),
                ("exercise", f"Practice {name} I", 20),
                ("exercise", f"Practice {name} II", 20),
                ("assessment", f"Skill check: {name}", 15),
            ]
        else:
            templates = [
                ("lesson", f"{name} foundations", 30),
                ("lesson", f"Applied {name}", 30),
                ("exercise", f"Guided {name} practice", 20),
                ("exercise", f"Independent {name} practice", 20),
                ("exercise", f"Challenge: {name}", 20),
                ("project", f"Mini project: {name}", 45),
                ("assessment", f"Mastery check: {name}", 20),
            ]
        return [
            {
                "item_type": item_type,
                "title": title,
                "description": f"{description} This {item_type} is tailored to your current mastery level.",
                "estimated_minutes": minutes,
            }
            for item_type, title, minutes in templates
        ]

    async def generate_roadmap_metadata(
        self,
        phases: list[dict[str, Any]],
        goal_title: str,
        user_mastery: dict[str, float],
        daily_minutes: int,
        total_weeks: int,
    ) -> dict[str, Any]:
        fallback = {
            "summary": f"Your {total_weeks}-week path toward {goal_title} follows prerequisites first and adjusts depth to your assessment results.",
            "phases": [
                {
                    "title": phase["title"],
                    "description": phase["description"],
                }
                for phase in phases
            ],
        }
        count = len(phases)
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "phases": {
                    "type": "array",
                    "minItems": count,
                    "maxItems": count,
                    "items": {
                        "type": "object",
                        "properties": {"title": {"type": "string"}, "description": {"type": "string"}},
                        "required": ["title", "description"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["summary", "phases"],
            "additionalProperties": False,
        }
        try:
            payload = await self.ai.generate_structured(
                instructions=(
                    "You are an expert curriculum designer. Write motivating, concise phase names and "
                    "descriptions without changing phase order or skill membership. Return strict JSON."
                ),
                prompt=(
                    f"Goal: {goal_title}\nDaily study minutes: {daily_minutes}\nTotal weeks: {total_weeks}\n"
                    f"Mastery by skill: {json.dumps(user_mastery)}\nPhases: {json.dumps(phases, default=str)}"
                ),
                schema_name="personalized_roadmap_metadata",
                schema=schema,
                max_output_tokens=1800,
            )
            if not isinstance(payload, dict) or len(payload.get("phases", [])) != count:
                return fallback
            return payload
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TypeError, ValueError):
            return fallback

    async def get_roadmap_by_goal(self, goal_id: str, user_id: str) -> Roadmap | None:
        parsed_goal, parsed_user = self._try_uuid(goal_id), self._try_uuid(user_id)
        if parsed_goal is None or parsed_user is None:
            return None
        result = await self.db.execute(
            self._roadmap_query().where(Roadmap.goal_id == parsed_goal, Roadmap.user_id == parsed_user)
        )
        return result.scalars().unique().one_or_none()

    async def get_roadmap_by_id(self, roadmap_id: str, user_id: str) -> Roadmap | None:
        parsed_roadmap, parsed_user = self._try_uuid(roadmap_id), self._try_uuid(user_id)
        if parsed_roadmap is None or parsed_user is None:
            return None
        result = await self.db.execute(
            self._roadmap_query().where(Roadmap.id == parsed_roadmap, Roadmap.user_id == parsed_user)
        )
        return result.scalars().unique().one_or_none()

    async def update_item_status(self, item_id: str, user_id: str, new_status: str) -> RoadmapItemUpdateResponse:
        parsed_item, parsed_user = self._parse_uuid(item_id), self._parse_uuid(user_id)
        result = await self.db.execute(
            select(RoadmapItem)
            .join(RoadmapPhase).join(Roadmap)
            .options(selectinload(RoadmapItem.skill), selectinload(RoadmapItem.phase).selectinload(RoadmapPhase.items))
            .where(RoadmapItem.id == parsed_item, Roadmap.user_id == parsed_user)
        )
        item = result.scalars().unique().one_or_none()
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")
        now = datetime.now(timezone.utc)
        item.status = new_status
        item.completed_at = now if new_status == "completed" else None
        await self.db.flush()
        phase = item.phase
        done = sum(entry.status in {"completed", "skipped"} for entry in phase.items)
        unlocked: RoadmapPhase | None = None
        roadmap_result = await self.db.execute(self._roadmap_query().where(Roadmap.id == phase.roadmap_id))
        roadmap = roadmap_result.scalars().unique().one()
        if phase.items and done == len(phase.items):
            phase.status = "completed"
            phase.completed_at = now
            unlocked = await self.unlock_next_phase(roadmap)
        elif phase.status == "completed":
            phase.status, phase.completed_at = "active", None
            roadmap.current_phase_index = phase.order_index
        await self.db.commit()
        refreshed = await self.get_roadmap_by_id(str(roadmap.id), user_id)
        if refreshed is None:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        refreshed_phase = next(entry for entry in refreshed.phases if entry.id == phase.id)
        refreshed_item = next(entry for entry in refreshed_phase.items if entry.id == item.id)
        phase_done = sum(entry.status in {"completed", "skipped"} for entry in refreshed_phase.items)
        total = sum(len(entry.items) for entry in refreshed.phases)
        roadmap_done = sum(entry.status in {"completed", "skipped"} for entry in refreshed.phases for entry in entry.items)
        return RoadmapItemUpdateResponse(
            item=self.serialize_item(refreshed_item),
            phase_id=str(refreshed_phase.id),
            phase_status=refreshed_phase.status,
            phase_progress_percentage=round(phase_done / len(refreshed_phase.items) * 100, 1) if refreshed_phase.items else 0,
            roadmap_progress_percentage=round(roadmap_done / total * 100, 1) if total else 0,
            unlocked_phase_id=str(unlocked.id) if unlocked else None,
        )

    async def unlock_next_phase(self, roadmap: Roadmap) -> RoadmapPhase | None:
        current = sorted(roadmap.phases, key=lambda phase: phase.order_index)
        next_phase = next((phase for phase in current if phase.status == "locked"), None)
        if next_phase is None:
            roadmap.status = "completed"
            return None
        next_phase.status = "active"
        next_phase.started_at = datetime.now(timezone.utc)
        roadmap.current_phase_index = next_phase.order_index
        return next_phase

    async def calculate_roadmap_progress(self, roadmap_id: str, user_id: str | None = None) -> RoadmapProgressResponse:
        if user_id:
            roadmap = await self.get_roadmap_by_id(roadmap_id, user_id)
        else:
            parsed = self._try_uuid(roadmap_id)
            result = await self.db.execute(self._roadmap_query().where(Roadmap.id == parsed)) if parsed else None
            roadmap = result.scalars().unique().one_or_none() if result else None
        if roadmap is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
        total = sum(len(phase.items) for phase in roadmap.phases)
        completed = sum(item.status in {"completed", "skipped"} for phase in roadmap.phases for item in phase.items)
        remaining_minutes = sum(
            item.estimated_minutes or 0 for phase in roadmap.phases for item in phase.items
            if item.status not in {"completed", "skipped"}
        )
        daily = max(15, roadmap.goal.daily_study_minutes)
        completion_date = (datetime.now(timezone.utc) + timedelta(days=math.ceil(remaining_minutes / daily))).date() if remaining_minutes else datetime.now(timezone.utc).date()
        active = next((phase for phase in roadmap.phases if phase.status == "active"), None)
        return RoadmapProgressResponse(
            total_items=total,
            completed_items=completed,
            overall_percentage=round(completed / total * 100, 1) if total else 0,
            current_phase=active.title if active else None,
            estimated_completion_date=completion_date,
            phases=[
                PhaseProgressResponse(
                    phase_id=str(phase.id), title=phase.title, status=phase.status,
                    progress=round(sum(item.status in {"completed", "skipped"} for item in phase.items) / len(phase.items) * 100, 1) if phase.items else 0,
                ) for phase in roadmap.phases
            ],
        )

    async def adapt_roadmap(self, roadmap_id: str, user_id: str) -> Roadmap:
        roadmap = await self.get_roadmap_by_id(roadmap_id, user_id)
        if roadmap is None:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        active = next((phase for phase in roadmap.phases if phase.status == "active"), None)
        if active:
            skill_ids = [item.skill_id for item in active.items if item.skill_id]
            result = await self.db.execute(
                select(UserSkill).where(UserSkill.user_id == roadmap.user_id, UserSkill.skill_id.in_(skill_ids))
            )
            low_mastery = {entry.skill_id for entry in result.scalars() if entry.mastery_score < 0.5}
            for item in active.items:
                if item.skill_id in low_mastery and item.status == "completed":
                    item.status, item.completed_at = "pending", None
        roadmap.last_adapted_at = datetime.now(timezone.utc)
        await self.db.commit()
        refreshed = await self.get_roadmap_by_id(roadmap_id, user_id)
        assert refreshed is not None
        return refreshed

    @classmethod
    def serialize_roadmap(cls, roadmap: Roadmap) -> RoadmapResponse:
        phases = [cls.serialize_phase(phase) for phase in sorted(roadmap.phases, key=lambda entry: entry.order_index)]
        total = sum(phase.items_count for phase in phases)
        completed = sum(phase.completed_items_count for phase in phases)
        return RoadmapResponse(
            id=str(roadmap.id), goal_id=str(roadmap.goal_id), goal_title=roadmap.goal.title,
            goal_target_date=roadmap.goal.target_date, status=roadmap.status, total_phases=roadmap.total_phases,
            current_phase_index=roadmap.current_phase_index, estimated_weeks=roadmap.estimated_weeks,
            ai_generated_summary=roadmap.ai_generated_summary, phases=phases,
            overall_progress_percentage=round(completed / total * 100, 1) if total else 0,
            completed_items=completed, total_items=total, last_adapted_at=roadmap.last_adapted_at,
            created_at=roadmap.created_at,
        )

    @classmethod
    def serialize_phase(cls, phase: RoadmapPhase) -> RoadmapPhaseResponse:
        items = [cls.serialize_item(item) for item in sorted(phase.items, key=lambda entry: entry.order_index)]
        completed = sum(item.status in {"completed", "skipped"} for item in phase.items)
        return RoadmapPhaseResponse(
            id=str(phase.id), title=phase.title, description=phase.description, order_index=phase.order_index,
            status=phase.status, estimated_weeks=phase.estimated_weeks, started_at=phase.started_at,
            completed_at=phase.completed_at, items=items, items_count=len(items), completed_items_count=completed,
            progress_percentage=round(completed / len(items) * 100, 1) if items else 0,
        )

    @staticmethod
    def serialize_item(item: RoadmapItem) -> RoadmapItemResponse:
        return RoadmapItemResponse(
            id=str(item.id), title=item.title, description=item.description, item_type=item.item_type,
            order_index=item.order_index, status=item.status, estimated_minutes=item.estimated_minutes,
            skill_id=str(item.skill_id) if item.skill_id else None,
            skill_name=item.skill.name if item.skill else None, completed_at=item.completed_at,
        )

    @staticmethod
    def _skill_dict(skill: Skill, priority: int) -> dict[str, Any]:
        return {"skill_id": str(skill.id), "slug": skill.slug, "name": skill.name, "description": skill.description, "category": skill.category, "estimated_hours": skill.estimated_hours, "priority": priority}

    @staticmethod
    def _phase_dict(skills: list[dict[str, Any]], minutes: int, weekly: int, index: int) -> dict[str, Any]:
        category = str(skills[0]["category"]).replace("-", " ").title()
        weeks = min(3, max(1, math.ceil(minutes / weekly)))
        return {"title": f"Phase {index + 1}: {category}", "description": f"Build capability across {', '.join(str(skill['name']) for skill in skills)}.", "skills": list(skills), "estimated_weeks": weeks}

    @staticmethod
    def _roadmap_query():
        return select(Roadmap).options(
            selectinload(Roadmap.goal),
            selectinload(Roadmap.phases).selectinload(RoadmapPhase.items).selectinload(RoadmapItem.skill),
        )

    @staticmethod
    def _try_uuid(value: str | None) -> uuid.UUID | None:
        try:
            return uuid.UUID(value) if value else None
        except (ValueError, TypeError):
            return None

    @classmethod
    def _parse_uuid(cls, value: str) -> uuid.UUID:
        parsed = cls._try_uuid(value)
        if parsed is None:
            raise HTTPException(status_code=400, detail="Invalid identifier")
        return parsed
