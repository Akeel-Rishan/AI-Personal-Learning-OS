"""Context-aware AI tutor and persistent conversation management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Any

from fastapi import HTTPException, status
from openai import APIError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import TutorConversation, TutorMessage
from app.models.exercise import Exercise, ExerciseAttempt
from app.models.goal import Goal, GoalSkill
from app.models.progress import UserSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.skill import Skill
from app.models.user import User
from app.schemas.tutor import (
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
    SendMessageResponse,
    SuggestedPromptsResponse,
)
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable
from app.services.plan_service import PlanService


class TutorService:
    """Personalize tutoring with live learner data and database-backed history."""

    _prompt_cache: dict[str, tuple[float, SuggestedPromptsResponse]] = {}
    _summary_cache: dict[str, str] = {}

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIService()

    async def build_learner_context(self, user_id: str) -> dict[str, Any]:
        parsed_user = self._parse_uuid(user_id)
        user = (
            await self.db.execute(
                select(User).options(selectinload(User.profile)).where(User.id == parsed_user)
            )
        ).scalars().one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        goal = (
            await self.db.execute(
                select(Goal)
                .options(selectinload(Goal.goal_skills).selectinload(GoalSkill.skill))
                .where(Goal.user_id == parsed_user, Goal.status == "active")
                .order_by(Goal.created_at.desc())
                .limit(1)
            )
        ).scalars().unique().one_or_none()
        roadmap = (
            await self.db.execute(
                select(Roadmap)
                .options(
                    selectinload(Roadmap.phases)
                    .selectinload(RoadmapPhase.items)
                    .selectinload(RoadmapItem.skill)
                )
                .where(Roadmap.user_id == parsed_user, Roadmap.status == "active")
                .order_by(Roadmap.created_at.desc())
                .limit(1)
            )
        ).scalars().unique().one_or_none()
        active_phase = (
            next((phase for phase in roadmap.phases if phase.status == "active"), None)
            if roadmap else None
        )
        focus_skills = list(
            dict.fromkeys(
                item.skill.name
                for item in (active_phase.items if active_phase else [])
                if item.skill is not None and item.status in {"pending", "active"}
            )
        )

        user_skills = list(
            (
                await self.db.execute(
                    select(UserSkill)
                    .options(selectinload(UserSkill.skill))
                    .where(UserSkill.user_id == parsed_user)
                    .order_by(UserSkill.mastery_score.desc())
                )
            ).scalars()
        )
        mastery = [
            {
                "id": str(entry.skill_id),
                "name": entry.skill.name,
                "mastery": round(entry.mastery_score, 3),
                "level": self._mastery_level(entry.mastery_score),
            }
            for entry in user_skills
        ]
        strong = [entry["name"] for entry in mastery if float(entry["mastery"]) >= 0.75]
        weak = [entry["name"] for entry in mastery if float(entry["mastery"]) < 0.5]

        recent_rows = (
            await self.db.execute(
                select(Exercise.title, Skill.name, ExerciseAttempt.user_answer)
                .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
                .outerjoin(Skill, Skill.id == Exercise.skill_id)
                .where(
                    ExerciseAttempt.user_id == parsed_user,
                    ExerciseAttempt.is_correct.is_(False),
                    ExerciseAttempt.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
                )
                .order_by(ExerciseAttempt.created_at.desc())
                .limit(5)
            )
        ).all()
        recent_mistakes = [
            {"exercise": title, "skill": skill_name, "answer": answer}
            for title, skill_name, answer in recent_rows
        ]

        plan_service = PlanService(self.db)
        today_plan = await plan_service.get_today_plan(user_id)
        today_items = [item.title for item in today_plan.items] if today_plan else []
        streak = await plan_service.get_streak_count(user_id)
        total_xp = await plan_service.get_user_total_xp(user_id)
        goal_skills = [
            {"id": str(link.skill.id), "name": link.skill.name, "slug": link.skill.slug}
            for link in sorted(goal.goal_skills, key=lambda item: item.priority_order)
        ] if goal else []

        return {
            "user_name": user.full_name.split()[0] if user.full_name else "Learner",
            "goal_title": goal.title if goal else "build new skills",
            "preferred_style": user.profile.preferred_explanation_style if user.profile else "balanced",
            "daily_minutes": user.profile.daily_study_minutes if user.profile else 60,
            "current_phase": active_phase.title if active_phase else "Getting started",
            "current_focus_skills": focus_skills,
            "goal_skills": goal_skills,
            "skill_mastery": mastery,
            "strong_skills": strong,
            "weak_skills": weak,
            "today_plan_items": today_items,
            "recent_mistakes": recent_mistakes,
            "total_xp": total_xp,
            "streak_days": streak,
        }

    async def build_system_prompt(
        self,
        context: dict[str, Any],
        socratic_mode: bool = False,
        skill_focus: str | None = None,
    ) -> str:
        mastery_lines = "\n".join(
            f"- {item['name']}: {round(float(item['mastery']) * 100)}% ({item['level']})"
            for item in context["skill_mastery"]
        ) or "- No mastery measurements yet"
        style = str(context["preferred_style"])
        style_instruction = {
            "visual": "Use spatial descriptions, small diagrams in text, and worked examples.",
            "mathematical": "Use precise definitions, notation, and derivations before examples.",
            "step_by_step": "Break reasoning into numbered, incremental steps.",
            "analogies": "Lead with a memorable analogy, then map it back to the technical idea.",
            "balanced": "Balance intuition, concise formal detail, and a concrete example.",
        }.get(style, "Balance intuition, concise formal detail, and a concrete example.")
        teaching = (
            "SOCRATIC MODE IS ENABLED. Never give direct answers. Ask guiding questions; if the learner "
            "is stuck, give one small hint and ask again. Praise reasoning, not merely correctness. Reveal "
            "the answer only after 2-3 guided exchanges."
            if socratic_mode else
            "EXPLANATION MODE. Match depth to mastery. Start weak skills with intuition and examples; "
            "skip basics and discuss nuance for strong skills. Always use a concrete example before an "
            f"abstract definition. {style_instruction}"
        )
        return f"""--- IDENTITY ---
