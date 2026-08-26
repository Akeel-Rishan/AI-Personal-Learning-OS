"""Assessment API request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssessmentCreateRequest(BaseModel):
    goal_id: str


class QuestionResponse(BaseModel):
    id: str
    skill_id: str | None
    skill_name: str
    skill_category: str
    question_type: str
    question_text: str
    options: list[str] | None
    difficulty: int
    order_index: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "skill_id", mode="before")
    @classmethod
    def stringify_ids(cls, value: object) -> str | None:
        return None if value is None else str(value)


class AssessmentStatusResponse(BaseModel):
    id: str
    goal_id: str | None
    goal_title: str | None
    assessment_type: str
    status: str
    total_questions: int
    completed_questions: int
    started_at: datetime | None
    completed_at: datetime | None
    current_question: QuestionResponse | None = None
    progress_percentage: float
    next_question: QuestionResponse | None = None


class AnswerSubmitRequest(BaseModel):
    question_id: str
    user_answer: str = Field(default="", max_length=12000)
    time_spent_seconds: int | None = Field(default=None, ge=0, le=86400)


class AnswerFeedbackResponse(BaseModel):
    question_id: str
    score: float
    is_correct: bool
    feedback: str
    correct_answer: str
    completed_questions: int
    total_questions: int
    is_assessment_complete: bool
    assessment_completed: bool
    next_question: QuestionResponse | None = None


class SkillScoreResult(BaseModel):
    skill_id: str
    skill_name: str
    skill_slug: str
    category: str
    mastery_score: float
    mastery_percentage: float
    questions_count: int
    correct_count: int
    confidence: float
    level: str


class AssessmentResultsResponse(BaseModel):
    assessment_id: str
    goal_id: str | None
    goal_title: str | None
    status: str
    overall_score: float
    total_questions: int
    correct_answers: int
    completed_at: datetime | None
    skill_scores: list[SkillScoreResult]
    strong_skills: list[SkillScoreResult]
    weak_skills: list[SkillScoreResult]


AssessmentQuestionResponse = QuestionResponse
