import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { TutorMessage } from "@/lib/tutor";

export interface ProjectStage { id:string; title:string; description:string; order_index:number; stage_type:string; instructions:string; deliverables:string[]; hints:string[]; resources:Array<{title:string;url:string}>; estimated_minutes:number; validation_criteria:string[] }
export interface Project { id:string; title:string; slug:string; description:string; short_description:string; difficulty_level:number; estimated_hours:number; category:string; required_skills:Array<Record<string,unknown>>; prerequisite_skills:Array<Record<string,unknown>>; tech_stack:string[]; learning_outcomes:string[]; is_featured:boolean; stages_count:number; stages:ProjectStage[] }
export interface ProjectLibraryItem extends Project { user_status:string|null; user_progress_percentage:number; is_eligible:boolean; missing_prerequisites:Array<{skill_name:string;required_mastery:number;current_mastery:number}>; user_project_id:string|null; recommendation_reason:string|null }
export interface UserProjectStage { id:string; stage_id:string; stage_order_index:number; status:"locked"|"active"|"submitted"|"completed"; hints_used:number; ai_score:number|null; ai_feedback:StageEvaluation|null; submitted_code:string|null; submitted_notes:string|null; mentor_conversation_id:string|null; started_at:string|null; completed_at:string|null; stage:ProjectStage }
export interface UserProject { id:string; project_id:string; status:string; current_stage_index:number; total_stages:number; xp_earned:number; progress_percentage:number; started_at:string; completed_at:string|null; last_active_at:string; work_data:Record<string,{code?:string;notes?:string;saved_at?:string}>; project:Project; stage_progress:UserProjectStage[] }
export interface StageEvaluation { overall_score:number; passed:boolean; criteria_evaluation:Array<{criterion:string;met:boolean;feedback:string;severity:string}>; strengths:string[]; improvements:string[]; overall_feedback:string; ready_for_next_stage:boolean; mentor_note:string; xp_awarded:number; next_stage_unlocked:boolean; next_stage_title:string|null; cached:boolean; project_completed:boolean }
export interface Completion { project_title:string; total_stages:number; completion_date:string; average_stage_score:number; total_xp_earned:number; skills_improved:string[]; completion_message:string; certificate_data:{learner_name:string;project_title:string;grade:string;score_percentage:number;completion_date:string;xp_earned:number}; evaluation:Record<string,unknown> }

export const getProjects=()=>apiGet<ProjectLibraryItem[]>("/api/v1/projects/");
export const getRecommendedProjects=()=>apiGet<ProjectLibraryItem[]>("/api/v1/projects/recommended");
export const getMyProjects=(status?:string)=>apiGet<UserProject[]>(`/api/v1/projects/my-projects${status?`?status=${status}`:""}`);
export const getProject=(id:string)=>apiGet<Project>(`/api/v1/projects/${id}`);
export const getEligibility=(id:string)=>apiGet<{eligible:boolean;missing_prerequisites:ProjectLibraryItem["missing_prerequisites"];recommendation:string}>(`/api/v1/projects/${id}/eligibility`);
export const startProject=(id:string)=>apiPost<UserProject>(`/api/v1/projects/${id}/start`,{});
export const getWorkspace=(id:string)=>apiGet<UserProject>(`/api/v1/projects/workspace/${id}`);
export const saveProjectWork=(id:string,stage_id:string,code:string,notes:string)=>apiPatch<{saved:boolean;saved_at:string}>(`/api/v1/projects/workspace/${id}/save-work`,{stage_id,code,notes});
export const submitProjectStage=(id:string,stageId:string,submitted_code:string,submitted_notes:string)=>apiPost<StageEvaluation>(`/api/v1/projects/workspace/${id}/stages/${stageId}/submit`,{submitted_code,submitted_notes});
export const getProjectHint=(id:string,stageId:string,index:number)=>apiGet<{hint:string;hint_number:number;total_hints:number;hints_remaining:number}>(`/api/v1/projects/workspace/${id}/stages/${stageId}/hint?hint_index=${index}`);
export const getMentorHistory=(id:string,stageId:string)=>apiGet<TutorMessage[]>(`/api/v1/projects/workspace/${id}/mentor/history/${stageId}`);
export const sendMentorMessage=(id:string,stage_id:string,message:string)=>apiPost<{content:string;assistant_message_id:string;user_message_id:string;conversation_id:string}>(`/api/v1/projects/workspace/${id}/mentor/message`,{stage_id,message});
export const submitFinalProject=(id:string,payload:{project_description:string;final_code:string|null;reflection:string;challenges_faced:string;github_url:string|null})=>apiPost<Completion>(`/api/v1/projects/workspace/${id}/submit-final`,payload);
