"""AI-assisted educational Python code review."""

from __future__ import annotations

import ast
import json
from typing import Any

from openai import APIError

from app.models.exercise import Exercise
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable


REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
        "is_correct": {"type": ["boolean", "null"]},
        "correctness_score": {"type": "number", "minimum": 0, "maximum": 1},
        "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
        "style_score": {"type": "number", "minimum": 0, "maximum": 1},
        "performance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "passed_test_cases": {"type": ["integer", "null"]},
        "total_test_cases": {"type": ["integer", "null"]},
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"}, "suggestion": {"type": "string"},
                    "example": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "warning", "suggestion"]},
                },
                "required": ["issue", "suggestion", "example", "severity"],
                "additionalProperties": False,
            },
        },
        "better_approach": {"type": ["string", "null"]},
        "learning_note": {"type": "string"},
    },
    "required": ["overall_score", "is_correct", "correctness_score", "quality_score", "style_score", "performance_score", "passed_test_cases", "total_test_cases", "summary", "strengths", "improvements", "better_approach", "learning_note"],
    "additionalProperties": False,
}


class CodeReviewService:
    """Assess correctness and teach improvements without executing submitted code."""

    def __init__(self) -> None:
        self.ai = AIService()

    async def evaluate_code_solution(self, exercise: Exercise, user_code: str, skill_name: str) -> dict[str, Any]:
        content = exercise.content
        prompt = (
            f"Skill: {skill_name}\nExercise: {content.get('problem_statement', exercise.description)}\n"
            f"Test cases: {json.dumps(content.get('test_cases', []))}\nConstraints: {content.get('constraints', [])}\n"
            f"Expected approach: {exercise.solution or 'Not provided'}\nStudent code:\n```python\n{user_code}\n```"
        )
        return await self._review(prompt, user_code, skill_name, len(content.get("test_cases", []) or []), True)

    async def review_free_code(self, code: str, context: str, skill_name: str, user_mastery: float) -> dict[str, Any]:
        depth = "correctness and fundamental readability" if user_mastery < .5 else "optimization, edge cases, and Python best practices"
        prompt = f"Skill: {skill_name}\nLearner mastery: {user_mastery:.0%}\nReview emphasis: {depth}\nContext: {context or 'General review'}\nStudent code:\n```python\n{code}\n```"
        return await self._review(prompt, code, skill_name, 0, False)

    async def _review(self, prompt: str, code: str, skill_name: str, test_count: int, tied_to_exercise: bool) -> dict[str, Any]:
        try:
            result = await self.ai.generate_structured(
                instructions=(
                    "You are an expert Python code reviewer for education. Evaluate correctness, readability, "
                    "Pythonic style, performance, and edge cases. Never execute code. Give specific, actionable "
                    "feedback and do not reveal a complete solution. Return strict JSON."
                ),
                prompt=prompt,
                schema_name="educational_code_review",
                schema=REVIEW_SCHEMA,
                max_output_tokens=1800,
            )
            return self._normalize(result)
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError, KeyError, TypeError, ValueError):
            return self._fallback_review(code, skill_name, test_count, tied_to_exercise)

    @staticmethod
    def _normalize(result: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(result)
        for key in ("overall_score", "correctness_score", "quality_score", "style_score", "performance_score"):
            normalized[key] = round(min(1.0, max(0.0, float(normalized.get(key, 0)))), 3)
        normalized["strengths"] = [str(item)[:300] for item in normalized.get("strengths", [])][:8]
        normalized["improvements"] = list(normalized.get("improvements", []))[:8]
        return normalized

    @staticmethod
    def _fallback_review(code: str, skill_name: str, test_count: int, tied_to_exercise: bool) -> dict[str, Any]:
        improvements: list[dict[str, str]] = []
        try:
            tree = ast.parse(code)
            syntax_ok = True
        except SyntaxError as exc:
            tree = None
            syntax_ok = False
            improvements.append({"issue": f"Syntax error near line {exc.lineno or 1}", "suggestion": exc.msg, "example": "Check punctuation and indentation around that line.", "severity": "critical"})
        has_function = bool(tree and any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree)))
        has_docstring = bool(tree and any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node) for node in ast.walk(tree)))
        if syntax_ok and not has_function:
            improvements.append({"issue": "No reusable function was detected", "suggestion": "Put the solution logic in a clearly named function.", "example": "def solve(data):\n    return result", "severity": "warning"})
        if syntax_ok and has_function and not has_docstring:
            improvements.append({"issue": "The function has no short description", "suggestion": "Add a concise docstring describing inputs and output.", "example": '"""Return the transformed values."""', "severity": "suggestion"})
        score = .2 if not syntax_ok else .68 + (.08 if has_function else 0) + (.05 if has_docstring else 0)
        score = round(min(.9, score), 2)
        passed = round(test_count * score) if tied_to_exercise else None
        return {
            "overall_score": score, "is_correct": score >= .7 if tied_to_exercise else None,
            "correctness_score": score, "quality_score": .75 if syntax_ok else .2,
            "style_score": .72 if syntax_ok else .2, "performance_score": .7 if syntax_ok else .2,
            "passed_test_cases": passed, "total_test_cases": test_count if tied_to_exercise else None,
            "summary": "The code is syntactically valid and has a workable structure." if syntax_ok else "Fix the syntax error before evaluating the solution approach.",
            "strengths": (["Valid Python syntax", "A reusable function structure"] if has_function else ["A clear attempt at the problem"]),
            "improvements": improvements or [{"issue": "Edge cases are not documented", "suggestion": "State how empty or unusual inputs should behave.", "example": "if not data: return []", "severity": "suggestion"}],
            "better_approach": "Separate input validation from the core transformation, then verify one edge case at a time.",
            "learning_note": f"In {skill_name}, correctness comes first; readable structure makes that correctness easier to verify.",
        }

    @staticmethod
    def format_feedback_for_display(review_result: dict[str, Any], attempt_number: int = 1) -> dict[str, Any]:
        percentage = round(float(review_result.get("overall_score", 0)) * 100)
        grade, color = (("Excellent", "green") if percentage >= 90 else ("Good", "blue") if percentage >= 70 else ("Needs Work", "yellow") if percentage >= 45 else ("Incorrect", "red"))
        return {
            "score_percentage": percentage, "grade": grade, "grade_color": color,
            "summary": review_result.get("summary", ""),
            "sections": [
                {"title": "Correctness", "score": round(float(review_result.get("correctness_score", 0)) * 100), "color": color, "items": review_result.get("strengths", [])},
                {"title": "Improvements", "items": review_result.get("improvements", [])},
            ],
            "show_hint_button": percentage < 70,
            "show_solution_button": attempt_number >= 3,
        }
