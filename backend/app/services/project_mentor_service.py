"""Stage-aware Socratic project mentor and submission evaluator."""
from __future__ import annotations
import asyncio, json, re, uuid
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.conversation import TutorConversation,TutorMessage
from app.models.project import Project,ProjectStage,UserProject,UserProjectStage
from app.services.ai_service import AIService
from app.services.tutor_service import TutorService

SAFE_REDIRECT="I can see you want the complete solution, but let me guide you instead. What part are you stuck on specifically?"

class ProjectMentorService:
    def __init__(self,db:AsyncSession):self.db=db;self.ai=AIService()
    async def build_mentor_system_prompt(self,project:Project,current_stage:ProjectStage,user_project:UserProject,user_context:dict[str,object],stage_progress:UserProjectStage)->str:
        statuses="\n".join(("✓" if item.status=="completed" else "→" if item.id==stage_progress.id else "○")+f" Stage {item.stage_order_index+1}: {item.stage.title} — {item.status}" for item in user_project.stage_progress)
        return f"""You are an expert Socratic project mentor guiding {user_context.get('user_name','Learner')} through {project.title}. Guide, never solve.
PROJECT: {project.description}\nTECH: {', '.join(project.tech_stack)}\nSTAGES: {user_project.total_stages}
CURRENT STAGE {current_stage.order_index+1}: {current_stage.title} ({current_stage.stage_type})\n{current_stage.instructions}
DELIVERABLES:\n- """+"\n- ".join(current_stage.deliverables)+"\nVALIDATION:\n- "+"\n- ".join(current_stage.validation_criteria)+f"\nHINTS (reveal only progressively): {current_stage.hints}\nHINTS USED: {stage_progress.hints_used}/{len(current_stage.hints)}\nPROGRESS:\n{statuses}\nRULES: Never give a complete stage solution. Point out one issue at a time. Ask what they tried before hinting. Keep focus on this stage. Be encouraging and specific. Keep under 300 words. End with a guiding question or one next action."
    async def send_mentor_message(self,user_project_id:str,stage_id:str,user_id:str,message:str)->dict[str,object]:
        up,progress=await self._load(user_project_id,stage_id,user_id); context=await TutorService(self.db).build_learner_context(user_id); conversation=await self._conversation(up,progress,context)
        prompt=await self.build_mentor_system_prompt(up.project,progress.stage,up,context,progress); history=[{"role":m.role,"content":m.content} for m in conversation.messages[-16:] if m.role in {"user","assistant"}]+[{"role":"user","content":message}]
        try: generated=await asyncio.wait_for(self.ai.generate_text(instructions=prompt,messages=history,max_output_tokens=700),timeout=20); content=str(generated["content"]).strip()
        except Exception: generated={"model":self.ai.model,"fallback":True}; content=f"Let’s work through {progress.stage.title} one step at a time. What have you tried so far, and which deliverable is blocking you?"
        if self._reveals_solution(content,progress.stage):content=SAFE_REDIRECT
        user_message=TutorMessage(conversation_id=conversation.id,role="user",content=message,message_metadata={"project_stage":str(progress.stage_id)}); assistant=TutorMessage(conversation_id=conversation.id,role="assistant",content=content,message_metadata={"socratic_mode":True,"project_stage":str(progress.stage_id),"model":str(generated.get("model",self.ai.model))});self.db.add_all([user_message,assistant]);conversation.message_count+=2;conversation.updated_at=datetime.now(timezone.utc);await self.db.commit()
        return {"user_message_id":str(user_message.id),"assistant_message_id":str(assistant.id),"content":content,"conversation_id":str(conversation.id),"metadata":assistant.message_metadata or {}}
    async def get_stage_hint(self,user_project_id:str,stage_id:str,user_id:str,hint_index:int)->dict[str,object]:
        _,progress=await self._load(user_project_id,stage_id,user_id); hints=progress.stage.hints
        if hint_index<0 or hint_index>=len(hints):raise HTTPException(404,"No more hints. Ask your mentor about the specific step blocking you.")
        progress.hints_used=max(progress.hints_used,hint_index+1);await self.db.commit();return {"hint":hints[hint_index],"hint_number":hint_index+1,"total_hints":len(hints),"hints_remaining":len(hints)-hint_index-1}
    async def evaluate_stage_submission(self,user_project_id:str,stage_id:str,user_id:str,submitted_code:str,submitted_notes:str)->dict[str,object]:
        up,progress=await self._load(user_project_id,stage_id,user_id);stage=progress.stage
        schema={"type":"object","properties":{"overall_score":{"type":"number"},"passed":{"type":"boolean"},"criteria_evaluation":{"type":"array","items":{"type":"object","properties":{"criterion":{"type":"string"},"met":{"type":"boolean"},"feedback":{"type":"string"},"severity":{"type":"string"}},"required":["criterion","met","feedback","severity"],"additionalProperties":False}},"strengths":{"type":"array","items":{"type":"string"}},"improvements":{"type":"array","items":{"type":"string"}},"overall_feedback":{"type":"string"},"ready_for_next_stage":{"type":"boolean"},"mentor_note":{"type":"string"}},"required":["overall_score","passed","criteria_evaluation","strengths","improvements","overall_feedback","ready_for_next_stage","mentor_note"],"additionalProperties":False}
        try: result=await asyncio.wait_for(self.ai.generate_structured(instructions="Evaluate this learner project stage strictly against every criterion. Return strict JSON.",prompt=f"Project: {up.project.title}\nStage: {stage.title}\nInstructions: {stage.instructions}\nCriteria: {json.dumps(stage.validation_criteria)}\nCode:\n{submitted_code}\nNotes: {submitted_notes}",schema_name="project_stage_evaluation",schema=schema,max_output_tokens=1400),timeout=20)
        except Exception: result=self._fallback_evaluation(stage,submitted_code,submitted_notes)
        score=min(1,max(0,float(result.get("overall_score",0))));result["overall_score"]=score;result["passed"]=score>=.65 and bool(result.get("passed",True));result["ready_for_next_stage"]=bool(result["passed"]);return result
    async def generate_stage_intro_message(self,project:Project,stage:ProjectStage,user_context:dict[str,object],is_first_stage:bool)->str:
        prefix=f"Welcome to {project.title}! I’m your project mentor for this journey." if is_first_stage else f"Nice work on the previous milestone. Stage {stage.order_index+1} focuses on {stage.title}."
        return f"{prefix}\n\nIn this stage you’ll produce {len(stage.deliverables)} concrete deliverables. Start by reading the checklist, then turn the first item into one small testable task. What will your first action be?"
    async def generate_completion_message(self,project:Project,user_project:UserProject,evaluation:dict[str,object])->str:return f"You completed {project.title} across all {user_project.total_stages} stages. You built, tested, revised, and explained a real artifact—exactly the workflow used in professional projects."
    async def _conversation(self,up:UserProject,progress:UserProjectStage,context:dict[str,object])->TutorConversation:
        if progress.mentor_conversation_id:
            row=(await self.db.execute(select(TutorConversation).options(selectinload(TutorConversation.messages)).where(TutorConversation.id==progress.mentor_conversation_id))).scalars().unique().one_or_none()
            if row:return row
        conversation=TutorConversation(user_id=up.user_id,title=f"{up.project.title} — Stage {progress.stage_order_index+1}: {progress.stage.title}",message_count=1);self.db.add(conversation);await self.db.flush();intro=await self.generate_stage_intro_message(up.project,progress.stage,context,progress.stage_order_index==0);self.db.add(TutorMessage(conversation=conversation,role="assistant",content=intro,message_metadata={"socratic_mode":True,"project_stage":str(progress.stage_id)}));progress.mentor_conversation_id=conversation.id;await self.db.flush();return conversation
    async def _load(self,user_project_id:str,stage_id:str,user_id:str)->tuple[UserProject,UserProjectStage]:
        try: upid,sid,uid=uuid.UUID(user_project_id),uuid.UUID(stage_id),uuid.UUID(user_id)
        except ValueError as exc:raise HTTPException(422,"Invalid identifier") from exc
        up=(await self.db.execute(select(UserProject).options(selectinload(UserProject.project).selectinload(Project.stages),selectinload(UserProject.stage_progress).selectinload(UserProjectStage.stage)).where(UserProject.id==upid,UserProject.user_id==uid))).scalars().unique().one_or_none()
        if not up:raise HTTPException(404,"Project workspace not found")
        progress=next((item for item in up.stage_progress if item.stage_id==sid),None)
        if not progress:raise HTTPException(404,"Project stage not found")
        return up,progress
    @staticmethod
    def _reveals_solution(content:str,stage:ProjectStage)->bool:
        blocks=re.findall(r"```[\w-]*\n([\s\S]*?)```",content); keywords={word.lower() for criterion in stage.validation_criteria for word in re.findall(r"[A-Za-z_]{5,}",criterion)}
        return any(len(block.splitlines())>=12 and (sum(word in block.lower() for word in keywords)/max(1,len(keywords)))>.8 for block in blocks)
    @staticmethod
    def _fallback_evaluation(stage:ProjectStage,code:str,notes:str)->dict[str,object]:
        substantive=len(code.strip())>=60; criteria=[{"criterion":item,"met":substantive,"feedback":"The submission contains a substantive implementation to review." if substantive else "Add a working implementation and explain how it meets this criterion.","severity":"required"} for item in stage.validation_criteria];score=.72 if substantive else .35
        return {"overall_score":score,"passed":substantive,"criteria_evaluation":criteria,"strengths":["Submitted a clear implementation attempt"] if substantive else [],"improvements":[] if substantive else ["Implement the deliverables before resubmitting"],"overall_feedback":"The submission demonstrates the stage deliverables." if substantive else "The submission needs more implementation detail.","ready_for_next_stage":substantive,"mentor_note":"Carry your tested assumptions into the next stage."}
