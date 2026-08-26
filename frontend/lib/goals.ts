export interface Skill {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  category: string;
  difficulty_level: number;
  estimated_hours: number | null;
  is_active: boolean;
  prerequisites?: Skill[];
}

export interface GoalSkill {
  skill: Skill;
  priority_order: number;
  is_required: boolean;
  reason: string | null;
}

export interface GoalSummary {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  target_role: string | null;
  status: string;
  target_date: string | null;
  daily_study_minutes: number;
  created_at: string;
  skill_count: number;
}

export interface GoalDetail extends GoalSummary {
  required_skills: GoalSkill[];
  ai_summary: string | null;
  estimated_weeks: number | null;
  difficulty_assessment: string | null;
  warnings: string[];
}

export interface GoalDecomposition {
  goal_id: string;
  required_skills: GoalSkill[];
  estimated_weeks: number;
  difficulty_assessment: string;
  summary: string;
  recommended_daily_focus_minutes: number;
  warnings: string[];
  note: string;
}

export interface GoalDraft {
  title: string;
  targetRole: string;
  existingKnowledge: string;
  dailyMinutes: number;
  targetDate: string;
}
