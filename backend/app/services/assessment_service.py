"""Assessment lifecycle, answer persistence, and skill mastery scoring."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment, AssessmentAttempt, AssessmentQuestion
from app.models.goal import Goal, GoalSkill
from app.models.progress import SkillHistory, UserSkill
from app.models.skill import Skill
from app.schemas.assessment import (
    AnswerFeedbackResponse,
    AssessmentQuestionResponse,
    AssessmentResultsResponse,
    AssessmentStatusResponse,
    SkillScoreResult,
)
from app.services.answer_evaluator import AnswerEvaluator
from app.services.question_generator import QuestionGenerator


class AssessmentService:
    """Coordinate an owned assessment from generation through mastery updates."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.generator = QuestionGenerator()
        self.evaluator = AnswerEvaluator()

    async def create_initial_assessment(self, user_id: str, goal_id: str) -> Assessment:
        """Create one diagnostic assessment for an owned goal, or reuse the latest one."""

        parsed_goal = self._parse_uuid(goal_id)
        parsed_user = self._parse_uuid(user_id)
        existing = await self.get_by_goal(goal_id, user_id)
        if existing is not None:
            return existing

        goal_result = await self.db.execute(
            select(Goal)
            .options(selectinload(Goal.goal_skills).selectinload(GoalSkill.skill))
            .where(Goal.id == parsed_goal, Goal.user_id == parsed_user)
        )
        goal = goal_result.scalars().unique().one_or_none()
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        links = sorted(goal.goal_skills, key=lambda item: item.priority_order)
        skills = [link.skill for link in links]
        if not skills:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Create the goal skill plan before starting an assessment.",
            )

        generated = await self.generator.generate_initial_assessment(
            skills,
            goal.existing_knowledge,
        )
        if not generated:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Assessment questions could not be generated.",
            )

        now = datetime.now(timezone.utc)
        assessment = Assessment(
            user_id=parsed_user,
            goal_id=parsed_goal,
            assessment_type="initial",
            status="in_progress",
            total_questions=len(generated),
            completed_questions=0,
            started_at=now,
        )
        self.db.add(assessment)
        await self.db.flush()
        for index, item in enumerate(generated):
            self.db.add(
                AssessmentQuestion(
                    assessment_id=assessment.id,
                    skill_id=item["skill_id"],
                    question_type=item["question_type"],
                    question_text=item["question_text"],
                    options=item.get("options"),
                    correct_answer=item.get("correct_answer"),
                    explanation=item.get("explanation"),
                    difficulty=item["difficulty"],
                    order_index=index,
                )
            )
        await self.db.commit()
        created = await self.get_assessment(str(assessment.id), user_id)
        if created is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Assessment was not saved")
        return created

    async def get_by_goal(self, goal_id: str, user_id: str) -> Assessment | None:
        parsed_goal = self._try_uuid(goal_id)
        parsed_user = self._try_uuid(user_id)
        if parsed_goal is None or parsed_user is None:
            return None
        result = await self.db.execute(
            self._assessment_query()
            .where(Assessment.goal_id == parsed_goal, Assessment.user_id == parsed_user)
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        return result.scalars().unique().one_or_none()

    async def get_assessment(self, assessment_id: str, user_id: str) -> Assessment | None:
        parsed_assessment = self._try_uuid(assessment_id)
        parsed_user = self._try_uuid(user_id)
        if parsed_assessment is None or parsed_user is None:
            return None
        result = await self.db.execute(
            self._assessment_query().where(
                Assessment.id == parsed_assessment,
                Assessment.user_id == parsed_user,
            )
        )
        return result.scalars().unique().one_or_none()

    async def get_next_question(
        self,
        assessment_id: str,
        user_id: str,
    ) -> AssessmentQuestion | None:
        """Return the first unanswered question for an owned assessment."""

        assessment = await self.get_assessment(assessment_id, user_id)
        return None if assessment is None else self._next_question(assessment)

    async def submit_answer(
        self,
        assessment_id: str,
        question_id: str,
        user_answer: str,
        time_spent_seconds: int | None,
        user_id: str,
    ) -> AnswerFeedbackResponse:
        assessment = await self.get_assessment(assessment_id, user_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        if assessment.status == "completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment is already complete")
        parsed_question = self._parse_uuid(question_id)
        question = next((item for item in assessment.questions if item.id == parsed_question), None)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        if any(attempt.question_id == parsed_question for attempt in assessment.attempts):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")

        evaluation = await self.evaluator.evaluate_answer(question, user_answer)
        attempt = AssessmentAttempt(
            assessment=assessment,
            question=question,
            user_answer=user_answer.strip() or None,
            is_correct=evaluation["is_correct"],
            score=evaluation["score"],
            ai_feedback=evaluation["feedback"],
            time_spent_seconds=time_spent_seconds,
        )
        self.db.add(attempt)
        await self.db.flush()
        assessment.completed_questions = len(assessment.attempts)
        completed = assessment.completed_questions >= assessment.total_questions
        if completed:
            await self._finalize_loaded(assessment)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered") from exc

        next_question = None if completed else self._next_question(assessment)
        return AnswerFeedbackResponse(
            question_id=str(question.id),
            score=evaluation["score"],
            is_correct=evaluation["is_correct"],
            feedback=evaluation["feedback"],
            correct_answer=question.correct_answer or "",
            completed_questions=assessment.completed_questions,
            total_questions=assessment.total_questions,
            is_assessment_complete=completed,
            assessment_completed=completed,
            next_question=self.serialize_question(next_question) if next_question else None,
        )

    async def get_results(self, assessment_id: str, user_id: str) -> AssessmentResultsResponse:
        assessment = await self.get_assessment(assessment_id, user_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        if assessment.status != "completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment is not complete")
        return self.serialize_results(assessment)

    async def finalize_assessment(self, assessment_id: str, user_id: str) -> AssessmentResultsResponse:
        """Finalize a fully answered owned assessment and return its skill profile."""

        assessment = await self.get_assessment(assessment_id, user_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        if assessment.status != "completed":
            if len(assessment.attempts) < assessment.total_questions:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment is not complete")
            await self._finalize_loaded(assessment)
            await self.db.commit()
        return self.serialize_results(assessment)

    async def _finalize_loaded(self, assessment: Assessment) -> None:
        now = datetime.now(timezone.utc)
        grouped: dict[uuid.UUID, list[AssessmentAttempt]] = defaultdict(list)
        for attempt in assessment.attempts:
            if attempt.question.skill_id is not None:
                grouped[attempt.question.skill_id].append(attempt)

        for skill_id, attempts in grouped.items():
            mastery = self._calculate_skill_score(attempts)
            confidence = min(1.0, len(attempts) / 3)
            result = await self.db.execute(
                select(UserSkill).where(
                    UserSkill.user_id == assessment.user_id,
                    UserSkill.skill_id == skill_id,
                )
            )
            user_skill = result.scalar_one_or_none()
            if user_skill is None:
                user_skill = UserSkill(user_id=assessment.user_id, skill_id=skill_id)
                self.db.add(user_skill)
                await self.db.flush()
            user_skill.mastery_score = mastery
            user_skill.confidence_level = confidence
            user_skill.times_practiced += len(attempts)
            user_skill.times_correct += sum(bool(item.is_correct) for item in attempts)
            user_skill.times_incorrect += sum(not bool(item.is_correct) for item in attempts)
            user_skill.last_assessed_at = now
            user_skill.is_completed = mastery >= 0.8
            self.db.add(
                SkillHistory(
                    user_skill=user_skill,
                    mastery_score=mastery,
                    change_reason="Initial skill assessment",
                    recorded_at=now,
                )
            )

        assessment.score_percentage = self._weighted_score(assessment.attempts)
        assessment.status = "completed"
        assessment.completed_questions = assessment.total_questions
        assessment.completed_at = now

    @classmethod
    def _calculate_skill_score(cls, attempts: Iterable[AssessmentAttempt]) -> float:
        items = list(attempts)
        score = cls._weighted_score(items)
        if len(items) < 3:
            score *= 0.85
        return round(min(1.0, max(0.0, score)), 4)

    async def calculate_skill_score(
        self,
        attempts: list[AssessmentAttempt],
        questions: list[AssessmentQuestion] | None = None,
    ) -> float:
        """Calculate mastery using the documented difficulty weighting formula."""

        del questions
        return self._calculate_skill_score(attempts)

    @staticmethod
    def _weighted_score(attempts: Iterable[AssessmentAttempt]) -> float:
        items = list(attempts)
        total_weight = sum(max(1, item.question.difficulty) for item in items)
        if not total_weight:
            return 0.0
        earned = sum((item.score or 0.0) * max(1, item.question.difficulty) for item in items)
        return round(earned / total_weight, 4)

    @classmethod
    def serialize_status(cls, assessment: Assessment) -> AssessmentStatusResponse:
        next_question = cls._next_question(assessment)
        current = cls.serialize_question(next_question) if next_question else None
        progress = (
            assessment.completed_questions / assessment.total_questions * 100
            if assessment.total_questions
            else 0.0
        )
        return AssessmentStatusResponse(
            id=str(assessment.id),
            goal_id=str(assessment.goal_id) if assessment.goal_id else None,
            goal_title=assessment.goal.title if assessment.goal else None,
            assessment_type=assessment.assessment_type,
            status=assessment.status,
            total_questions=assessment.total_questions,
            completed_questions=assessment.completed_questions,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at,
            current_question=current,
            progress_percentage=round(progress, 1),
            next_question=current,
        )

    @staticmethod
    def serialize_question(question: AssessmentQuestion) -> AssessmentQuestionResponse:
        return AssessmentQuestionResponse(
            id=str(question.id),
            skill_id=str(question.skill_id) if question.skill_id else None,
            skill_name=question.skill.name if question.skill else "General",
            skill_category=question.skill.category if question.skill else "general",
            question_type=question.question_type,
            question_text=question.question_text,
            options=question.options,
            difficulty=question.difficulty,
            order_index=question.order_index,
        )

    @classmethod
    def serialize_results(cls, assessment: Assessment) -> AssessmentResultsResponse:
        grouped: dict[uuid.UUID, list[AssessmentAttempt]] = defaultdict(list)
        for attempt in assessment.attempts:
            if attempt.question.skill_id is not None:
                grouped[attempt.question.skill_id].append(attempt)
        skill_scores: list[SkillScoreResult] = []
        for skill_id, attempts in grouped.items():
            skill = attempts[0].question.skill
            score = cls._calculate_skill_score(attempts)
            percentage = round(score * 100, 1)
            skill_scores.append(
                SkillScoreResult(
                    skill_id=str(skill_id),
                    skill_name=skill.name if skill else "General",
                    skill_slug=skill.slug if skill else "general",
                    category=skill.category if skill else "general",
                    mastery_score=score,
                    mastery_percentage=percentage,
                    questions_count=len(attempts),
                    correct_count=sum(bool(item.is_correct) for item in attempts),
                    confidence=round(min(1.0, len(attempts) / 3), 4),
                    level=(
                        "advanced" if score >= 0.8 else "intermediate" if score >= 0.5 else "beginner"
                    ),
                )
            )
        skill_scores.sort(key=lambda item: item.mastery_percentage, reverse=True)
        score = assessment.score_percentage or 0.0
        return AssessmentResultsResponse(
            assessment_id=str(assessment.id),
            goal_id=str(assessment.goal_id) if assessment.goal_id else None,
            goal_title=assessment.goal.title if assessment.goal else None,
            status=assessment.status,
            overall_score=round(score * 100, 1),
            total_questions=assessment.total_questions,
            correct_answers=sum(bool(item.is_correct) for item in assessment.attempts),
            completed_at=assessment.completed_at,
            skill_scores=skill_scores,
            strong_skills=[item for item in skill_scores if item.mastery_score >= 0.7],
            weak_skills=[item for item in skill_scores if item.mastery_score < 0.5],
        )

    @staticmethod
    def _next_question(assessment: Assessment) -> AssessmentQuestion | None:
        answered = {attempt.question_id for attempt in assessment.attempts}
        return next(
            (question for question in sorted(assessment.questions, key=lambda item: item.order_index) if question.id not in answered),
            None,
        )

    @staticmethod
    def _assessment_query():
        return select(Assessment).options(
            selectinload(Assessment.goal),
            selectinload(Assessment.questions).selectinload(AssessmentQuestion.skill),
            selectinload(Assessment.attempts)
            .selectinload(AssessmentAttempt.question)
            .selectinload(AssessmentQuestion.skill),
        )

    @staticmethod
    def _try_uuid(value: str) -> uuid.UUID | None:
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _parse_uuid(cls, value: str) -> uuid.UUID:
        parsed = cls._try_uuid(value)
        if parsed is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid identifier")
        return parsed
