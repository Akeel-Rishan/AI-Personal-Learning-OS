export type RoadmapItemStatus = "pending" | "active" | "completed" | "skipped";

export interface RoadmapItem {
  id: string;
  title: string;
  description: string | null;
  item_type: "lesson" | "exercise" | "project" | "assessment" | "review";
  order_index: number;
  status: RoadmapItemStatus;
  estimated_minutes: number | null;
  skill_id: string | null;
  skill_name: string | null;
  completed_at: string | null;
}

export interface RoadmapPhase {
  id: string;
  title: string;
  description: string | null;
  order_index: number;
  status: "locked" | "active" | "paused" | "completed";
  estimated_weeks: number | null;
  started_at: string | null;
  completed_at: string | null;
  items: RoadmapItem[];
  items_count: number;
  completed_items_count: number;
  progress_percentage: number;
  phase_metadata: Record<string, unknown> | null;
}

export interface Roadmap {
  id: string;
  goal_id: string;
  goal_title: string;
  goal_target_date: string | null;
  status: string;
  total_phases: number;
  current_phase_index: number;
  estimated_weeks: number | null;
  ai_generated_summary: string | null;
  phases: RoadmapPhase[];
  overall_progress_percentage: number;
  completed_items: number;
  total_items: number;
  last_adapted_at: string | null;
  created_at: string;
}

export interface RoadmapItemUpdate {
  item: RoadmapItem;
  phase_id: string;
  phase_status: RoadmapPhase["status"];
  phase_progress_percentage: number;
  roadmap_progress_percentage: number;
  unlocked_phase_id: string | null;
}
