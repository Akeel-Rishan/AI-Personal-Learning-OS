import { apiDelete, apiGet, apiPost } from "@/lib/api";

export interface CareerRequirement { skill_id:string; skill_name:string; skill_slug:string; skill_category:string; importance:string; min_mastery_required:number; min_mastery_percentage:number; target_mastery:number; target_mastery_percentage:number; relevance_note:string|null; order_index:number }
export interface CareerRole { id:string; title:string; slug:string; description:string; short_description:string; category:string; seniority_level:string; average_salary_usd:number|null; demand_level:string; typical_companies:string[]; responsibilities:string[]; related_role_slugs:string[]; is_featured:boolean; skill_requirements:CareerRequirement[] }
export interface SkillReadiness { skill_id:string; skill_name:string; skill_slug:string; category:string; importance:string; current_mastery:number; current_mastery_percentage:number; min_required:number; min_required_percentage:number; target_mastery:number; target_mastery_percentage:number; gap:number; gap_percentage:number; skill_readiness:number; status:"ready"|"close"|"gap"|"not_started"; relevance_note:string|null }
export interface CareerReadiness { role_id:string; role_title:string; role_slug:string; overall_readiness:number; overall_readiness_percentage:number; essential_readiness:number; important_readiness:number; readiness_level:string; skills:SkillReadiness[]; ready_skills:SkillReadiness[]; close_skills:SkillReadiness[]; gap_skills:SkillReadiness[]; not_started_skills:SkillReadiness[]; critical_gaps:SkillReadiness[]; estimated_weeks_to_ready:number|null }
export interface ActionPlan { role_id:string; role_title:string; executive_summary:string; estimated_job_ready_weeks:number; priority_phases:Array<{phase_number:number;title:string;duration_weeks:number;focus_skills:string[];description:string;key_actions:string[]}>; quick_wins:Array<{skill:string;skill_slug:string;current:number;required:number;gap_percentage:number;action:string;estimated_days:number}>; encouragement:string; market_note:string; generated_at:string }
export interface CareerGoalBundle { career_goal:{id:string;role_id:string;role_title:string;role_slug:string;target_date:string|null;job_ready_alert?:boolean}; role:CareerRole; readiness:CareerReadiness; readiness_change:number; roadmap_alignment?:{missing_from_roadmap:string[];suggestion:string} }
export interface MarketInsights { role_title:string; demand_description:string; key_skills_in_demand:string[]; emerging_technologies:string[]; typical_interview_topics:string[]; portfolio_recommendations:string[]; disclaimer:string }

export const getCareerRoles=(category?:string)=>apiGet<CareerRole[]>(`/api/v1/career/roles${category?`?category=${encodeURIComponent(category)}`:""}`);
export const getCareerReadiness=(id:string)=>apiGet<CareerReadiness>(`/api/v1/career/roles/${id}/readiness`);
export const getCareerActionPlan=(id:string)=>apiGet<ActionPlan>(`/api/v1/career/roles/${id}/action-plan`);
export const getCareerMarketInsights=(id:string)=>apiGet<MarketInsights>(`/api/v1/career/roles/${id}/market-insights`);
export const compareCareerRoles=(ids:string[])=>apiPost<CareerReadiness[]>("/api/v1/career/compare",{role_ids:ids});
export const setCareerGoal=(role_id:string,job_ready_alert=false,target_date?:string)=>apiPost<CareerGoalBundle>("/api/v1/career/goal",{role_id,job_ready_alert,target_date});
export const getCareerGoal=()=>apiGet<CareerGoalBundle>("/api/v1/career/goal");
export const deleteCareerGoal=()=>apiDelete<void>("/api/v1/career/goal");
