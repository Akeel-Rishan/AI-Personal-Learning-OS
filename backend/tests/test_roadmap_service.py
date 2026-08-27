"""Unit tests for stable prerequisite ordering."""

from app.services.roadmap_service import RoadmapService


def skills(*ids: str) -> list[dict[str, str]]:
    return [{"skill_id": skill_id, "name": skill_id} for skill_id in ids]


def ordered_ids(items: list[dict[str, str]]) -> list[str]:
    return [item["skill_id"] for item in items]


def test_topological_sort_respects_clear_dependencies() -> None:
    result = RoadmapService.topological_sort_skills(
        skills("python", "numpy", "stats", "ml", "deployment"),
        {"numpy": ["python"], "ml": ["numpy", "stats"], "deployment": ["ml"]},
    )
    order = ordered_ids(result)
    assert order.index("python") < order.index("numpy") < order.index("ml")
    assert order.index("stats") < order.index("ml") < order.index("deployment")


def test_skill_without_prerequisites_appears_first() -> None:
    result = RoadmapService.topological_sort_skills(
        skills("foundation", "advanced"),
        {"advanced": ["foundation"]},
    )
    assert ordered_ids(result) == ["foundation", "advanced"]


def test_circular_dependency_is_handled_gracefully() -> None:
    result = RoadmapService.topological_sort_skills(
        skills("independent", "a", "b"),
        {"a": ["b"], "b": ["a"]},
    )
    assert ordered_ids(result) == ["independent", "a", "b"]
