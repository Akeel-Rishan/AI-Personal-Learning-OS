"""Generate skill assessment questions with OpenAI and local fallbacks."""

from __future__ import annotations

from typing import Any

from openai import APIError

from app.models.skill import Skill
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable
from app.services.fallback_questions import fallback_questions_for


class QuestionGenerator:
    """Create validated, mixed-format technical assessment questions."""

    def __init__(self) -> None:
        self.ai = AIService()

    async def generate_questions_for_skill(
        self,
        skill: Skill,
        count: int = 3,
        difficulty_range: tuple[int, int] = (1, 3),
    ) -> list[dict[str, Any]]:
        """Generate exactly ``count`` questions for one skill."""

        count = min(6, max(1, count))
        low, high = max(1, difficulty_range[0]), min(5, difficulty_range[1])
        instructions = (
            f"You are an expert technical educator creating assessment questions. Questions must "
            f"accurately test {skill.name}. Generate exactly {count} questions. Mix question types; "
            "for each set of three prefer one multiple_choice, one explanation, and one debugging. "
            f"Difficulty must be between {low} and {high}, where 1 is easy and 5 is hard. "
            "For coding skills include actual code snippets. For math skills use concrete numerical "
            "examples. Answers and explanations must be accurate and self-contained."
        )
        prompt = (
            f"Skill: {skill.name}\nCategory: {skill.category}\n"
            f"Description: {skill.description or 'No description provided'}\n"
            f"Generate {count} diagnostic questions that distinguish memorization from understanding."
        )
        schema = {
            "type": "array",
            "minItems": count,
            "maxItems": count,
            "items": {
                "type": "object",
                "properties": {
                    "question_type": {
                        "type": "string",
                        "enum": ["multiple_choice", "explanation", "debugging", "coding"],
                    },
                    "question_text": {"type": "string"},
                    "options": {
                        "anyOf": [
                            {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                            {"type": "null"},
                        ]
                    },
                    "correct_answer": {"type": "string"},
                    "explanation": {"type": "string"},
                    "difficulty": {"type": "integer", "minimum": low, "maximum": high},
                },
                "required": [
                    "question_type",
                    "question_text",
                    "options",
                    "correct_answer",
                    "explanation",
                    "difficulty",
                ],
                "additionalProperties": False,
            },
        }
        try:
            payload = await self.ai.generate_structured(
                instructions=instructions,
                prompt=prompt,
                schema_name="assessment_questions",
                schema=schema,
                max_output_tokens=3200,
            )
            return self._normalize_questions(payload, count, low, high)
        except (AIServiceUnavailable, AIServiceResponseError, APIError, ValueError, TypeError):
            offset = sum(ord(character) for character in skill.slug) % 5
            return fallback_questions_for(skill.category, count, offset)

    async def generate_initial_assessment(
        self,
        goal_skills: list[Skill],
        existing_knowledge: str,
        max_questions: int = 20,
    ) -> list[dict[str, Any]]:
        """Generate questions for up to six ordered foundational goal skills."""

        selected = goal_skills[:6]
        if not selected:
            return []
        per_skill = min(4, max(2, max_questions // len(selected)))
        difficulty = (2, 4) if existing_knowledge.strip() else (1, 3)
        questions: list[dict[str, Any]] = []
        for skill in selected:
            remaining = max_questions - len(questions)
            if remaining <= 0:
                break
            generated = await self.generate_questions_for_skill(
                skill,
                count=min(per_skill, remaining),
                difficulty_range=difficulty,
            )
            for question in generated:
                question["skill_id"] = skill.id
                questions.append(question)
        return questions[:max_questions]

    @staticmethod
    def _normalize_questions(
        payload: Any,
        count: int,
        low: int,
        high: int,
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, list) or len(payload) != count:
            raise ValueError("Unexpected question count")
        normalized: list[dict[str, Any]] = []
        allowed_types = {"multiple_choice", "explanation", "debugging", "coding"}
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Question must be an object")
            question_type = str(item.get("question_type", ""))
            if question_type not in allowed_types:
                raise ValueError("Unsupported question type")
            options = item.get("options")
            if question_type == "multiple_choice":
                if not isinstance(options, list) or len(options) != 4:
                    raise ValueError("MCQ requires four options")
                options = [str(option) for option in options]
            else:
                options = None
            question_text = str(item.get("question_text", "")).strip()
            correct_answer = str(item.get("correct_answer", "")).strip()
            if not question_text or not correct_answer:
                raise ValueError("Question and answer are required")
            normalized.append(
                {
                    "question_type": question_type,
                    "question_text": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "explanation": str(item.get("explanation", "")).strip(),
                    "difficulty": min(high, max(low, int(item.get("difficulty", low)))),
                }
            )
        return normalized
