"""Goal CRUD and AI-powered skill decomposition."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from openai import APIError
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.goal import Goal, GoalSkill
from app.models.skill import Skill
from app.schemas.goal import GoalCreateRequest, GoalDecomposeResponse, GoalSkillResponse
from app.schemas.skill import SkillResponse, SkillWithPrerequisitesResponse
from app.services.ai_service import AIService, AIServiceUnavailable


class GoalService:
    """Coordinate goal ownership, persistence, and generated curriculum data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIService()

    async def create_goal(self, user_id: str, data: GoalCreateRequest) -> Goal:
        """Create an active goal and pause any previous active goal."""

        parsed_user_id = self._parse_uuid(user_id)
        await self.db.execute(
            update(Goal)
            .where(Goal.user_id == parsed_user_id, Goal.status == "active")
            .values(status="paused")
        )
        goal = Goal(
            user_id=parsed_user_id,
            title=data.title,
            description=data.description,
            target_role=data.target_role,
            status="active",
            target_date=data.target_date,
            daily_study_minutes=data.daily_study_minutes,
            existing_knowledge=data.existing_knowledge,
            ai_warnings=[],
        )
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def get_user_goals(self, user_id: str) -> list[Goal]:
        """Return the current learner's goals newest first."""

        result = await self.db.execute(
            self._goal_query()
            .where(Goal.user_id == self._parse_uuid(user_id))
            .order_by(Goal.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_goal_by_id(self, goal_id: str, user_id: str) -> Goal | None:
        """Return a goal only when it belongs to the current learner."""

        parsed_goal_id = self._try_uuid(goal_id)
        parsed_user_id = self._try_uuid(user_id)
        if parsed_goal_id is None or parsed_user_id is None:
            return None
        result = await self.db.execute(
            self._goal_query().where(
                Goal.id == parsed_goal_id,
                Goal.user_id == parsed_user_id,
            )
        )
        return result.scalars().unique().one_or_none()

    async def get_active_goal(self, user_id: str) -> Goal | None:
        """Return the learner's most recent active goal."""

        parsed_user_id = self._try_uuid(user_id)
        if parsed_user_id is None:
            return None
        result = await self.db.execute(
            self._goal_query()
            .where(Goal.user_id == parsed_user_id, Goal.status == "active")
            .order_by(Goal.created_at.desc())
            .limit(1)
        )
        return result.scalars().unique().one_or_none()

    async def decompose_goal(
        self,
        goal_id: str,
        user_id: str,
        existing_knowledge: str,
    ) -> GoalDecomposeResponse:
        """Generate a curriculum, replace goal skills, and persist AI metadata."""

        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        result = await self.db.execute(
            select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.name)
        )
        skills = list(result.scalars().all())
        available_skills = [
            {
                "id": str(skill.id),
                "name": skill.name,
                "slug": skill.slug,
                "category": skill.category,
                "difficulty_level": skill.difficulty_level,
                "estimated_hours": skill.estimated_hours,
            }
            for skill in skills
        ]
        knowledge = existing_knowledge.strip() or goal.existing_knowledge
        try:
            decomposition = await self.ai.decompose_goal(
                goal_title=goal.title,
                existing_knowledge=knowledge,
                daily_minutes=goal.daily_study_minutes,
                target_date=goal.target_date.isoformat() if goal.target_date else None,
                available_skills=available_skills,
            )
        except AIServiceUnavailable as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        except APIError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI could not generate the roadmap right now. Please retry in a moment.",
            ) from exc

        skills_by_slug = {skill.slug: skill for skill in skills}
        await self.db.execute(delete(GoalSkill).where(GoalSkill.goal_id == goal.id))
        for item in decomposition["required_skills"]:
            selected_skill = skills_by_slug.get(str(item["slug"]))
            if selected_skill is None:
                continue
            self.db.add(
                GoalSkill(
                    goal_id=goal.id,
                    skill_id=selected_skill.id,
                    priority_order=int(item["priority_order"]),
                    is_required=bool(item["is_required"]),
                    reason=str(item.get("reason") or "Supports this learning goal"),
                )
            )
        goal.existing_knowledge = knowledge
        goal.ai_summary = str(decomposition["summary"])
        goal.estimated_weeks = int(decomposition["estimated_weeks"])
        goal.difficulty_assessment = str(decomposition["difficulty_assessment"])
        goal.ai_warnings = list(decomposition.get("warnings", []))
        await self.db.commit()

        refreshed = await self.get_goal_by_id(goal_id, user_id)
        if refreshed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return GoalDecomposeResponse(
            goal_id=str(refreshed.id),
            required_skills=self.serialize_goal_skills(refreshed),
            estimated_weeks=refreshed.estimated_weeks or 1,
            difficulty_assessment=refreshed.difficulty_assessment or "intermediate",
            summary=refreshed.ai_summary or "Your personalized path is ready.",
            recommended_daily_focus_minutes=int(
                decomposition.get("recommended_daily_focus_minutes", refreshed.daily_study_minutes)
            ),
            warnings=refreshed.ai_warnings or [],
        )

    async def get_goal_skills(self, goal_id: str, user_id: str) -> list[GoalSkillResponse]:
        """Return full ordered skill details for an owned goal."""

        goal = await self.get_goal_by_id(goal_id, user_id)
        return [] if goal is None else self.serialize_goal_skills(goal)

    async def update_status(self, goal_id: str, user_id: str, new_status: str) -> Goal | None:
        """Update an owned goal's lifecycle status."""

        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            return None
        if new_status == "active":
            await self.db.execute(
                update(Goal)
                .where(
                    Goal.user_id == goal.user_id,
                    Goal.id != goal.id,
                    Goal.status == "active",
                )
                .values(status="paused")
            )
        goal.status = new_status
        await self.db.commit()
        updated = await self.get_goal_by_id(goal_id, user_id)
        return updated

    async def update_goal(
        self,
        goal_id: str,
        user_id: str,
        data: GoalCreateRequest,
    ) -> Goal | None:
        """Update editable planning fields on an owned goal."""

        goal = await self.get_goal_by_id(goal_id, user_id)
        if goal is None:
            return None
        goal.title = data.title
        goal.description = data.description
        goal.target_role = data.target_role
        goal.target_date = data.target_date
        goal.daily_study_minutes = data.daily_study_minutes
        goal.existing_knowledge = data.existing_knowledge
        await self.db.commit()
        return await self.get_goal_by_id(goal_id, user_id)

    @staticmethod
    def serialize_goal_skills(goal: Goal) -> list[GoalSkillResponse]:
        """Convert eager-loaded ORM links into API-safe graph objects."""

        serialized: list[GoalSkillResponse] = []
        for link in sorted(goal.goal_skills, key=lambda item: item.priority_order):
            prerequisites = [SkillResponse.model_validate(item) for item in link.skill.prerequisites]
            skill = SkillWithPrerequisitesResponse(
                **SkillResponse.model_validate(link.skill).model_dump(),
                prerequisites=prerequisites,
            )
            serialized.append(
                GoalSkillResponse(
                    skill=skill,
                    priority_order=link.priority_order,
                    is_required=link.is_required,
                    reason=link.reason,
                )
            )
        return serialized

    @staticmethod
    def _goal_query():
        return select(Goal).options(
            selectinload(Goal.goal_skills)
            .selectinload(GoalSkill.skill)
            .selectinload(Skill.prerequisites)
        )

    @staticmethod
    def _try_uuid(value: str) -> uuid.UUID | None:
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _parse_uuid(cls, value: str) -> uuid.UUID:
        parsed = cls._try_uuid(value)
        if parsed is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid identifier")
        return parsed
