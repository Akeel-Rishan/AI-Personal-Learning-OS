export interface AssessmentQuestion {
  id: string;
  skill_id: string | null;
  skill_name: string;
  skill_category: string;
  question_type: "multiple_choice" | "explanation" | "debugging" | "coding";
  question_text: string;
  options: string[] | null;
  difficulty: number;
  order_index: number;
}

export interface AssessmentStatus {
  id: string;
  goal_id: string | null;
  goal_title: string | null;
  assessment_type: string;
  status: string;
  total_questions: number;
  completed_questions: number;
  started_at: string | null;
  completed_at: string | null;
  current_question: AssessmentQuestion | null;
  progress_percentage: number;
  next_question: AssessmentQuestion | null;
}

export interface AnswerFeedback {
  question_id: string;
  score: number;
  is_correct: boolean;
  feedback: string;
  correct_answer: string;
  completed_questions: number;
  total_questions: number;
  is_assessment_complete: boolean;
  assessment_completed: boolean;
  next_question: AssessmentQuestion | null;
}

export interface SkillScore {
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  category: string;
  mastery_score: number;
  mastery_percentage: number;
  questions_count: number;
  correct_count: number;
  confidence: number;
  level: "beginner" | "intermediate" | "advanced" | "not_assessed";
}

export interface AssessmentResults {
  assessment_id: string;
  goal_id: string | null;
  goal_title: string | null;
  status: string;
  overall_score: number;
  total_questions: number;
  correct_answers: number;
  completed_at: string | null;
  skill_scores: SkillScore[];
  strong_skills: SkillScore[];
  weak_skills: SkillScore[];
}
