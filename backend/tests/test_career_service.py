import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.career_service import CareerService


def requirement(importance: str, current_id, minimum: float, target: float):
    skill = SimpleNamespace(
        id=current_id,
        name=f"Skill {importance}",
        slug=f"skill-{importance}",
        category="technical",
        estimated_hours=20,
    )
    return SimpleNamespace(
        skill=skill,
        importance=importance,
        min_mastery_required=minimum,
        target_mastery=target,
        relevance_note="Required for the role",
    )


def test_weighted_readiness_and_status_buckets():
    essential_id, important_id, optional_id = uuid4(), uuid4(), uuid4()
    role = SimpleNamespace(
        id=uuid4(), title="Test Engineer", slug="test-engineer",
        skill_requirements=[
            requirement("essential", essential_id, 0.7, 0.8),
            requirement("important", important_id, 0.6, 0.8),
            requirement("optional", optional_id, 0.4, 0.5),
        ],
    )
    result = CareerService.calculate_readiness_from_inputs(
        role, {str(essential_id): 0.8, str(important_id): 0.6, str(optional_id): 0.0}
    )
    # (1*3 + .75*2 + 0*.5) / 5.5
    assert result["overall_readiness_percentage"] == 82
    assert len(result["ready_skills"]) == 2
    assert len(result["not_started_skills"]) == 1
    assert result["essential_readiness"] == 1.0


def test_empty_mastery_is_zero_and_estimates_time():
    skill_id = uuid4()
    role = SimpleNamespace(
        id=uuid4(), title="Data Scientist", slug="data-scientist",
        skill_requirements=[requirement("essential", skill_id, 0.7, 0.8)],
    )
    result = CareerService.calculate_readiness_from_inputs(role, {}, daily_minutes=60)
    assert result["overall_readiness_percentage"] == 0
    assert result["readiness_level"] == "just_starting"
    assert result["critical_gaps"][0]["gap_percentage"] == 70
    assert result["estimated_weeks_to_ready"] == 2


def test_one_ready_python_skill_does_not_overstate_role_readiness():
    ids = [uuid4() for _ in range(8)]
    role = SimpleNamespace(
        id=uuid4(), title="Machine Learning Engineer", slug="ml-engineer",
        skill_requirements=[requirement("essential", skill_id, 0.85, 0.95) for skill_id in ids],
    )
    result = CareerService.calculate_readiness_from_inputs(role, {str(ids[0]): 0.88})
    assert result["skills"][0]["status"] == "ready"
    assert all(item["status"] == "not_started" for item in result["skills"][1:])
    assert result["overall_readiness"] < 0.30


def test_explicit_week_estimator_rounds_up():
    service = CareerService(SimpleNamespace())
    weeks = asyncio.run(service.calculate_estimated_weeks([{"gap": 0.3, "estimated_hours": 20}], 60))
    assert weeks == 1
