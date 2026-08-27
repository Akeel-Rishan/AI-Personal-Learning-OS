"""Spaced-repetition interval, retention, and urgency tests."""

from datetime import datetime, timedelta, timezone

from app.services.spaced_repetition import SpacedRepetitionScheduler


def test_mastery_interval_boundaries() -> None:
    scheduler = SpacedRepetitionScheduler()
    assert scheduler.get_review_interval_days(0.39) == 1
    assert scheduler.get_review_interval_days(0.4) == 3
    assert scheduler.get_review_interval_days(0.8) == 14
    assert scheduler.get_review_interval_days(1.0) == 30


def test_high_mastery_skill_is_due_after_fifteen_days() -> None:
    scheduler = SpacedRepetitionScheduler()
    practiced = datetime.now(timezone.utc) - timedelta(days=15)
    result = scheduler.get_skills_due_for_review(
        [{"skill_id": "1", "skill_name": "NumPy", "mastery_score": 0.8, "last_practiced_at": practiced, "times_practiced": 5}]
    )
    assert len(result) == 1
    assert result[0]["days_overdue"] >= 1


def test_unpracticed_and_very_low_mastery_skills_are_not_reviews() -> None:
    scheduler = SpacedRepetitionScheduler()
    old = datetime.now(timezone.utc) - timedelta(days=100)
    result = scheduler.get_skills_due_for_review(
        [
            {"skill_id": "1", "skill_name": "New", "mastery_score": 0.8, "last_practiced_at": None},
            {"skill_id": "2", "skill_name": "Low", "mastery_score": 0.2, "last_practiced_at": old},
        ]
    )
    assert result == []
