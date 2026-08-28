import asyncio

from app.models.project import ProjectStage
from app.services.project_evaluator import ProjectEvaluator
from app.services.project_mentor_service import ProjectMentorService


def test_stage_xp_rewards_quality_and_penalizes_hints() -> None:
    assert asyncio.run(ProjectEvaluator.calculate_xp_for_stage(1.0, 0, 0)) == 100
    assert asyncio.run(ProjectEvaluator.calculate_xp_for_stage(0.5, 2, 2)) == 55
    assert asyncio.run(ProjectEvaluator.calculate_xp_for_stage(0.0, 3, 20)) == 10


def test_stage_fallback_requires_substantive_code() -> None:
    stage = ProjectStage(validation_criteria=["Loads CSV data", "Validates required columns"])
    incomplete = ProjectMentorService._fallback_evaluation(stage, "pass", "")
    complete = ProjectMentorService._fallback_evaluation(stage, "def load(path):\n    return [row for row in path if row is not None]\n" * 2, "Tested missing rows")
    assert incomplete["passed"] is False
    assert complete["passed"] is True
    assert len(complete["criteria_evaluation"]) == 2


def test_complete_solution_guard_detects_large_targeted_code_block() -> None:
    stage = ProjectStage(validation_criteria=["validate columns", "handle missing values", "create summary table"])
    code = "\n".join(["validate columns and handle missing values then create summary table"] * 12)
    assert ProjectMentorService._reveals_solution(f"```python\n{code}\n```", stage) is True
    assert ProjectMentorService._reveals_solution("Try inspecting one intermediate value first.", stage) is False
