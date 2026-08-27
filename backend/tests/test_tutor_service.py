"""Tutor prompt personalization and fallback behavior tests."""

import asyncio

from app.services.tutor_service import TutorService


CONTEXT = {
    "user_name": "Alex",
    "goal_title": "Machine Learning Engineer",
    "preferred_style": "visual",
    "daily_minutes": 60,
    "current_phase": "Statistics Foundations",
    "current_focus_skills": ["Statistics"],
    "skill_mastery": [{"name": "Statistics", "mastery": 0.32, "level": "weak"}],
    "strong_skills": ["Python"],
    "weak_skills": ["Statistics"],
    "today_plan_items": ["Statistics introduction"],
    "recent_mistakes": [],
}


def test_explanation_prompt_contains_full_learner_context() -> None:
    service = TutorService(None)  # type: ignore[arg-type]
    prompt = asyncio.run(service.build_system_prompt(CONTEXT, False, "Statistics"))
    assert "Alex" in prompt
    assert "Machine Learning Engineer" in prompt
    assert "Statistics: 32% (weak)" in prompt
    assert "EXPLANATION MODE" in prompt
    assert "spatial descriptions" in prompt


def test_socratic_prompt_changes_teaching_contract() -> None:
    service = TutorService(None)  # type: ignore[arg-type]
    prompt = asyncio.run(service.build_system_prompt(CONTEXT, True, "Statistics"))
    assert "SOCRATIC MODE IS ENABLED" in prompt
    assert "Never give direct answers" in prompt
    assert "2-3 guided exchanges" in prompt


def test_offline_fallback_remains_personalized_and_mode_aware() -> None:
    direct = TutorService._fallback_tutor_response(CONTEXT, "Explain variance", False, "Statistics")
    socratic = TutorService._fallback_tutor_response(CONTEXT, "Explain variance", True, "Statistics")
    assert "Alex" in direct and "Statistics" in direct
    assert "reason through" in socratic
    assert direct != socratic


def test_long_context_is_compacted_but_keeps_last_twenty_messages() -> None:
    service = TutorService(None)  # type: ignore[arg-type]
    service.ai.client = None
    history = [
        {"role": "user" if index % 2 == 0 else "assistant", "content": f"message-{index}:" + "x" * 30_000}
        for index in range(22)
    ]
    compacted = asyncio.run(service._manage_context_window(history))
    assert len(compacted) == 21
    assert compacted[0]["content"].startswith("Earlier conversation summary:")
    assert compacted[-1] == history[-1]
