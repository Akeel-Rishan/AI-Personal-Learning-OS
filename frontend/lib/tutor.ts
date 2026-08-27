export interface TutorMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  skill_id: string | null;
  skill_name: string | null;
  is_active: boolean;
  message_count: number;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: TutorMessage[];
}

export interface SendMessageResponse {
  user_message_id: string;
  assistant_message_id: string;
  content: string;
  conversation_id: string;
  metadata: Record<string, unknown>;
}

export interface TutorSkillMastery {
  id: string;
  name: string;
  mastery: number;
  level: "weak" | "developing" | "strong";
}

export interface GoalSkillOption { id: string; name: string; slug: string }

export interface LearnerContext {
  user_name: string;
  goal_title: string;
  preferred_style: ExplanationStyle;
  daily_minutes: number;
  current_phase: string;
  current_focus_skills: string[];
  goal_skills: GoalSkillOption[];
  skill_mastery: TutorSkillMastery[];
  strong_skills: string[];
  weak_skills: string[];
  today_plan_items: string[];
  recent_mistakes: Array<{ exercise: string; skill: string | null; answer: string | null }>;
  total_xp: number;
  streak_days: number;
}

export type ExplanationStyle = "visual" | "mathematical" | "step_by_step" | "analogies" | "balanced";

export interface SuggestedPromptsResponse {
  prompts: string[];
  generated_for_skill: string | null;
}
