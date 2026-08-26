"""Read-only skill catalog and prerequisite graph endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillCategoryResponse, SkillResponse, SkillWithPrerequisitesResponse


router = APIRouter()


@router.get("/", response_model=list[SkillResponse])
async def list_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(default=None, max_length=100),
    search: str | None = Query(default=None, max_length=100),
) -> list[SkillResponse]:
    """List active skills with optional category and name filtering."""

    statement = select(Skill).where(Skill.is_active.is_(True))
    if category:
        statement = statement.where(func.lower(Skill.category) == category.strip().lower())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Skill.name.ilike(term), Skill.slug.ilike(term)))
    result = await db.execute(statement.order_by(Skill.category, Skill.difficulty_level, Skill.name))
    return [SkillResponse.model_validate(skill) for skill in result.scalars().all()]


@router.get("/categories", response_model=list[SkillCategoryResponse])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SkillCategoryResponse]:
    """Return active skill counts grouped by category."""

    result = await db.execute(
        select(Skill.category, func.count(Skill.id))
        .where(Skill.is_active.is_(True))
        .group_by(Skill.category)
        .order_by(Skill.category)
    )
    return [SkillCategoryResponse(category=category, count=count) for category, count in result.all()]


@router.get("/{skill_id}", response_model=SkillWithPrerequisitesResponse)
async def get_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SkillWithPrerequisitesResponse:
    """Return a skill and its direct prerequisites."""

    result = await db.execute(
        select(Skill).options(selectinload(Skill.prerequisites)).where(Skill.id == skill_id)
    )
    skill = result.scalars().unique().one_or_none()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return SkillWithPrerequisitesResponse(
        **SkillResponse.model_validate(skill).model_dump(),
        prerequisites=[SkillResponse.model_validate(item) for item in skill.prerequisites],
    )
