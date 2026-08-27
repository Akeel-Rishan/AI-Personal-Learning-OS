"""Exercise generation fallback tests."""

import uuid

from app.models.skill import Skill
from app.services.exercise_service import ExerciseService


def test_fallback_generation_produces_requested_mix_and_complete_content() -> None:
    skill = Skill(id=uuid.uuid4(), name="Python Functions", slug="python-functions", description="Define and call reusable functions.", category="programming", difficulty_level=2)
    exercises = ExerciseService._fallback_exercises(skill, 8, 3)
    assert len(exercises) == 8
    assert {item["exercise_type"] for item in exercises} == {"multiple_choice", "explanation", "debugging", "coding"}
    assert all(1 <= item["difficulty"] <= 5 for item in exercises)
    assert all(item["hints"] for item in exercises)
    assert all("problem_statement" in item["content"] for item in exercises)


def test_generation_schema_requires_exact_requested_count() -> None:
    schema = ExerciseService._generation_schema(5)
    items = schema["properties"]["exercises"]
    assert items["minItems"] == 5
    assert items["maxItems"] == 5
