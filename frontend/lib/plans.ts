export type PlanItemStatus = "pending" | "in_progress" | "completed" | "skipped";

export interface DailyPlanItem {
  id: string;
  title: string;
  description: string | null;
  item_type: "lesson" | "exercise" | "review" | "assessment" | "practice" | "project";
  order_index: number;
  estimated_minutes: number;
  status: PlanItemStatus;
  skill_id: string | null;
  skill_name: string | null;
  roadmap_item_id: string | null;
  completed_at: string | null;
}

export interface DailyPlan {
  id: string;
  plan_date: string;
  status: "pending" | "in_progress" | "completed" | "partial";
  total_estimated_minutes: number;
  actual_minutes_spent: number;
  ai_generated_note: string | null;
  items: DailyPlanItem[];
  completed_items_count: number;
  total_items_count: number;
  completion_percentage: number;
}

export interface PlanSummary {
  total_items: number;
  completed_items: number;
  skipped_items: number;
  total_minutes_planned: number;
  actual_minutes_spent: number;
  skills_practiced: string[];
  xp_earned: number;
  streak_days: number;
  is_new_streak_milestone: boolean;
  roadmap_progress_delta: number;
  completion_message: string;
}

export interface StreakInfo {
  current_streak: number;
  longest_streak: number;
  last_completed_date: string | null;
  streak_at_risk: boolean;
}
