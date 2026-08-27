"""Tutor conversation request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    skill_id: str | None = None


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    socratic_mode: bool = False
    skill_focus: str | None = Field(default=None, max_length=200)
    regenerate: bool = False

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")
        return cleaned


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict[str, object] | None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str | None
    skill_id: str | None
    skill_name: str | None
    is_active: bool
    message_count: int
    last_message_preview: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class SendMessageResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    content: str
    conversation_id: str
    metadata: dict[str, object]


class SuggestedPromptsResponse(BaseModel):
    prompts: list[str]
    generated_for_skill: str | None


class DeleteConversationResponse(BaseModel):
    deleted: bool
