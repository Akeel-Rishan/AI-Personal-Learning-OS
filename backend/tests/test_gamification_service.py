"""Pure XP level calculations."""

from app.services.gamification_service import GamificationService


def test_level_boundaries_are_monotonic() -> None:
    calculate = GamificationService.calculate_level
    assert calculate(0)["level"] == 1
    assert calculate(99)["level"] == 1
    assert calculate(100)["level"] == 2
    assert calculate(299)["level"] == 2
    assert calculate(300)["level"] == 3
    assert calculate(600)["level"] == 4


def test_level_progress_fields_are_consistent() -> None:
    result = GamificationService.calculate_level(175)
    assert result["level"] == 2
    assert result["xp_for_current_level"] == 100
    assert result["xp_for_next_level"] == 300
    assert result["xp_progress"] == 75
    assert result["xp_needed"] == 125
    assert result["progress_percentage"] == 37.5
