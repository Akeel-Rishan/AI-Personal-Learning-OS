"""API schemas for adaptive learning decisions and knowledge gaps."""
from datetime import datetime
from pydantic import BaseModel, Field

class KnowledgeGapResponse(BaseModel):
    id: str; skill_id: str; skill_name: str; skill_slug: str
    gap_type: str; gap_severity: str; description: str; misconception: str | None
    evidence: dict[str, object]; status: str; intervention_created: bool
    intervention_items: dict[str, object] | None; detected_at: datetime
    mastery_at_detection: float; mastery_percentage_at_detection: int
    current_mastery: float; current_mastery_percentage: int; days_active: int

class AdaptationEventResponse(BaseModel):
    id: str; skill_id: str | None; skill_name: str | None; trigger_type: str
    gap_type: str; gap_severity: str; gap_description: str; action_taken: str
    action_description: str; items_inserted: dict[str, object] | None
    is_resolved: bool; ai_reasoning: str | None; created_at: datetime

class AdaptationScanResponse(BaseModel):
    gaps_detected: int; gaps_resolved: int; adaptations_made: int
    adaptation_details: list[dict[str, object]] = Field(default_factory=list)
    decayed_skills: list[str] = Field(default_factory=list)
    scan_duration_ms: int; message: str

class GapReportResponse(BaseModel):
    active_gaps: list[KnowledgeGapResponse]; resolved_gaps: list[KnowledgeGapResponse]
    resolved_gaps_count: int; total_gaps_ever: int; most_problematic_skill: str | None
    average_resolution_days: float | None; gap_type_breakdown: dict[str, int]
    severity_breakdown: dict[str, int]

class InterventionNotification(BaseModel):
    gap_id: str; skill_name: str; severity: str; learner_message: str
    gap_explanation: str; action_required: str; intervention_items_count: int
    tutor_conversation_id: str | None; estimated_fix_minutes: int

class ManualAdaptationRequest(BaseModel):
    skill_id: str | None = None

class DismissResponse(BaseModel):
    dismissed: bool
