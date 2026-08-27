"""Authenticated AI tutor conversation endpoints."""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.tutor import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    DeleteConversationResponse,
    MessageRequest,
    SendMessageResponse,
    SuggestedPromptsResponse,
)
from app.services.tutor_service import TutorService


router = APIRouter()


@router.post("/conversations", response_model=ConversationDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationDetailResponse:
    service = TutorService(db)
    conversation = await service.create_conversation(
        str(current_user.id), payload.title, payload.skill_id
    )
    return service.serialize_detail(conversation)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    skill_id: str | None = None,
) -> list[ConversationResponse]:
    service = TutorService(db)
    conversations = await service.get_conversations(str(current_user.id), limit, skill_id)
    return [service.serialize_conversation(item) for item in conversations]


@router.get("/suggested-prompts", response_model=SuggestedPromptsResponse)
async def suggested_prompts(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conversation_id: str | None = None,
    refresh: bool = False,
) -> SuggestedPromptsResponse:
    return await TutorService(db).generate_suggested_prompts(
        str(current_user.id), conversation_id, refresh
    )


@router.get("/context", response_model=dict[str, Any])
async def tutor_context(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    return await TutorService(db).build_learner_context(str(current_user.id))


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationDetailResponse:
    service = TutorService(db)
    conversation = await service.get_conversation(conversation_id, str(current_user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return service.serialize_detail(conversation)


@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    payload: MessageRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SendMessageResponse:
    try:
        async with asyncio.timeout(30):
            return await TutorService(db).send_message(
                conversation_id,
                str(current_user.id),
                payload.content,
                payload.socratic_mode,
                payload.skill_focus,
                payload.regenerate,
            )
    except TimeoutError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The tutor took too long to respond. Please try again.",
        ) from exc


@router.delete("/conversations/{conversation_id}", response_model=DeleteConversationResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteConversationResponse:
    deleted = await TutorService(db).delete_conversation(conversation_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return DeleteConversationResponse(deleted=True)