You are an expert AI tutor for {context['user_name']}, who is learning toward this goal: {context['goal_title']}.

--- LEARNER PROFILE ---
Name: {context['user_name']}
Current Focus: {context['current_phase']}
Skills they are working on now: {', '.join(context['current_focus_skills']) or 'Not established yet'}
Strong areas (go deeper and skip basics): {', '.join(context['strong_skills']) or 'Not measured yet'}
Areas needing support (be extra careful and use more examples): {', '.join(context['weak_skills']) or 'Not measured yet'}
Preferred explanation style: {style}
Skill mastery levels:
{mastery_lines}

--- TODAY'S LEARNING ---
Today's plan: {', '.join(context['today_plan_items']) or 'No scheduled items'}
{f"Current focus skill: {skill_focus}" if skill_focus else ''}
Recent mistakes: {context['recent_mistakes'] or 'None recorded'}

--- TEACHING APPROACH ---
{teaching}

--- RESPONSE GUIDELINES ---
- Keep responses focused and appropriately sized.
- Naturally anchor each response to the learner's current topic or personal learning context.
- Use Markdown headings, lists, and fenced code blocks when helpful.
- Use Python for code unless asked otherwise and $formula$ notation for math.
- End teaching explanations with a brief comprehension-check question.
- If confusion persists, switch to a genuinely different explanation approach.
- Be patient and never shame the learner.
- Briefly answer off-topic questions, then redirect toward their learning goal.

