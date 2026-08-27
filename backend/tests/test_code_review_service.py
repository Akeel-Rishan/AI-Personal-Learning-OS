"""Offline code-review behavior and display formatting tests."""

import asyncio

from app.services.code_review_service import CodeReviewService


def test_fallback_flags_syntax_errors_without_executing_code() -> None:
    service = CodeReviewService()
    service.ai.client = None
    result = asyncio.run(service.review_free_code("def broken(:\n    pass", "Find the problem", "Python", 0.2))
    assert result["overall_score"] < 0.5
    assert result["is_correct"] is None
    assert result["improvements"][0]["severity"] == "critical"
    assert "Syntax error" in result["improvements"][0]["issue"]


def test_fallback_rewards_valid_function_structure() -> None:
    service = CodeReviewService()
    service.ai.client = None
    result = asyncio.run(service.review_free_code('def double(value):\n    """Double one value."""\n    return value * 2', "Review this helper", "Functions", 0.7))
    assert result["overall_score"] >= 0.8
    assert "Valid Python syntax" in result["strengths"]


def test_feedback_formatter_unlocks_solution_after_three_attempts() -> None:
    review = CodeReviewService._fallback_review("not valid python :", "Python", 2, True)
    first = CodeReviewService.format_feedback_for_display(review, 1)
    third = CodeReviewService.format_feedback_for_display(review, 3)
    assert first["show_hint_button"] is True
    assert first["show_solution_button"] is False
    assert third["show_solution_button"] is True
