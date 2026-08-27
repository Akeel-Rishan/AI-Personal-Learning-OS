"""Exercise generation, attempt, feedback, and review schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ExerciseContentSchema(BaseModel):
    problem_statement: str
    starter_code: str | None = None
    test_cases: list[dict[str, object]] | None = None
    constraints: list[str] | None = None
    example_input: str | None = None
    example_output: str | None = None
    options: list[str] | None = None
    explanation: str | None = None
    buggy_code: str | None = None


class ExerciseResponse(BaseModel):
    id: str
    title: str
    exercise_type: str
    difficulty: int
    content: dict[str, object]
    hints: list[str] | None
    skill_id: str | None
    skill_name: str | None
    skill_slug: str | None
    is_ai_generated: bool


class ExerciseWithAttemptResponse(ExerciseResponse):
    user_attempts: int = 0
    best_score: float | None = None
    is_completed: bool = False
    last_attempted_at: datetime | None = None


class AttemptRequest(BaseModel):
    user_answer: str = Field(min_length=1, max_length=20_000)
    time_spent_seconds: int = Field(ge=0, le=86_400)

    @field_validator("user_answer")
    @classmethod
    def clean_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Answer cannot be empty")
        return value


class AttemptFeedbackResponse(BaseModel):
    attempt_id: str
    is_correct: bool
    score: float
    feedback: str
    correct_answer: str | None
    detailed_feedback: dict[str, object] | None
    mastery_change: float
    new_mastery: float
    hint_available: bool
    next_hint: str | None
    attempt_number: int
    mastery_percentage: int
    weakness_detected: dict[str, object] | None = None
    adaptation_triggered: bool = False
    adaptation: dict[str, object] | None = None


class HintResponse(BaseModel):
    hint: str
    hint_number: int
    total_hints: int


class ExerciseGenerateRequest(BaseModel):
    skill_id: str
    count: int = Field(default=5, ge=1, le=10)
    difficulty: int | None = Field(default=None, ge=1, le=5)


class CodeReviewRequest(BaseModel):
    code: str = Field(min_length=10, max_length=20_000)
    context: str = Field(default="", max_length=2_000)
    skill_id: str | None = None


class CodeReviewResponse(BaseModel):
    overall_score: float
    is_correct: bool | None
    correctness_score: float | None = None
    quality_score: float | None = None
    style_score: float | None = None
    performance_score: float | None = None
    passed_test_cases: int | None = None
    total_test_cases: int | None = None
    summary: str
    strengths: list[str]
    improvements: list[dict[str, object]]
    better_approach: str | None
    learning_note: str
    formatted: dict[str, object]


class ExerciseStatsResponse(BaseModel):
    total_attempted: int
    correct_first_try: int
    total_correct: int
    accuracy_rate: float
    average_attempts: float
    hardest_exercise: str | None = None
    easiest_exercise: str | None = None
    time_spent_minutes: int
    mastery_gained: float


class RecommendedExerciseResponse(BaseModel):
    exercise: ExerciseWithAttemptResponse
    skill_name: str
    skill_slug: str
    skill_mastery: float
    reason: str


class ExerciseHistoryItem(BaseModel):
    exercise_id: str
    exercise_title: str
    exercise_type: str
    skill_id: str | None
    skill_name: str | None
    best_score: float
    attempts: int
    is_completed: bool
    last_attempted_at: datetime