--- WHAT NOT TO DO ---
- Do not complete homework or entire projects for the learner; guide them.
- Do not contradict earlier messages.
- Do not use unexplained jargon for weak skills.
"""

    async def create_conversation(
        self, user_id: str, title: str | None = None, skill_id: str | None = None
    ) -> TutorConversation:
        parsed_skill = self._optional_uuid(skill_id)
        skill = await self.db.get(Skill, parsed_skill) if parsed_skill else None
        if parsed_skill and skill is None:
            raise HTTPException(status_code=404, detail="Skill not found")
        conversation = TutorConversation(
            user_id=self._parse_uuid(user_id),
            skill_id=parsed_skill,
            title=(title.strip()[:300] if title and title.strip() else None)
            or (f"Chat about {skill.name}" if skill else "General Learning Chat"),
            is_active=True,
            message_count=0,
        )
        self.db.add(conversation)
        await self.db.commit()
        return await self.get_conversation(str(conversation.id), user_id)  # type: ignore[return-value]

    async def get_conversations(
        self, user_id: str, limit: int = 20, skill_id: str | None = None
    ) -> list[TutorConversation]:
        query = (
            select(TutorConversation)
            .options(selectinload(TutorConversation.skill), selectinload(TutorConversation.messages))
            .where(TutorConversation.user_id == self._parse_uuid(user_id))
            .order_by(TutorConversation.updated_at.desc())
            .limit(limit)
        )
        if skill_id:
            query = query.where(TutorConversation.skill_id == self._parse_uuid(skill_id))
        result = await self.db.execute(query)
        return list(result.scalars().unique())

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> TutorConversation | None:
        parsed_conversation = self._optional_uuid(conversation_id)
        if parsed_conversation is None:
            return None
        result = await self.db.execute(
            select(TutorConversation)
            .options(selectinload(TutorConversation.skill), selectinload(TutorConversation.messages))
            .execution_options(populate_existing=True)
            .where(
                TutorConversation.id == parsed_conversation,
                TutorConversation.user_id == self._parse_uuid(user_id),
            )
        )
        return result.scalars().unique().one_or_none()

    async def send_message(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        socratic_mode: bool = False,
        skill_focus: str | None = None,
        regenerate: bool = False,
    ) -> SendMessageResponse:
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        context = await self.build_learner_context(user_id)
        focus = skill_focus or (conversation.skill.name if conversation.skill else None)
        system_prompt = await self.build_system_prompt(context, socratic_mode, focus)
        stored_messages = list(conversation.messages)
        regeneration_user: TutorMessage | None = None
        if regenerate:
            if len(stored_messages) < 2 or stored_messages[-1].role != "assistant" or stored_messages[-2].role != "user":
                raise HTTPException(status_code=409, detail="There is no assistant response to regenerate")
            regeneration_user = stored_messages[-2]
            if regeneration_user.content != user_message:
                raise HTTPException(status_code=409, detail="The last response can only be regenerated from its original message")
            await self.db.delete(stored_messages[-1])
            stored_messages = stored_messages[:-2]
        history = [
            {"role": message.role, "content": message.content}
            for message in stored_messages
            if message.role in {"user", "assistant"}
        ]
        history = await self._manage_context_window(history)
        history.append({"role": "user", "content": user_message})
        try:
            generated = await self.ai.generate_text(
                instructions=system_prompt, messages=history, max_output_tokens=2048
            )
            content = str(generated["content"]).strip()
            if not content:
                raise AIServiceResponseError("OpenAI returned an empty tutor response")
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError):
            content = self._fallback_tutor_response(context, user_message, socratic_mode, focus)
            generated = {"model": self.ai.model, "input_tokens": 0, "output_tokens": 0, "fallback": True}

        now = datetime.now(timezone.utc)
        user_record = regeneration_user or TutorMessage(
            conversation_id=conversation.id, role="user", content=user_message,
            message_metadata={"socratic_mode": socratic_mode, "skill_focus": focus},
        )
        assistant_metadata: dict[str, object] = {
            "provider": "openai",
            "model": str(generated.get("model", self.ai.model)),
            "input_tokens": int(generated.get("input_tokens", 0)),
            "output_tokens": int(generated.get("output_tokens", 0)),
            "socratic_mode": socratic_mode,
            "fallback": bool(generated.get("fallback", False)),
        }
        assistant_record = TutorMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=content,
            message_metadata=assistant_metadata,
        )
        if regeneration_user is None:
            self.db.add(user_record)
        self.db.add(assistant_record)
        first_exchange = conversation.message_count == 0
        if regeneration_user is None:
            conversation.message_count += 2
        conversation.updated_at = now
        await self.db.flush()
        if first_exchange and conversation.title == "General Learning Chat":
            conversation.title = await self.auto_generate_title(conversation_id, user_message)
        await self.db.commit()
        return SendMessageResponse(
            user_message_id=str(user_record.id),
            assistant_message_id=str(assistant_record.id),
            content=content,
            conversation_id=conversation_id,
            metadata=assistant_metadata,
        )

    async def generate_suggested_prompts(
        self, user_id: str, conversation_id: str | None = None, refresh: bool = False
    ) -> SuggestedPromptsResponse:
        cache_key = f"{user_id}:{conversation_id or 'general'}"
        cached = self._prompt_cache.get(cache_key)
        if not refresh and cached and monotonic() - cached[0] < 3600:
            return cached[1]
        context = await self.build_learner_context(user_id)
        focus = (
            context["current_focus_skills"][0]
            if context["current_focus_skills"]
            else context["weak_skills"][0] if context["weak_skills"] else None
        )
        try:
            prompts = await self.ai.generate_structured(
                instructions="Generate five concise, specific tutoring questions. Return strict JSON.",
                prompt=(
                    f"Learner: {context['user_name']}\nCurrent skills: {context['current_focus_skills']}\n"
                    f"Weak skills: {context['weak_skills']}\nMastery: {context['skill_mastery']}\n"
                    "Mix conceptual and practical questions at the learner's current level."
                ),
                schema_name="tutor_suggestions",
                schema={
                    "type": "object",
                    "properties": {
                        "prompts": {
                            "type": "array", "minItems": 5, "maxItems": 5,
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["prompts"],
                    "additionalProperties": False,
                },
                max_output_tokens=500,
            )
            questions = [str(item)[:300] for item in prompts["prompts"]][:5]
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError, KeyError, TypeError):
            topic = focus or (context["weak_skills"][0] if context["weak_skills"] else "my current topic")
            questions = [
                f"Can you explain {topic} with a concrete example?",
                f"What is the most important idea to understand about {topic}?",
                f"Can you give me a short practice problem about {topic}?",
                f"What common mistakes should I avoid with {topic}?",
                f"How does {topic} connect to my learning goal?",
            ]
        if focus and not any(focus.casefold() in question.casefold() for question in questions):
            questions[0] = f"Can you explain {focus} with a concrete example?"
        response = SuggestedPromptsResponse(prompts=questions, generated_for_skill=focus)
        self._prompt_cache[cache_key] = (monotonic(), response)
        return response

    async def get_conversation_summary(self, conversation_id: str, user_id: str) -> str:
        if conversation_id in self._summary_cache:
            return self._summary_cache[conversation_id]
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        excerpt = "\n".join(f"{item.role}: {item.content}" for item in conversation.messages[:3])
        try:
            generated = await self.ai.generate_text(
                instructions="Summarize the conversation in one sentence of at most eight words.",
                messages=excerpt,
                max_output_tokens=40,
            )
            summary = str(generated["content"]).strip().strip('"')
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError):
            summary = conversation.title or "Learning conversation"
        self._summary_cache[conversation_id] = summary
        return summary

    async def auto_generate_title(self, conversation_id: str, first_user_message: str) -> str:
        try:
            generated = await self.ai.generate_text(
                instructions="Create a clear 4-6 word tutoring conversation title. Return only the title, without quotes or ending punctuation.",
                messages=first_user_message,
                max_output_tokens=30,
            )
            title = str(generated["content"]).strip().strip('"').rstrip(".!?")[:300]
            if title:
                return title
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError):
            pass
        words = first_user_message.strip(" .!?\n").split()[:6]
        return " ".join(words).title()[:300] or "Learning Conversation"

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation is None:
            return False
        await self.db.delete(conversation)
        await self.db.commit()
        self._summary_cache.pop(conversation_id, None)
        return True

    async def _manage_context_window(
        self, history: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        if sum(len(item["content"]) for item in history) / 4 <= 150_000:
            return history
        older, recent = history[:-20], history[-20:]
        source = "\n".join(f"{item['role']}: {item['content']}" for item in older)
        try:
            generated = await self.ai.generate_text(
                instructions="Summarize this tutoring history in 3-5 sentences, preserving concepts discussed and the learner's demonstrated understanding.",
                messages=source,
                max_output_tokens=500,
            )
            summary = str(generated["content"])
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError):
            summary = source[-4000:]
        return [{"role": "user", "content": f"Earlier conversation summary:\n{summary}"}, *recent]

    @classmethod
    def serialize_conversation(cls, conversation: TutorConversation) -> ConversationResponse:
        last = conversation.messages[-1].content if conversation.messages else None
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            skill_id=str(conversation.skill_id) if conversation.skill_id else None,
            skill_name=conversation.skill.name if conversation.skill else None,
            is_active=conversation.is_active,
            message_count=conversation.message_count,
            last_message_preview=last[:100] if last else None,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    @classmethod
    def serialize_detail(cls, conversation: TutorConversation) -> ConversationDetailResponse:
        base = cls.serialize_conversation(conversation)
        return ConversationDetailResponse(
            **base.model_dump(),
            messages=[
                MessageResponse(
                    id=str(message.id), role=message.role, content=message.content,
                    metadata=message.message_metadata, created_at=message.created_at,
                )
                for message in conversation.messages
            ],
        )

    @staticmethod
    def _fallback_tutor_response(
        context: dict[str, Any], message: str, socratic: bool, focus: str | None
    ) -> str:
        topic = focus or (context["current_focus_skills"][0] if context["current_focus_skills"] else "your current lesson")
        if socratic:
            return (
                f"{context['user_name']}, let’s reason through this together using **{topic}**. "
                f"Before we unpack _{message[:120]}_, what do you already believe is the first step, and why?"
            )
        return (
            f"{context['user_name']}, I’m temporarily unable to reach the AI model, but I can keep this tied to "
            f"**{topic}**. Try breaking the question into: what you know, what result you expect, and the exact "
            "step where the result changes. Which of those can you describe first?"
        )

    @staticmethod
    def _mastery_level(score: float) -> str:
        return "strong" if score >= 0.75 else "developing" if score >= 0.5 else "weak"

    @staticmethod
    def _optional_uuid(value: str | None) -> uuid.UUID | None:
        if not value:
            return None
        try:
            return uuid.UUID(value)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid identifier") from exc

    @classmethod
    def _parse_uuid(cls, value: str) -> uuid.UUID:
        parsed = cls._optional_uuid(value)
        if parsed is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid identifier")
        return parsed
