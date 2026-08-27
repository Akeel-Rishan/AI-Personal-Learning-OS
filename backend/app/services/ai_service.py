"""OpenAI wrapper for structured learning-plan generation."""

from __future__ import annotations

import asyncio
import json
from math import ceil
from typing import Any

from openai import OpenAI

from app.core.config import settings


class AIServiceUnavailable(RuntimeError):
    """Raised when OpenAI cannot be called with the current configuration."""


class AIServiceResponseError(RuntimeError):
    """Raised when a structured model response cannot be decoded."""


class AIService:
    """Generate and validate structured curriculum decisions with OpenAI."""

    def __init__(self) -> None:
        self.model = settings.openai_model
        self.client = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key.strip()
            else None
        )

    async def decompose_goal(
        self,
        goal_title: str,
        existing_knowledge: str,
        daily_minutes: int,
        target_date: str | None,
        available_skills: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run the synchronous SDK call in a worker thread for FastAPI."""

        if self.client is None:
            raise AIServiceUnavailable(
                "OpenAI is not configured yet. Add OPENAI_API_KEY to backend/.env and restart the backend."
            )
        return await asyncio.to_thread(
            self._decompose_sync,
            goal_title,
            existing_knowledge,
            daily_minutes,
            target_date,
            available_skills,
        )

    async def generate_structured(
        self,
        *,
        instructions: str,
        prompt: str,
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int = 2200,
    ) -> Any:
        """Generate strict JSON-schema output without blocking the event loop."""

        if self.client is None:
            raise AIServiceUnavailable(
                "OpenAI is not configured yet. Add OPENAI_API_KEY to backend/.env and restart the backend."
            )
        return await asyncio.to_thread(
            self._generate_structured_sync,
            instructions,
            prompt,
            schema_name,
            schema,
            max_output_tokens,
        )

    async def generate_text(
        self,
        *,
        instructions: str,
        messages: list[dict[str, str]] | str,
        max_output_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate plain text and return normalized usage metadata."""

        if self.client is None:
            raise AIServiceUnavailable(
                "OpenAI is not configured yet. Add OPENAI_API_KEY to backend/.env and restart the backend."
            )
        return await asyncio.to_thread(
            self._generate_text_sync, instructions, messages, max_output_tokens
        )

    def _generate_text_sync(
        self,
        instructions: str,
        messages: list[dict[str, str]] | str,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        if self.client is None:
            raise AIServiceUnavailable("OpenAI is not configured")
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=messages,
            max_output_tokens=max_output_tokens,
            store=False,
        )
        usage = getattr(response, "usage", None)
        return {
            "content": response.output_text or "",
            "model": getattr(response, "model", self.model),
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        }

    def _generate_structured_sync(
        self,
        instructions: str,
        prompt: str,
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int,
    ) -> Any:
        if self.client is None:
            raise AIServiceUnavailable("OpenAI is not configured")
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
            max_output_tokens=max_output_tokens,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        try:
            return json.loads(response.output_text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise AIServiceResponseError("OpenAI returned invalid structured output") from exc

    def _decompose_sync(
        self,
        goal_title: str,
        existing_knowledge: str,
        daily_minutes: int,
        target_date: str | None,
        available_skills: list[dict[str, Any]],
    ) -> dict[str, Any]:
        system_prompt = (
            "You are an expert curriculum designer. Select only skills from the provided "
            "available_skills list and match them by exact slug. Order skills by learning "
            "dependency with prerequisites first. Estimate timelines realistically from the "
            "learner's daily minutes. Return ONLY valid JSON with no markdown fences or explanation."
        )
        decomposition_schema = {
            "type": "object",
            "properties": {
                "required_skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "slug": {"type": "string"},
                            "priority_order": {"type": "integer", "minimum": 1},
                            "is_required": {"type": "boolean"},
                            "reason": {"type": "string"},
                        },
                        "required": ["slug", "priority_order", "is_required", "reason"],
                        "additionalProperties": False,
                    },
                },
                "estimated_weeks": {"type": "integer", "minimum": 1},
                "difficulty_assessment": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"],
                },
                "summary": {"type": "string"},
                "recommended_daily_focus_minutes": {
                    "type": "integer",
                    "minimum": 15,
                    "maximum": 480,
                },
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "required_skills",
                "estimated_weeks",
                "difficulty_assessment",
                "summary",
                "recommended_daily_focus_minutes",
                "warnings",
            ],
            "additionalProperties": False,
        }
        prompt = (
            f"Goal: {goal_title}\n"
            f"Existing knowledge: {existing_knowledge or 'Not provided'}\n"
            f"Daily study time: {daily_minutes} minutes\n"
            f"Target date: {target_date or 'No fixed date'}\n\n"
            f"Available skills:\n{json.dumps(available_skills, ensure_ascii=False)}"
        )
        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=prompt,
            max_output_tokens=2200,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "goal_decomposition",
                    "strict": True,
                    "schema": decomposition_schema,
                }
            },
        )
        response_text = response.output_text
        try:
            parsed = json.loads(response_text)
            return self._validate_decomposition(parsed, available_skills, daily_minutes)
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            return self._fallback_decomposition(available_skills, daily_minutes)

    def _validate_decomposition(
        self,
        payload: dict[str, Any],
        available_skills: list[dict[str, Any]],
        daily_minutes: int,
    ) -> dict[str, Any]:
        allowed = {str(skill["slug"]) for skill in available_skills}
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in payload["required_skills"]:
            slug = str(item["slug"])
            if slug not in allowed or slug in seen:
                continue
            seen.add(slug)
            selected.append(
                {
                    "slug": slug,
                    "priority_order": len(selected) + 1,
                    "is_required": bool(item.get("is_required", True)),
                    "reason": str(item.get("reason", "Supports the goal's learning path"))[:600],
                }
            )
        if not selected:
            raise ValueError("OpenAI did not select any valid skills")
        difficulty = str(payload.get("difficulty_assessment", "intermediate")).lower()
        if difficulty not in {"beginner", "intermediate", "advanced"}:
            difficulty = "intermediate"
        return {
            "required_skills": selected,
            "estimated_weeks": max(1, int(payload.get("estimated_weeks", 1))),
            "difficulty_assessment": difficulty,
            "summary": str(payload.get("summary", "Your personalized learning path is ready."))[:1500],
            "recommended_daily_focus_minutes": min(
                480, max(15, int(payload.get("recommended_daily_focus_minutes", daily_minutes)))
            ),
            "warnings": [str(item)[:500] for item in payload.get("warnings", [])][:5],
        }

    def _fallback_decomposition(
        self,
        available_skills: list[dict[str, Any]],
        daily_minutes: int,
    ) -> dict[str, Any]:
        ordered = sorted(
            available_skills,
            key=lambda skill: (int(skill.get("difficulty_level", 1)), str(skill.get("category", ""))),
        )[:12]
        total_hours = sum(float(skill.get("estimated_hours") or 10) for skill in ordered)
        weekly_hours = max(1.75, daily_minutes * 7 / 60)
        return {
            "required_skills": [
                {
                    "slug": str(skill["slug"]),
                    "priority_order": index,
                    "is_required": True,
                    "reason": "Included in the starter plan while the AI response is recovered.",
                }
                for index, skill in enumerate(ordered, start=1)
            ],
            "estimated_weeks": max(1, ceil(total_hours / weekly_hours)),
            "difficulty_assessment": "intermediate",
            "summary": "A practical foundation-first path has been prepared. You can refine it as your progress reveals new strengths and gaps.",
            "recommended_daily_focus_minutes": daily_minutes,
            "warnings": ["OpenAI returned an invalid response, so a safe starter plan was generated."],
        }

    def generate_skill_explanation(self, skill_name: str, user_level: str, context: str) -> str:
        """Generate a brief explanation of a skill's relevance."""

        if self.client is None:
            return f"{skill_name} is an important {user_level}-level building block for {context}."
        response = self.client.responses.create(
            model=self.model,
            max_output_tokens=180,
            instructions="Explain curriculum relevance in two concise sentences.",
            input=f"Why is {skill_name} important for a {user_level} learner pursuing {context}?",
            store=False,
        )
        return response.output_text or f"{skill_name} supports progress toward {context}."
