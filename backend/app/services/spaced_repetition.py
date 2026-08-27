"""SM-2-inspired spaced repetition scheduling helpers."""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any


class SpacedRepetitionScheduler:
    """Determine which practiced skills need reinforcement today."""

    REVIEW_INTERVALS = {
        (0.0, 0.4): 1,
        (0.4, 0.6): 3,
        (0.6, 0.75): 7,
        (0.75, 0.9): 14,
        (0.9, 1.0): 30,
    }

    def get_review_interval_days(self, mastery_score: float) -> int:
        score = min(1.0, max(0.0, mastery_score))
        for (low, high), days in self.REVIEW_INTERVALS.items():
            if low <= score < high:
                return days
        return 30

    @staticmethod
    def calculate_retention(mastery_score: float, days_since_practice: int) -> float:
        score = min(1.0, max(0.0, mastery_score))
        stability = max(1.0, score * 30)
        retention = score * math.exp(-max(0, days_since_practice) / stability)
        return round(min(1.0, max(0.1, retention)), 4)

    def get_skills_due_for_review(
        self,
        user_skills: list[dict[str, Any]],
        max_review_items: int = 3,
    ) -> list[dict[str, Any]]:
        today = datetime.now(timezone.utc).date()
        due: list[dict[str, Any]] = []
        for skill in user_skills:
            score = float(skill.get("mastery_score", 0.0))
            practiced = self._parse_date(skill.get("last_practiced_at"))
            if practiced is None or score <= 0.2:
                continue
            days_since = max(0, (today - practiced).days)
            interval = self.get_review_interval_days(score)
            if days_since < interval:
                continue
            retention = self.calculate_retention(score, days_since)
            due.append(
                {
                    **skill,
                    "retention_estimate": retention,
                    "days_since_practice": days_since,
                    "days_overdue": days_since - interval,
                    "review_type": "quick_review" if retention >= 0.5 else "full_review",
                    "urgency": (days_since - interval + 1) / interval,
                }
            )
        due.sort(key=lambda item: (-float(item["urgency"]), float(item["retention_estimate"])))
        return [{key: value for key, value in item.items() if key != "urgency"} for item in due[:max_review_items]]

    @staticmethod
    def estimate_review_time_minutes(review_type: str, mastery_score: float) -> int:
        score = min(1.0, max(0.0, mastery_score))
        if review_type == "quick_review":
            return round(15 - (score * 5))
        return round(30 - (score * 10))

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).date() if value.tzinfo else value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except ValueError:
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    return None
        return None
