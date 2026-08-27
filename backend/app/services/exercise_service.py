"""Targeted exercise generation, attempts, mastery updates, hints, and analytics."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from openai import APIError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exercise import Exercise, ExerciseAttempt
from app.models.gamification import XPEvent
from app.models.progress import SkillHistory, UserSkill
from app.models.skill import Skill
from app.schemas.exercise import (
    AttemptFeedbackResponse,
    ExerciseHistoryItem,
    ExerciseResponse,
    ExerciseStatsResponse,
    ExerciseWithAttemptResponse,
    HintResponse,
    RecommendedExerciseResponse,
)
from app.services.ai_service import AIService, AIServiceResponseError, AIServiceUnavailable
from app.services.code_review_service import CodeReviewService


class ExerciseService:
    """Create adaptive practice and keep attempts and skill mastery consistent."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai = AIService()
        self.code_review = CodeReviewService()

    async def generate_exercises_for_skill(
        self,
        skill_id: str,
        user_id: str,
        count: int = 5,
        focus_weak_areas: bool = True,
        difficulty: int | None = None,
    ) -> list[Exercise]:
        skill = await self._get_skill(skill_id)
        user_skill = await self._get_user_skill(user_id, skill.id)
        mastery = user_skill.mastery_score if user_skill else 0.0
        weakness = await self.detect_weakness_patterns(user_id, skill_id) if focus_weak_areas else None
        recent = await self._recent_incorrect_answers(user_id, skill.id)
        target_difficulty = difficulty or min(5, max(1, round(mastery * 4) + 1))
        schema = self._generation_schema(count)
        try:
            payload = await self.ai.generate_structured(
                instructions=(
                    "You generate practical technical learning exercises. Use runnable Python for code, produce "
                    "a mix of multiple_choice, explanation, debugging, and coding items, and return strict JSON."
                ),
                prompt=(
                    f"Generate exactly {count} exercises for {skill.name}.\nDescription: {skill.description}\n"
                    f"Mastery: {mastery:.0%}\nTarget difficulty around {target_difficulty}/5.\n"
                    f"Detected weakness: {weakness or 'none'}\nRecent wrong answers: {json.dumps(recent)}\n"
                    "Target misconceptions with practical questions. Do not put the solution in problem_statement."
                ),
                schema_name="targeted_exercises",
                schema=schema,
                max_output_tokens=4000,
            )
            generated = payload["exercises"]
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError, KeyError, TypeError):
            generated = self._fallback_exercises(skill, count, target_difficulty)
        exercises: list[Exercise] = []
        for item in generated[:count]:
            exercise = Exercise(
                skill_id=skill.id,
                title=str(item["title"])[:300],
                description=str(item.get("content", {}).get("problem_statement", item["title"])),
                exercise_type=str(item["exercise_type"]),
                difficulty=min(5, max(1, int(item.get("difficulty", target_difficulty)))),
                content=dict(item["content"]),
                solution=str(item.get("solution") or ""),
                hints=[str(hint)[:500] for hint in item.get("hints", [])][:5],
                is_ai_generated=True,
            )
            self.db.add(exercise)
            exercises.append(exercise)
        await self.db.commit()
        for exercise in exercises:
            await self.db.refresh(exercise)
            exercise.skill = skill
        return exercises

    async def get_exercises_for_skill(
        self, skill_id: str, user_id: str, limit: int = 10, exclude_completed: bool = True
    ) -> list[ExerciseWithAttemptResponse]:
        skill = await self._get_skill(skill_id)
        exercises = await self._load_skill_exercises(skill.id, limit)
        if len(exercises) < min(3, limit):
            await self.generate_exercises_for_skill(skill_id, user_id, max(3 - len(exercises), 3))
            exercises = await self._load_skill_exercises(skill.id, limit)
        serialized = [await self.serialize_exercise_with_attempt(item, user_id) for item in exercises]
        if exclude_completed:
            serialized = [item for item in serialized if not item.is_completed]
        return serialized

    async def get_exercise(self, exercise_id: str, user_id: str) -> ExerciseWithAttemptResponse | None:
        exercise = await self._get_exercise(exercise_id, required=False)
        return await self.serialize_exercise_with_attempt(exercise, user_id) if exercise else None

    async def get_recommended_exercises(self, user_id: str, limit: int = 5) -> list[RecommendedExerciseResponse]:
        parsed_user = self._parse_uuid(user_id)
        rows = list((await self.db.execute(
            select(UserSkill).options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == parsed_user, UserSkill.mastery_score < .65)
            .order_by(UserSkill.mastery_score.asc()).limit(limit)
        )).scalars())
        recommendations: list[RecommendedExerciseResponse] = []
        for entry in rows:
            exercises = await self._load_skill_exercises(entry.skill_id, 2)
            if not exercises:
                exercises = await self.generate_exercises_for_skill(str(entry.skill_id), user_id, 2)
            for exercise in exercises:
                response = await self.serialize_exercise_with_attempt(exercise, user_id)
                if response.is_completed:
                    continue
                recommendations.append(RecommendedExerciseResponse(
                    exercise=response, skill_name=entry.skill.name, skill_slug=entry.skill.slug,
                    skill_mastery=entry.mastery_score,
                    reason=f"Targeting your weak area in {entry.skill.name} ({entry.mastery_score:.0%})",
                ))
                if len(recommendations) >= limit:
                    return recommendations
        return recommendations

    async def submit_attempt(
        self, exercise_id: str, user_id: str, user_answer: str, time_spent_seconds: int
    ) -> AttemptFeedbackResponse:
        exercise = await self._get_exercise(exercise_id)
        parsed_user = self._parse_uuid(user_id)
        completed_attempts = list((await self.db.execute(
            select(ExerciseAttempt).where(
                ExerciseAttempt.exercise_id == exercise.id,
                ExerciseAttempt.user_id == parsed_user,
                ExerciseAttempt.is_correct.is_not(None),
            ).order_by(ExerciseAttempt.attempt_number)
        )).scalars())
        draft = (await self.db.execute(
            select(ExerciseAttempt).where(
                ExerciseAttempt.exercise_id == exercise.id,
                ExerciseAttempt.user_id == parsed_user,
                ExerciseAttempt.is_correct.is_(None),
            ).order_by(ExerciseAttempt.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        attempt_number = len(completed_attempts) + 1
        evaluation = await self._evaluate_answer(exercise, user_answer, attempt_number)
        score = min(1.0, max(0.0, float(evaluation["score"])))
        is_correct = bool(evaluation.get("is_correct", score >= .7))
        attempt = draft or ExerciseAttempt(
            user_id=parsed_user, exercise_id=exercise.id, attempt_number=attempt_number
        )
        attempt.user_answer = user_answer
        attempt.is_correct = is_correct
        attempt.score = score
        attempt.ai_feedback = str(evaluation["feedback"])
        attempt.time_spent_seconds = time_spent_seconds
        self.db.add(attempt)
        await self.db.flush()
        user_skill, mastery_change = await self._update_mastery(
            parsed_user, exercise.skill_id, is_correct, attempt_number, attempt.id
        )
        if is_correct:
            self.db.add(XPEvent(
                user_id=parsed_user, event_type="exercise_completed", xp_earned=30,
                description=f"[exercise:{exercise.id}] Completed {exercise.title}"[:300],
            ))
        await self.db.commit()
        weakness = await self.detect_weakness_patterns(user_id, str(exercise.skill_id)) if not is_correct and exercise.skill_id else None
        next_hint_index = attempt.hints_used
        hints = exercise.hints or []
        return AttemptFeedbackResponse(
            attempt_id=str(attempt.id), is_correct=is_correct, score=round(score, 3),
            feedback=str(evaluation["feedback"]),
            correct_answer=exercise.solution if exercise.exercise_type == "multiple_choice" else None,
            detailed_feedback=evaluation.get("detailed_feedback"),
            mastery_change=round(mastery_change, 3), new_mastery=round(user_skill.mastery_score, 3),
            hint_available=not is_correct and next_hint_index < len(hints),
            next_hint=hints[next_hint_index] if not is_correct and next_hint_index < len(hints) else None,
            attempt_number=attempt_number, mastery_percentage=round(user_skill.mastery_score * 100),
            weakness_detected=weakness,
        )

    async def get_hint(self, exercise_id: str, user_id: str, hint_index: int) -> HintResponse:
        exercise = await self._get_exercise(exercise_id)
        hints = exercise.hints or []
        if hint_index < 0 or hint_index >= len(hints):
            raise HTTPException(status_code=404, detail="No more hints are available")
        parsed_user = self._parse_uuid(user_id)
        draft = (await self.db.execute(
            select(ExerciseAttempt).where(
                ExerciseAttempt.exercise_id == exercise.id,
                ExerciseAttempt.user_id == parsed_user,
                ExerciseAttempt.is_correct.is_(None),
            ).order_by(ExerciseAttempt.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        if draft is None:
            completed_count = await self.db.scalar(select(func.count(ExerciseAttempt.id)).where(
                ExerciseAttempt.exercise_id == exercise.id, ExerciseAttempt.user_id == parsed_user,
                ExerciseAttempt.is_correct.is_not(None),
            ))
            draft = ExerciseAttempt(user_id=parsed_user, exercise_id=exercise.id, attempt_number=int(completed_count or 0) + 1, hints_used=0)
            self.db.add(draft)
        draft.hints_used = max(draft.hints_used, hint_index + 1)
        await self.db.commit()
        return HintResponse(hint=hints[hint_index], hint_number=hint_index + 1, total_hints=len(hints))

    async def detect_weakness_patterns(self, user_id: str, skill_id: str) -> dict[str, object] | None:
        rows = list((await self.db.execute(
            select(ExerciseAttempt, Exercise)
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .where(
                ExerciseAttempt.user_id == self._parse_uuid(user_id),
                Exercise.skill_id == self._parse_uuid(skill_id),
                ExerciseAttempt.is_correct.is_not(None),
            ).order_by(ExerciseAttempt.created_at.desc()).limit(10)
        )).all())
        consecutive: list[tuple[ExerciseAttempt, Exercise]] = []
        for attempt, exercise in rows:
            if attempt.is_correct:
                break
            consecutive.append((attempt, exercise))
        if len(consecutive) < 3:
            return None
        source = [{"question": item.description, "correct_answer": item.solution, "user_answer": attempt.user_answer} for attempt, item in consecutive]
        try:
            result = await self.ai.generate_structured(
                instructions="Identify the learner's specific misconception from repeated wrong answers. Return strict JSON.",
                prompt=json.dumps(source), schema_name="exercise_weakness",
                schema={
                    "type": "object",
                    "properties": {"misconception": {"type": "string"}, "targeted_review": {"type": "string"}, "suggested_resources": {"type": "array", "items": {"type": "string"}}},
                    "required": ["misconception", "targeted_review", "suggested_resources"], "additionalProperties": False,
                }, max_output_tokens=500,
            )
            return result
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError, KeyError, TypeError):
            return {
                "misconception": f"Repeated difficulty applying {consecutive[0][1].title}",
                "targeted_review": "Review the core rule, then work through one small example before trying again.",
                "suggested_resources": ["Ask the AI Tutor for a guided example", "Retry with the first hint"],
            }

    async def get_exercise_history(self, user_id: str, skill_id: str | None = None, limit: int = 20) -> list[ExerciseHistoryItem]:
        query = select(ExerciseAttempt, Exercise).join(Exercise).options(selectinload(Exercise.skill)).where(
            ExerciseAttempt.user_id == self._parse_uuid(user_id), ExerciseAttempt.is_correct.is_not(None)
        ).order_by(ExerciseAttempt.created_at.desc())
        if skill_id:
            query = query.where(Exercise.skill_id == self._parse_uuid(skill_id))
        rows = list((await self.db.execute(query.limit(limit * 5))).all())
        grouped: dict[uuid.UUID, list[tuple[ExerciseAttempt, Exercise]]] = {}
        for attempt, exercise in rows:
            grouped.setdefault(exercise.id, []).append((attempt, exercise))
        history: list[ExerciseHistoryItem] = []
        for entries in list(grouped.values())[:limit]:
            exercise = entries[0][1]; attempts = [entry[0] for entry in entries]
            history.append(ExerciseHistoryItem(
                exercise_id=str(exercise.id), exercise_title=exercise.title, exercise_type=exercise.exercise_type,
                skill_id=str(exercise.skill_id) if exercise.skill_id else None,
                skill_name=exercise.skill.name if exercise.skill else None,
                best_score=max(float(item.score or 0) for item in attempts), attempts=len(attempts),
                is_completed=any(bool(item.is_correct) for item in attempts),
                last_attempted_at=max(item.created_at for item in attempts),
            ))
        return history

    async def get_skill_exercise_stats(self, user_id: str, skill_id: str) -> ExerciseStatsResponse:
        rows = list((await self.db.execute(
            select(ExerciseAttempt, Exercise).join(Exercise).where(
                ExerciseAttempt.user_id == self._parse_uuid(user_id), Exercise.skill_id == self._parse_uuid(skill_id),
                ExerciseAttempt.is_correct.is_not(None),
            ).order_by(ExerciseAttempt.created_at)
        )).all())
        grouped: dict[uuid.UUID, list[tuple[ExerciseAttempt, Exercise]]] = {}
        for row in rows:
            grouped.setdefault(row[1].id, []).append(row)
        averages = [(sum(float(item[0].score or 0) for item in entries) / len(entries), entries[0][1].title) for entries in grouped.values()]
        changes = []
        if rows:
            histories = list((await self.db.execute(
                select(SkillHistory).join(UserSkill).where(
                    UserSkill.user_id == self._parse_uuid(user_id), UserSkill.skill_id == self._parse_uuid(skill_id),
                    SkillHistory.change_reason.like("Exercise attempt%"),
                )
            )).scalars())
            for item in histories:
                match = re.search(r"([+-]\d+\.\d+)$", item.change_reason or "")
                if match:
                    changes.append(float(match.group(1)))
        total = len(rows); correct = sum(bool(item[0].is_correct) for item in rows)
        return ExerciseStatsResponse(
            total_attempted=len(grouped),
            correct_first_try=sum(bool(entries[0][0].is_correct) for entries in grouped.values()),
            total_correct=correct,
            accuracy_rate=round(correct / total * 100, 1) if total else 0,
            average_attempts=round(total / len(grouped), 2) if grouped else 0,
            hardest_exercise=min(averages)[1] if averages else None,
            easiest_exercise=max(averages)[1] if averages else None,
            time_spent_minutes=round(sum(int(item[0].time_spent_seconds or 0) for item in rows) / 60),
            mastery_gained=round(sum(changes), 3),
        )

    async def serialize_exercise_with_attempt(self, exercise: Exercise, user_id: str) -> ExerciseWithAttemptResponse:
        attempts = list((await self.db.execute(select(ExerciseAttempt).where(
            ExerciseAttempt.exercise_id == exercise.id, ExerciseAttempt.user_id == self._parse_uuid(user_id),
            ExerciseAttempt.is_correct.is_not(None),
        ))).scalars())
        return ExerciseWithAttemptResponse(
            **self.serialize_exercise(exercise).model_dump(), user_attempts=len(attempts),
            best_score=max((float(item.score or 0) for item in attempts), default=None),
            is_completed=any(bool(item.is_correct) for item in attempts),
            last_attempted_at=max((item.created_at for item in attempts), default=None),
        )

    @staticmethod
    def serialize_exercise(exercise: Exercise) -> ExerciseResponse:
        return ExerciseResponse(
            id=str(exercise.id), title=exercise.title, exercise_type=exercise.exercise_type,
            difficulty=exercise.difficulty, content=exercise.content, hints=exercise.hints,
            skill_id=str(exercise.skill_id) if exercise.skill_id else None,
            skill_name=exercise.skill.name if exercise.skill else None,
            skill_slug=exercise.skill.slug if exercise.skill else None,
            is_ai_generated=exercise.is_ai_generated,
        )

    async def _evaluate_answer(self, exercise: Exercise, answer: str, attempt_number: int) -> dict[str, Any]:
        if exercise.exercise_type == "multiple_choice":
            correct = answer.strip().casefold() == (exercise.solution or "").strip().casefold()
            return {"score": 1.0 if correct else 0.0, "is_correct": correct, "feedback": str(exercise.content.get("explanation") or ("Correct." if correct else "Review the distinction between the options.")), "detailed_feedback": None}
        if exercise.exercise_type in {"coding", "debugging"}:
            code = answer.split("FIXED CODE:\n", 1)[-1] if exercise.exercise_type == "debugging" else answer
            review = await self.code_review.evaluate_code_solution(exercise, code, exercise.skill.name if exercise.skill else "Python")
            return {"score": review["overall_score"], "is_correct": bool(review.get("is_correct", False)), "feedback": review["summary"], "detailed_feedback": {**review, "formatted": self.code_review.format_feedback_for_display(review, attempt_number)}}
        words = answer.split()
        try:
            result = await self.ai.generate_structured(
                instructions="Evaluate a learner explanation for conceptual accuracy and completeness. Return strict JSON.",
                prompt=f"Question: {exercise.description}\nExpected concepts: {exercise.solution}\nAnswer: {answer}",
                schema_name="explanation_review",
                schema={
                    "type": "object", "properties": {
                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                        "feedback": {"type": "string"}, "covered": {"type": "array", "items": {"type": "string"}},
                        "missing": {"type": "array", "items": {"type": "string"}},
                    }, "required": ["score", "feedback", "covered", "missing"], "additionalProperties": False,
                }, max_output_tokens=600,
            )
            return {"score": result["score"], "is_correct": float(result["score"]) >= .7, "feedback": result["feedback"], "detailed_feedback": result}
        except (AIServiceUnavailable, AIServiceResponseError, APIError, TimeoutError, KeyError, TypeError):
            score = min(1.0, len(words) / 45)
            return {"score": score, "is_correct": score >= .7, "feedback": "Your explanation has useful detail." if score >= .7 else "Add more reasoning and a concrete example.", "detailed_feedback": {"covered": [], "missing": ["More detail and an example"] if score < .7 else []}}

    async def _update_mastery(self, user_id: uuid.UUID, skill_id: uuid.UUID | None, correct: bool, attempt_number: int, attempt_id: uuid.UUID) -> tuple[UserSkill, float]:
        if skill_id is None:
            raise HTTPException(status_code=409, detail="This exercise is not linked to a skill")
        user_skill = (await self.db.execute(select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id))).scalar_one_or_none()
        if user_skill is None:
            user_skill = UserSkill(user_id=user_id, skill_id=skill_id, mastery_score=0, confidence_level=0)
            self.db.add(user_skill); await self.db.flush()
        requested_change = .05 if correct and attempt_number == 1 else .02 if correct else -.03
        old = user_skill.mastery_score
        user_skill.mastery_score = min(1.0, max(0.0, old + requested_change))
        actual_change = user_skill.mastery_score - old
        user_skill.last_practiced_at = datetime.now(timezone.utc)
        user_skill.times_practiced += 1
        user_skill.times_correct += int(correct)
        user_skill.times_incorrect += int(not correct)
        self.db.add(SkillHistory(
            user_skill_id=user_skill.id, mastery_score=user_skill.mastery_score,
            change_reason=f"Exercise attempt {attempt_id}: {actual_change:+.3f}",
        ))
        return user_skill, actual_change

    async def _get_skill(self, skill_id: str) -> Skill:
        skill = await self.db.get(Skill, self._parse_uuid(skill_id))
        if skill is None:
            raise HTTPException(status_code=404, detail="Skill not found")
        return skill

    async def _get_user_skill(self, user_id: str, skill_id: uuid.UUID) -> UserSkill | None:
        return (await self.db.execute(select(UserSkill).where(UserSkill.user_id == self._parse_uuid(user_id), UserSkill.skill_id == skill_id))).scalar_one_or_none()

    async def _get_exercise(self, exercise_id: str, required: bool = True) -> Exercise | None:
        result = await self.db.execute(select(Exercise).options(selectinload(Exercise.skill)).where(Exercise.id == self._parse_uuid(exercise_id)))
        exercise = result.scalars().one_or_none()
        if required and exercise is None:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise

    async def _load_skill_exercises(self, skill_id: uuid.UUID, limit: int) -> list[Exercise]:
        return list((await self.db.execute(select(Exercise).options(selectinload(Exercise.skill)).where(Exercise.skill_id == skill_id).order_by(Exercise.difficulty, Exercise.created_at.desc()).limit(limit))).scalars())

    async def _recent_incorrect_answers(self, user_id: str, skill_id: uuid.UUID) -> list[dict[str, str]]:
        rows = (await self.db.execute(select(ExerciseAttempt, Exercise).join(Exercise).where(
            ExerciseAttempt.user_id == self._parse_uuid(user_id), Exercise.skill_id == skill_id,
            ExerciseAttempt.is_correct.is_(False),
        ).order_by(ExerciseAttempt.created_at.desc()).limit(10))).all()
        return [{"exercise": exercise.title, "answer": attempt.user_answer or ""} for attempt, exercise in rows]

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid identifier") from exc

    @staticmethod
    def _generation_schema(count: int) -> dict[str, Any]:
        nullable_string = {"type": ["string", "null"]}
        return {
            "type": "object", "properties": {"exercises": {
                "type": "array", "minItems": count, "maxItems": count, "items": {
                    "type": "object", "properties": {
                        "title": {"type": "string"}, "exercise_type": {"type": "string", "enum": ["multiple_choice", "explanation", "debugging", "coding"]},
                        "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
                        "content": {"type": "object", "properties": {
                            "problem_statement": {"type": "string"}, "starter_code": nullable_string,
                            "test_cases": {"type": ["array", "null"], "items": {"type": "object", "properties": {"input": {"type": "string"}, "expected_output": {"type": "string"}, "description": {"type": "string"}}, "required": ["input", "expected_output", "description"], "additionalProperties": False}},
                            "constraints": {"type": ["array", "null"], "items": {"type": "string"}},
                            "example_input": nullable_string, "example_output": nullable_string,
                            "options": {"type": ["array", "null"], "items": {"type": "string"}},
                            "explanation": nullable_string, "buggy_code": nullable_string,
                        }, "required": ["problem_statement", "starter_code", "test_cases", "constraints", "example_input", "example_output", "options", "explanation", "buggy_code"], "additionalProperties": False},
                        "solution": {"type": "string"}, "hints": {"type": "array", "items": {"type": "string"}},
                    }, "required": ["title", "exercise_type", "difficulty", "content", "solution", "hints"], "additionalProperties": False,
                }}}, "required": ["exercises"], "additionalProperties": False,
        }

    @staticmethod
    def _fallback_exercises(skill: Skill, count: int, difficulty: int) -> list[dict[str, Any]]:
        templates = [
            {"title": f"{skill.name}: choose the best explanation", "exercise_type": "multiple_choice", "content": {"problem_statement": f"Which statement best describes a sound use of {skill.name}?", "options": [f"Apply {skill.name} deliberately and verify the result", "Ignore inputs and edge cases", "Memorize output without reasoning", "Avoid testing assumptions"], "explanation": "A reliable approach applies the concept deliberately and checks the outcome."}, "solution": f"Apply {skill.name} deliberately and verify the result", "hints": ["Look for the option that includes verification.", "Good technical work checks assumptions and results."]},
            {"title": f"Explain {skill.name} in your own words", "exercise_type": "explanation", "content": {"problem_statement": f"Explain {skill.name} to a beginner using at least one concrete example."}, "solution": f"A clear definition of {skill.name}, its purpose, and a concrete example", "hints": ["Start with the problem the concept solves.", "Add one small input-to-output example."]},
            {"title": f"Debug a {skill.name} function", "exercise_type": "debugging", "content": {"problem_statement": "Find the syntax bug, describe it, and submit corrected code.", "buggy_code": "def transform(values):\n    for value in values\n        print(value)\n    return values", "starter_code": "def transform(values):\n    for value in values:\n        print(value)\n    return values"}, "solution": "Add the missing colon after `for value in values`.", "hints": ["Inspect the line that begins the loop.", "Python block headers end with a colon."]},
            {"title": f"Write a focused {skill.name} solution", "exercise_type": "coding", "content": {"problem_statement": "Write a Python function `transform(values)` that returns a new list containing only positive values, doubled.", "starter_code": "def transform(values):\n    # Return doubled positive values\n    pass", "test_cases": [{"input": "[-2, 0, 3, 5]", "expected_output": "[6, 10]", "description": "Mixed values"}], "constraints": ["Do not mutate the input list"], "example_input": "[-2, 0, 3, 5]", "example_output": "[6, 10]"}, "solution": "Use a filtered list comprehension and multiply each retained value by two.", "hints": ["Filter with `if value > 0`.", "A list comprehension can filter and transform together."]},
        ]
        result = []
        for index in range(count):
            item = json.loads(json.dumps(templates[index % len(templates)]))
            item["title"] = f"{item['title']} #{index + 1}"
            item["difficulty"] = min(5, max(1, difficulty + (index % 3) - 1))
            content = item["content"]
            for key in ("starter_code", "test_cases", "constraints", "example_input", "example_output", "options", "explanation", "buggy_code"):
                content.setdefault(key, None)
            result.append(item)
        return result
