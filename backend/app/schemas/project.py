"""Validated project-library, workspace, mentor, and submission payloads."""
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator

class ProjectStageResponse(BaseModel):
    id:str; title:str; description:str; order_index:int; stage_type:str; instructions:str
    deliverables:list[str]; hints:list[str]; resources:list[dict[str,str]]; estimated_minutes:int; validation_criteria:list[str]

class ProjectResponse(BaseModel):
    id:str; title:str; slug:str; description:str; short_description:str; difficulty_level:int; estimated_hours:float; category:str
    required_skills:list[dict[str,object]]; prerequisite_skills:list[dict[str,object]]; tech_stack:list[str]; learning_outcomes:list[str]; is_featured:bool; stages_count:int=0; stages:list[ProjectStageResponse]=Field(default_factory=list)

class ProjectLibraryItem(ProjectResponse):
    user_status:str|None=None; user_progress_percentage:float=0; is_eligible:bool=True; missing_prerequisites:list[dict[str,object]]=Field(default_factory=list); user_project_id:str|None=None; recommendation_reason:str|None=None

class UserProjectStageResponse(BaseModel):
    id:str; stage_id:str; stage_order_index:int; status:str; hints_used:int; ai_score:float|None; ai_feedback:dict[str,object]|None; submitted_code:str|None=None; submitted_notes:str|None=None; mentor_conversation_id:str|None; started_at:datetime|None; completed_at:datetime|None; stage:ProjectStageResponse

class UserProjectResponse(BaseModel):
    id:str; project_id:str; status:str; current_stage_index:int; total_stages:int; xp_earned:int; progress_percentage:float; started_at:datetime; completed_at:datetime|None; last_active_at:datetime; work_data:dict[str,object]; project:ProjectResponse; stage_progress:list[UserProjectStageResponse]

class StageSubmitRequest(BaseModel):
    submitted_code:str=Field(min_length=10,max_length=100_000); submitted_notes:str=Field(default="",max_length=10_000)

class StageEvaluationResponse(BaseModel):
    overall_score:float; passed:bool; criteria_evaluation:list[dict[str,object]]; strengths:list[str]; improvements:list[str]; overall_feedback:str; ready_for_next_stage:bool; mentor_note:str; xp_awarded:int; next_stage_unlocked:bool; next_stage_title:str|None; cached:bool=False; project_completed:bool=False

class WorkSaveRequest(BaseModel):
    stage_id:str; code:str=Field(max_length=100_000); notes:str=Field(default="",max_length=10_000)

class WorkSaveResponse(BaseModel): saved:bool; saved_at:datetime
class MentorMessageRequest(BaseModel): message:str=Field(min_length=1,max_length=4000); stage_id:str
class MentorMessageResponse(BaseModel): user_message_id:str; assistant_message_id:str; content:str; conversation_id:str; metadata:dict[str,object]
class HintResponse(BaseModel): hint:str; hint_number:int; total_hints:int; hints_remaining:int

class FinalSubmitRequest(BaseModel):
    project_description:str=Field(min_length=50,max_length=20_000); final_code:str|None=Field(default=None,max_length=200_000); reflection:str=Field(min_length=100,max_length=30_000); challenges_faced:str=Field(min_length=50,max_length=20_000); github_url:str|None=Field(default=None,max_length=500)
    @field_validator("github_url")
    @classmethod
    def validate_url(cls,value:str|None)->str|None:
        if value and not value.startswith(("https://github.com/","http://github.com/")): raise ValueError("Enter a valid GitHub URL")
        return value

class ProjectCompletionResponse(BaseModel):
    project_title:str; total_stages:int; completion_date:datetime; average_stage_score:float; total_xp_earned:int; skills_improved:list[str]; completion_message:str; certificate_data:dict[str,object]; evaluation:dict[str,object]
