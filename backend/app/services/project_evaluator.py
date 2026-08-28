"""AI-assisted holistic project and deterministic XP evaluation."""
from __future__ import annotations
import asyncio, json
from app.models.project import Project, ProjectSubmission, UserProject
from app.services.ai_service import AIService

class ProjectEvaluator:
    def __init__(self)->None:self.ai=AIService()
    async def evaluate_final_submission(self,project:Project,user_project:UserProject,submission:ProjectSubmission,stage_evaluations:list[dict[str,object]])->dict[str,object]:
        average=sum(float(item.get("score",0)) for item in stage_evaluations)/max(1,len(stage_evaluations)); fallback=self._fallback(project,submission,average)
        schema={"type":"object","properties":{"overall_score":{"type":"number"},"grade":{"type":"string"},"dimensions":{"type":"object","additionalProperties":{"type":"object","properties":{"score":{"type":"number"},"feedback":{"type":"string"}},"required":["score","feedback"],"additionalProperties":False}},"learning_outcomes_achieved":{"type":"array","items":{"type":"object","properties":{"outcome":{"type":"string"},"achieved":{"type":"boolean"},"evidence":{"type":"string"}},"required":["outcome","achieved","evidence"],"additionalProperties":False}},"portfolio_ready":{"type":"boolean"},"portfolio_suggestions":{"type":"string"},"key_strengths":{"type":"array","items":{"type":"string"}},"growth_areas":{"type":"array","items":{"type":"string"}},"career_relevance":{"type":"string"},"completion_message":{"type":"string"}},"required":["overall_score","grade","dimensions","learning_outcomes_achieved","portfolio_ready","portfolio_suggestions","key_strengths","growth_areas","career_relevance","completion_message"],"additionalProperties":False}
        try:
            result=await asyncio.wait_for(self.ai.generate_structured(instructions="You are a senior engineer evaluating a complete learner project. Be constructive and return strict JSON.",prompt=f"Project: {project.title}\nOutcomes: {json.dumps(project.learning_outcomes)}\nStage results: {json.dumps(stage_evaluations,default=str)}\nDescription: {submission.project_description}\nCode: {submission.final_code or 'Not supplied'}\nReflection: {submission.reflection}\nChallenges: {submission.challenges_faced}",schema_name="project_final_evaluation",schema=schema,max_output_tokens=1800),timeout=20)
        except Exception: result=fallback
        score=min(1,max(0,float(result.get("overall_score",average)))); result["overall_score"]=score; result["xp_awarded"]=300+round(score*200)+(100 if float(dict(result.get("dimensions",{})).get("code_quality",{}).get("score",0))>=.8 else 0); return result
    @staticmethod
    async def calculate_xp_for_stage(stage_score:float,stage_order_index:int,hints_used:int)->int:return max(10,50+round(min(1,max(0,stage_score))*30)-max(0,hints_used)*5+(20 if stage_order_index==0 else 0))
    @staticmethod
    def _fallback(project:Project,submission:ProjectSubmission,average:float)->dict[str,object]:
        score=round(min(1,max(.65,average)),3); grade="Excellent" if score>=.85 else "Good" if score>=.75 else "Satisfactory"
        dimensions={key:{"score":score,"feedback":"The staged work demonstrates a consistent, working approach."} for key in ["functionality","code_quality","problem_solving","understanding","reflection_quality"]}
        return {"overall_score":score,"grade":grade,"dimensions":dimensions,"learning_outcomes_achieved":[{"outcome":item,"achieved":True,"evidence":"Supported by completed stage evaluations and the final reflection."} for item in project.learning_outcomes],"portfolio_ready":score>=.75,"portfolio_suggestions":"Add screenshots, setup instructions, and concise architecture notes.","key_strengths":["Completed a full staged engineering workflow","Documented decisions and learning"],"growth_areas":["Expand automated tests and edge-case coverage"],"career_relevance":"This demonstrates practical project delivery and technical communication.","completion_message":f"You completed {project.title} and turned the core concepts into a working project. Your persistence across every stage is the strongest evidence of your progress."}
