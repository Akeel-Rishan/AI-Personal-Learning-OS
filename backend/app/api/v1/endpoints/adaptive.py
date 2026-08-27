"""Authenticated adaptive-learning scans, gaps, notifications, and audit history."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.adaptive import AdaptationEvent, KnowledgeGap
from app.models.progress import UserSkill
from app.models.user import User
from app.schemas.adaptive import (
    AdaptationEventResponse,
    AdaptationScanResponse,
    DismissResponse,
    GapReportResponse,
    InterventionNotification,
    KnowledgeGapResponse,
    ManualAdaptationRequest,
)
from app.services.adaptive_engine import ACTIVE, AdaptiveEngine


router = APIRouter()


async def _serialize_gap(db: AsyncSession, gap: KnowledgeGap) -> KnowledgeGapResponse:
    mastery = await db.scalar(
        select(UserSkill.mastery_score).where(
            UserSkill.user_id == gap.user_id,
            UserSkill.skill_id == gap.skill_id,
        )
    )
    current = float(mastery or 0)
    detected = gap.detected_at
    if detected.tzinfo is None:
        detected = detected.replace(tzinfo=timezone.utc)
    return KnowledgeGapResponse(
        id=str(gap.id),
        skill_id=str(gap.skill_id),
        skill_name=gap.skill.name,
        skill_slug=gap.skill.slug,
        gap_type=gap.gap_type,
        gap_severity=gap.gap_severity,
        description=gap.description,
        misconception=gap.misconception,
        evidence=gap.evidence or {},
        status=gap.status,
        intervention_created=gap.intervention_created,
        intervention_items=gap.intervention_items,
        detected_at=gap.detected_at,
        mastery_at_detection=gap.mastery_at_detection,
        mastery_percentage_at_detection=round(gap.mastery_at_detection * 100),
        current_mastery=current,
        current_mastery_percentage=round(current * 100),
        days_active=max(0, (datetime.now(timezone.utc) - detected).days),
    )


def _serialize_event(event: AdaptationEvent) -> AdaptationEventResponse:
    return AdaptationEventResponse(
        id=str(event.id),
        skill_id=str(event.skill_id) if event.skill_id else None,
        skill_name=event.skill.name if event.skill else None,
        trigger_type=event.trigger_type,
        gap_type=event.gap_type,
        gap_severity=event.gap_severity,
        gap_description=event.gap_description,
        action_taken=event.action_taken,
        action_description=event.action_description,
        items_inserted=event.items_inserted,
        is_resolved=event.is_resolved,
        ai_reasoning=event.ai_reasoning,
        created_at=event.created_at,
    )


async def _owned_gap(db: AsyncSession, user_id: uuid.UUID, gap_id: str) -> KnowledgeGap:
    try:
        parsed = uuid.UUID(gap_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Knowledge gap not found") from exc
    gap = (
        await db.execute(
            select(KnowledgeGap)
            .options(selectinload(KnowledgeGap.skill))
            .where(KnowledgeGap.id == parsed, KnowledgeGap.user_id == user_id)
        )
    ).scalar_one_or_none()
    if gap is None:
        raise HTTPException(status_code=404, detail="Knowledge gap not found")
    return gap


@router.post("/scan", response_model=AdaptationScanResponse)
async def scan(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdaptationScanResponse:
    return AdaptationScanResponse(**await AdaptiveEngine(db).run_full_adaptation_scan(str(current_user.id)))


@router.post("/adapt", response_model=AdaptationScanResponse)
async def adapt(
    payload: ManualAdaptationRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdaptationScanResponse:
    return AdaptationScanResponse(
        **await AdaptiveEngine(db).trigger_manual_adaptation(str(current_user.id), payload.skill_id)
    )


@router.get("/gaps", response_model=GapReportResponse)
async def gaps(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[Literal["active", "resolved", "all"], Query()] = "active",
) -> GapReportResponse:
    rows = list(
        (
            await db.execute(
                select(KnowledgeGap)
                .options(selectinload(KnowledgeGap.skill))
                .where(KnowledgeGap.user_id == current_user.id)
                .order_by(KnowledgeGap.detected_at.desc())
            )
        ).scalars()
    )
    active_rows = [item for item in rows if item.status in ACTIVE]
    resolved_rows = [item for item in rows if item.status == "resolved"]
    if status == "active":
        resolved_for_response: list[KnowledgeGap] = []
    elif status == "resolved":
        active_rows, resolved_for_response = [], resolved_rows
    else:
        resolved_for_response = resolved_rows
    active = [await _serialize_gap(db, item) for item in active_rows]
    resolved = [await _serialize_gap(db, item) for item in resolved_for_response]
    durations = [
        (item.resolved_at - item.detected_at).total_seconds() / 86400
        for item in resolved_rows
        if item.resolved_at is not None
    ]
    skill_counts = Counter(item.skill.name for item in rows)
    return GapReportResponse(
        active_gaps=active,
        resolved_gaps=resolved,
        resolved_gaps_count=len(resolved_rows),
        total_gaps_ever=len(rows),
        most_problematic_skill=skill_counts.most_common(1)[0][0] if skill_counts else None,
        average_resolution_days=round(sum(durations) / len(durations), 1) if durations else None,
        gap_type_breakdown=dict(Counter(item.gap_type for item in rows)),
        severity_breakdown=dict(Counter(item.gap_severity for item in active_rows)),
    )


@router.get("/gaps/{gap_id}", response_model=KnowledgeGapResponse)
async def gap_detail(
    gap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeGapResponse:
    return await _serialize_gap(db, await _owned_gap(db, current_user.id, gap_id))


@router.post("/gaps/{gap_id}/acknowledge", response_model=KnowledgeGapResponse)
async def acknowledge_gap(
    gap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeGapResponse:
    gap = await _owned_gap(db, current_user.id, gap_id)
    if gap.status in ACTIVE:
        gap.status = "acknowledged"
    await db.commit()
    return await _serialize_gap(db, gap)


@router.get("/history", response_model=list[AdaptationEventResponse])
async def history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    skill_id: str | None = None,
) -> list[AdaptationEventResponse]:
    events = await AdaptiveEngine(db).get_adaptation_history(str(current_user.id), limit, skill_id)
    return [_serialize_event(item) for item in events]


@router.get("/notifications", response_model=list[InterventionNotification])
async def notifications(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InterventionNotification]:
    rows = list(
        (
            await db.execute(
                select(KnowledgeGap)
                .options(selectinload(KnowledgeGap.skill))
                .where(
                    KnowledgeGap.user_id == current_user.id,
                    KnowledgeGap.status.in_(ACTIVE),
                    KnowledgeGap.notification_dismissed.is_(False),
                )
                .order_by(KnowledgeGap.detected_at.desc())
            )
        ).scalars()
    )
    result: list[InterventionNotification] = []
    for gap in rows:
        data = gap.intervention_items or {}
        plan = data.get("plan") if isinstance(data.get("plan"), dict) else {}
        inserted = data.get("inserted_item_ids") if isinstance(data.get("inserted_item_ids"), list) else []
        result.append(
            InterventionNotification(
                gap_id=str(gap.id),
                skill_name=gap.skill.name,
                severity=gap.gap_severity,
                learner_message=str(plan.get("learner_message") or f"We found a learning gap in {gap.skill.name}."),
                gap_explanation=gap.misconception or gap.description,
                action_required=str(plan.get("action_required") or "Complete the targeted review items."),
                intervention_items_count=len(inserted),
                tutor_conversation_id=str(data.get("tutor_conversation_id")) if data.get("tutor_conversation_id") else None,
                estimated_fix_minutes=int(data.get("estimated_fix_minutes") or 20),
            )
        )
    return result


@router.post("/notifications/{gap_id}/dismiss", response_model=DismissResponse)
async def dismiss_notification(
    gap_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DismissResponse:
    gap = await _owned_gap(db, current_user.id, gap_id)
    gap.notification_dismissed = True
    await db.commit()
    return DismissResponse(dismissed=True)
