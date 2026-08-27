import { apiGet, apiPost } from "@/lib/api";

export type GapSeverity = "critical" | "high" | "medium" | "low";

export interface KnowledgeGap {
  id: string; skill_id: string; skill_name: string; skill_slug: string;
  gap_type: string; gap_severity: GapSeverity; description: string; misconception: string | null;
  evidence: Record<string, unknown>; status: string; intervention_created: boolean;
  intervention_items: Record<string, unknown> | null; detected_at: string;
  mastery_at_detection: number; mastery_percentage_at_detection: number;
  current_mastery: number; current_mastery_percentage: number; days_active: number;
}

export interface GapReport {
  active_gaps: KnowledgeGap[]; resolved_gaps: KnowledgeGap[]; resolved_gaps_count: number;
  total_gaps_ever: number; most_problematic_skill: string | null; average_resolution_days: number | null;
  gap_type_breakdown: Record<string, number>; severity_breakdown: Record<string, number>;
}

export interface AdaptationEvent {
  id: string; skill_id: string | null; skill_name: string | null; trigger_type: string;
  gap_type: string; gap_severity: GapSeverity; gap_description: string; action_taken: string;
  action_description: string; items_inserted: Record<string, unknown> | null;
  is_resolved: boolean; ai_reasoning: string | null; created_at: string;
}

export interface InterventionNotification {
  gap_id: string; skill_name: string; severity: GapSeverity; learner_message: string;
  gap_explanation: string; action_required: string; intervention_items_count: number;
  tutor_conversation_id: string | null; estimated_fix_minutes: number;
}

export interface AdaptationScan {
  gaps_detected: number; gaps_resolved: number; adaptations_made: number;
  adaptation_details: Array<Record<string, unknown>>; decayed_skills: string[];
  scan_duration_ms: number; message: string;
}

export const getGapReport = (status = "all") => apiGet<GapReport>(`/api/v1/adaptive/gaps?status=${status}`);
export const getAdaptationHistory = (limit = 20) => apiGet<AdaptationEvent[]>(`/api/v1/adaptive/history?limit=${limit}`);
export const getAdaptiveNotifications = () => apiGet<InterventionNotification[]>("/api/v1/adaptive/notifications");
export const runAdaptationScan = () => apiPost<AdaptationScan>("/api/v1/adaptive/scan", {});
export const acknowledgeGap = (id: string) => apiPost<KnowledgeGap>(`/api/v1/adaptive/gaps/${id}/acknowledge`, {});
export const dismissAdaptiveNotification = (id: string) => apiPost<{ dismissed: boolean }>(`/api/v1/adaptive/notifications/${id}/dismiss`, {});
