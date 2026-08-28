"""Career mapping API payloads."""
from datetime import date,datetime
from pydantic import BaseModel,Field

class CareerSkillRequirementResponse(BaseModel):
    skill_id:str;skill_name:str;skill_slug:str;skill_category:str;importance:str;min_mastery_required:float;min_mastery_percentage:int;target_mastery:float;target_mastery_percentage:int;relevance_note:str|None;order_index:int
class CareerRoleResponse(BaseModel):
    id:str;title:str;slug:str;description:str;short_description:str;category:str;seniority_level:str;average_salary_usd:int|None;demand_level:str;typical_companies:list[str];responsibilities:list[str];related_role_slugs:list[str];is_featured:bool;skill_requirements:list[CareerSkillRequirementResponse]=Field(default_factory=list)
class SkillReadinessItem(BaseModel):
    skill_id:str;skill_name:str;skill_slug:str;category:str;importance:str;current_mastery:float;current_mastery_percentage:int;min_required:float;min_required_percentage:int;target_mastery:float;target_mastery_percentage:int;gap:float;gap_percentage:int;skill_readiness:float;status:str;relevance_note:str|None
class CareerReadinessResponse(BaseModel):
    role_id:str;role_title:str;role_slug:str;overall_readiness:float;overall_readiness_percentage:int;essential_readiness:float;important_readiness:float;readiness_level:str;skills:list[SkillReadinessItem];ready_skills:list[SkillReadinessItem];close_skills:list[SkillReadinessItem];gap_skills:list[SkillReadinessItem];not_started_skills:list[SkillReadinessItem];critical_gaps:list[SkillReadinessItem];estimated_weeks_to_ready:int|None
class ActionPlanResponse(BaseModel):
    role_id:str;role_title:str;executive_summary:str;estimated_job_ready_weeks:int;priority_phases:list[dict];quick_wins:list[dict];encouragement:str;market_note:str;generated_at:datetime
class CareerGoalSetRequest(BaseModel):role_id:str;target_date:date|None=None;job_ready_alert:bool=False
class CareerCompareRequest(BaseModel):role_ids:list[str]=Field(min_length=2,max_length=3)
class UserCareerGoalResponse(BaseModel):
    id:str;role_id:str;role_title:str;role_slug:str;is_primary:bool;initial_readiness:float|None;current_readiness:float|None;target_date:date|None;created_at:datetime
class MarketInsightsResponse(BaseModel):role_title:str;demand_description:str;key_skills_in_demand:list[str];emerging_technologies:list[str];typical_interview_topics:list[str];portfolio_recommendations:list[str];disclaimer:str
