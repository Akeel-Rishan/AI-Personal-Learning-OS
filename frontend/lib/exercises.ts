export type ExerciseType = "multiple_choice" | "explanation" | "debugging" | "coding";

export interface ExerciseContent {
  problem_statement: string;
  starter_code?: string | null;
  test_cases?: Array<{ input: string; expected_output: string; description: string }> | null;
  constraints?: string[] | null;
  example_input?: string | null;
  example_output?: string | null;
  options?: string[] | null;
  explanation?: string | null;
  buggy_code?: string | null;
}

export interface Exercise {
  id: string;
  title: string;
  exercise_type: ExerciseType;
  difficulty: number;
  content: ExerciseContent;
  hints: string[] | null;
  skill_id: string | null;
  skill_name: string | null;
  skill_slug: string | null;
  is_ai_generated: boolean;
  user_attempts: number;
  best_score: number | null;
  is_completed: boolean;
  last_attempted_at: string | null;
}

export interface AttemptFeedback {
  attempt_id: string;
  is_correct: boolean;
  score: number;
  feedback: string;
  correct_answer: string | null;
  detailed_feedback: Record<string, any> | null;
  mastery_change: number;
  new_mastery: number;
  hint_available: boolean;
  next_hint: string | null;
  attempt_number: number;
  mastery_percentage: number;
  weakness_detected: WeaknessPattern | null;
}

export interface WeaknessPattern {
  misconception: string;
  targeted_review: string;
  suggested_resources: string[];
}

export interface Recommendation {
  exercise: Exercise;
  skill_name: string;
  skill_slug: string;
  skill_mastery: number;
  reason: string;
}

export interface ExerciseStats {
  total_attempted: number;
  correct_first_try: number;
  total_correct: number;
  accuracy_rate: number;
  average_attempts: number;
  hardest_exercise: string | null;
  easiest_exercise: string | null;
  time_spent_minutes: number;
  mastery_gained: number;
}

export interface ExerciseHistory {
  exercise_id: string;
  exercise_title: string;
  exercise_type: ExerciseType;
  skill_id: string | null;
  skill_name: string | null;
  best_score: number;
  attempts: number;
  is_completed: boolean;
  last_attempted_at: string;
}

export interface CodeReview {
  overall_score: number;
  is_correct: boolean | null;
  correctness_score?: number | null;
  quality_score?: number | null;
  style_score?: number | null;
  performance_score?: number | null;
  passed_test_cases?: number | null;
  total_test_cases?: number | null;
  summary: string;
  strengths: string[];
  improvements: Array<{ issue?: string; suggestion?: string; example?: string; severity?: string }>;
  better_approach: string | null;
  learning_note: string;
  formatted: Record<string, any>;
}
