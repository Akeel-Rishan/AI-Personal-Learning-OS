"""Deterministic knowledge-gap classification and intervention selection."""

class KnowledgeGapClassifier:
    GAP_INTERVENTION_MAP = {
        "conceptual": {"action":"insert_explanation_session","items":["focused_lesson","visual_examples","comprehension_check"],"estimated_minutes":45,"description":"A focused conceptual explanation session with examples"},
        "procedural": {"action":"insert_practice_exercises","items":["step_by_step_exercise","guided_exercise","independent_exercise"],"estimated_minutes":40,"description":"Targeted practice exercises building procedural fluency"},
        "prerequisite": {"action":"insert_prerequisite_review","items":["prerequisite_review","bridge_exercise","skill_check"],"estimated_minutes":35,"description":"Quick review of the prerequisite skill before continuing"},
        "practice_deficit": {"action":"insert_practice_exercises","items":["practice_exercise"]*4,"estimated_minutes":50,"description":"Additional practice to build confidence and accuracy"},
        "retention_decay": {"action":"insert_review_session","items":["spaced_review","recall_exercise","application_exercise"],"estimated_minutes":30,"description":"Spaced repetition review to reinforce fading knowledge"},
    }

    def classify_gap(self, analysis: dict[str, object], misconception: dict[str, object] | None = None) -> dict[str, object]:
        consecutive=int(analysis.get("consecutive_incorrect",0)); accuracy=float(analysis.get("recent_accuracy",analysis.get("overall_accuracy",1.0))); total=int(analysis.get("total_attempts",0))
        if analysis.get("mastery_decay") or int(analysis.get("days_inactive",0)) >= 14: gap_type="retention_decay"
        elif analysis.get("prerequisite_weak"): gap_type="prerequisite"
        elif consecutive >= 3 and accuracy < .4: gap_type="conceptual"
        elif total < 5: gap_type="practice_deficit"
        elif accuracy < .5: gap_type="procedural"
        else: gap_type="conceptual"
        severity="critical" if consecutive>=5 or accuracy<.25 else "high" if consecutive>=3 or accuracy<.4 else "medium" if accuracy<.55 or analysis.get("mastery_trend")=="declining" else "low"
        template=dict(self.GAP_INTERVENTION_MAP[gap_type]); pause=self.should_pause_roadmap(severity,gap_type,float(analysis.get("current_phase_progress",0)))
        return {"gap_type":gap_type,"gap_severity":severity,"confidence":.9 if misconception and misconception.get("confidence")=="high" else .7,"recommended_action":template["action"],"intervention_template":template,"estimated_intervention_minutes":template["estimated_minutes"],"should_pause_current_phase":pause,"notify_user":severity in {"critical","high","medium"}}

    @staticmethod
    def should_pause_roadmap(gap_severity: str, gap_type: str, current_phase_progress: float) -> bool:
        if gap_severity=="critical": return True
        if gap_severity=="high" and gap_type in {"conceptual","prerequisite"}: return True
        return gap_severity=="medium" and current_phase_progress<.3 and gap_type!="practice_deficit"

    @staticmethod
    def generate_intervention_title(skill_name: str, gap_type: str, severity: str) -> str:
        if severity=="critical": return f"🚨 Critical Review Needed: {skill_name}"
        prefix={"conceptual":"Conceptual Review","procedural":"Guided Practice","prerequisite":"Prerequisite Bridge","practice_deficit":"Extra Practice","retention_decay":"Quick Refresh"}.get(gap_type,"Targeted Review")
        return f"{prefix}: {skill_name}"
