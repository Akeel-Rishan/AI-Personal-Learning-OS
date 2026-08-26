"""Evaluate assessment answers with deterministic and AI-assisted scoring."""

from __future__ import annotations

import re
from typing import Any

from openai import APIError

from app.models.assessment import AssessmentQuestion
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable


class AnswerEvaluator:
    """Score learner answers while keeping the assessment usable offline."""

    def __init__(self) -> None:
        self.ai = AIService()

    async def evaluate(
        self,
        question: AssessmentQuestion,
        user_answer: str | None,
    ) -> dict[str, Any]:
        """Return a normalized score, correctness flag, and concise feedback."""

        answer = (user_answer or "").strip()
        expected = (question.correct_answer or "").strip()
        if not answer:
            return self._result(0.0, "Skipped. Review the sample answer before continuing.")

        if question.question_type == "multiple_choice":
            correct = self._normalize(answer) == self._normalize(expected)
            prefix = "Correct!" if correct else "Not quite."
            feedback = f"{prefix} {question.explanation or ''}".strip()
            return self._result(1.0 if correct else 0.0, feedback or "Answer checked.")

        try:
            evaluated = await self._evaluate_with_ai(question, answer, expected)
            score = self._clamp(float(evaluated["score"]))
            return self._result(score, str(evaluated["feedback"]).strip())
        except (AIServiceUnavailable, AIServiceResponseError, APIError, KeyError, TypeError, ValueError):
            return self._heuristic_result(question.question_type, answer, expected)

    async def evaluate_answer(
        self,
        question: AssessmentQuestion,
        user_answer: str,
    ) -> dict[str, Any]:
        """Evaluate an answer using the public assessment service contract."""

        result = await self.evaluate(question, user_answer)
        result["correct_answer"] = question.correct_answer or ""
        return result

    async def _evaluate_with_ai(
        self,
        question: AssessmentQuestion,
        answer: str,
        expected: str,
    ) -> dict[str, Any]:
        common = {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "feedback": {"type": "string"},
        }
        extra: dict[str, Any]
        if question.question_type == "explanation":
            extra = {"key_concepts_covered": {"type": "array", "items": {"type": "string"}}}
        elif question.question_type == "debugging":
            extra = {
                "identified_bug": {"type": "boolean"},
                "fixed_bug": {"type": "boolean"},
            }
        else:
            extra = {
                "correctness": {"type": "number", "minimum": 0, "maximum": 1},
                "code_quality": {"type": "number", "minimum": 0, "maximum": 1},
            }
        properties = {**common, **extra}
        schema = {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
        return await self.ai.generate_structured(
            instructions=(
                "You are a fair technical assessment grader. Compare the learner response with the "
                "reference answer. Give partial credit for correct reasoning. Ignore writing style. "
                "Return actionable feedback in at most three sentences."
            ),
            prompt=(
                f"Question type: {question.question_type}\nQuestion: {question.question_text}\n"
                f"Reference answer: {expected}\nLearner answer: {answer}"
            ),
            schema_name=f"{question.question_type}_answer_evaluation",
            schema=schema,
            max_output_tokens=600,
        )

    def _heuristic_result(self, question_type: str, answer: str, expected: str) -> dict[str, Any]:
        expected_tokens = self._tokens(expected)
        answer_tokens = self._tokens(answer)
        overlap = len(expected_tokens & answer_tokens) / max(1, len(expected_tokens))
        length_factor = min(1.0, len(answer_tokens) / max(4, len(expected_tokens) * 0.55))
        score = self._clamp((overlap * 0.8) + (length_factor * 0.2))
        if question_type in {"coding", "debugging"} and not any(
            marker in answer for marker in ("=", "(", ")", ":", "return", "fix", "bug")
        ):
            score *= 0.75
        feedback = (
            "Good: your answer covers most of the reference concepts."
            if score >= 0.7
            else "Review the reference answer and include the key idea or correction more explicitly."
        )
        return self._result(score, feedback)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9_]+", value.lower()) if len(token) > 2}

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.lower().split()).rstrip(".")

    @staticmethod
    def _clamp(score: float) -> float:
        return min(1.0, max(0.0, score))

    @classmethod
    def _result(cls, score: float, feedback: str) -> dict[str, Any]:
        normalized = round(cls._clamp(score), 4)
        return {
            "score": normalized,
            "is_correct": normalized >= 0.7,
            "feedback": feedback,
        }
