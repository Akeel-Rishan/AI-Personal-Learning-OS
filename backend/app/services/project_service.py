"""Project library, eligibility, staged progression, autosave, and completion."""
from __future__ import annotations
import hashlib,uuid
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.conversation import TutorConversation
from app.models.progress import SkillHistory,UserSkill
from app.models.project import Project,ProjectStage,ProjectSubmission,UserProject,UserProjectStage
from app.models.skill import Skill
from app.schemas.project import ProjectLibraryItem,ProjectResponse,ProjectStageResponse,UserProjectResponse,UserProjectStageResponse
from app.services.gamification_service import GamificationService
from app.services.project_evaluator import ProjectEvaluator
from app.services.project_mentor_service import ProjectMentorService
from app.services.tutor_service import TutorService

class ProjectService:
    def __init__(self,db:AsyncSession):self.db=db;self.mentor=ProjectMentorService(db);self.evaluator=ProjectEvaluator()
    async def get_project_library(self,user_id:str,category:str|None=None,difficulty:int|None=None,status:str|None=None)->list[ProjectLibraryItem]:
        query=select(Project).options(selectinload(Project.stages)).where(Project.is_active.is_(True));
        if category:query=query.where(Project.category==category)
        if difficulty:query=query.where(Project.difficulty_level==difficulty)
        projects=list((await self.db.execute(query.order_by(Project.order_index))).scalars().unique());ups={item.project_id:item for item in await self.get_user_projects(user_id)};result=[]
        for item in projects:
            up=ups.get(item.id); eligibility=await self.check_eligibility(user_id,item)
            if status and (up.status if up else "not_started")!=status:continue
            result.append(self.serialize_library(item,up,eligibility))
        return result
    async def check_eligibility(self,user_id:str,project:Project)->dict[str,object]:
        missing=[]
        for requirement in project.prerequisite_skills:
            slug=str(requirement.get("skill_slug",""));required=float(requirement.get("min_mastery",0));row=(await self.db.execute(select(UserSkill).join(Skill).where(UserSkill.user_id==uuid.UUID(user_id),Skill.slug==slug))).scalars().one_or_none();current=float(row.mastery_score) if row else 0
            if current<required:
                skill=await self.db.scalar(select(Skill.name).where(Skill.slug==slug));missing.append({"skill_slug":slug,"skill_name":skill or slug.replace("-"," ").title(),"required_mastery":required,"current_mastery":current,"gap":round(required-current,3)})
        return {"eligible":not missing,"missing_prerequisites":missing,"recommendation":"You’re ready to start." if not missing else f"Build {missing[0]['skill_name']} mastery to {float(missing[0]['required_mastery']):.0%} first."}
    async def start_project(self,user_id:str,project_id:str)->UserProject:
        project=await self.get_project(project_id)
        if not project:raise HTTPException(404,"Project not found")
        eligibility=await self.check_eligibility(user_id,project)
        if not eligibility["eligible"]:raise HTTPException(409,{"message":"Prerequisites not met","missing_prerequisites":eligibility["missing_prerequisites"]})
        existing=(await self.db.execute(select(UserProject).where(UserProject.user_id==uuid.UUID(user_id),UserProject.project_id==project.id))).scalars().one_or_none()
        if existing:return await self.get_user_project(str(existing.id),user_id) # type: ignore[return-value]
        now=datetime.now(timezone.utc);up=UserProject(user_id=uuid.UUID(user_id),project_id=project.id,status="active",current_stage_index=0,total_stages=len(project.stages),work_data={},started_at=now,last_active_at=now);self.db.add(up);await self.db.flush()
        for index,stage in enumerate(project.stages):self.db.add(UserProjectStage(user_project_id=up.id,stage_id=stage.id,stage_order_index=index,status="active" if index==0 else "locked",started_at=now if index==0 else None))
        await self.db.flush();up=await self.get_user_project(str(up.id),user_id) # type: ignore[assignment]
        first=up.stage_progress[0];context=await TutorService(self.db).build_learner_context(user_id);await self.mentor._conversation(up,first,context);await self.db.commit();return await self.get_user_project(str(up.id),user_id) # type: ignore[return-value]
    async def get_project(self,project_id:str)->Project|None:
        try:parsed=uuid.UUID(project_id)
        except ValueError:return None
        return (await self.db.execute(select(Project).options(selectinload(Project.stages)).where(Project.id==parsed,Project.is_active.is_(True)))).scalars().unique().one_or_none()
    async def get_user_project(self,user_project_id:str,user_id:str)->UserProject|None:
        try:pid,uid=uuid.UUID(user_project_id),uuid.UUID(user_id)
        except ValueError:return None
        return (await self.db.execute(self._workspace_query().where(UserProject.id==pid,UserProject.user_id==uid).execution_options(populate_existing=True))).scalars().unique().one_or_none()
    async def get_user_projects(self,user_id:str,status:str|None=None)->list[UserProject]:
        query=self._workspace_query().where(UserProject.user_id==uuid.UUID(user_id));
        if status:query=query.where(UserProject.status==status)
        return list((await self.db.execute(query.order_by(UserProject.last_active_at.desc()))).scalars().unique())
    async def save_work(self,user_project_id:str,user_id:str,stage_id:str,code:str,notes:str)->datetime:
        up=await self.get_user_project(user_project_id,user_id)
        if not up or not any(str(item.stage_id)==stage_id and item.status!="locked" for item in up.stage_progress):raise HTTPException(404,"Editable project stage not found")
        now=datetime.now(timezone.utc);data=dict(up.work_data or {});data[f"stage_{stage_id}"]={"code":code,"notes":notes,"saved_at":now.isoformat()};up.work_data=data;up.last_active_at=now;await self.db.commit();return now
    async def submit_stage(self,user_project_id:str,stage_id:str,user_id:str,submitted_code:str,submitted_notes:str)->dict[str,object]:
        up=await self.get_user_project(user_project_id,user_id)
        if not up:raise HTTPException(404,"Project workspace not found")
        progress=next((item for item in up.stage_progress if str(item.stage_id)==stage_id),None)
        if not progress:raise HTTPException(404,"Project stage not found")
        digest=hashlib.sha256((submitted_code+"\0"+submitted_notes).encode()).hexdigest()
        if progress.submission_hash==digest and progress.ai_feedback:
            return {**progress.ai_feedback,"xp_awarded":0,"next_stage_unlocked":False,"next_stage_title":None,"cached":True,"project_completed":up.status=="completed"}
        if progress.status not in {"active","submitted"}:raise HTTPException(409,"Only the current stage can be submitted")
        evaluation=await self.mentor.evaluate_stage_submission(user_project_id,stage_id,user_id,submitted_code,submitted_notes);now=datetime.now(timezone.utc);progress.submitted_code=submitted_code;progress.submitted_notes=submitted_notes;progress.submission_hash=digest;progress.ai_score=float(evaluation["overall_score"]);progress.criteria_met=list(evaluation["criteria_evaluation"]);progress.ai_feedback=dict(evaluation);progress.submitted_at=now;next_stage=None;xp=0;completed=False
        if evaluation["passed"]:
            progress.status="completed";progress.completed_at=now;xp=await self.evaluator.calculate_xp_for_stage(progress.ai_score,progress.stage_order_index,progress.hints_used);up.xp_earned+=xp;await GamificationService(self.db).award_xp(user_id,"project_stage_completed",xp,f"[project:{up.id}] Completed {progress.stage.title}");next_stage=await self.unlock_next_stage(up)
            if next_stage is None:await self.finalize_project(user_project_id,user_id,commit=False);completed=True
        else:progress.status="submitted"
        progress.ai_feedback={**evaluation,"xp_awarded":xp};up.last_active_at=now;await self.db.commit();return {**evaluation,"xp_awarded":xp,"next_stage_unlocked":next_stage is not None,"next_stage_title":next_stage.stage.title if next_stage else None,"cached":False,"project_completed":completed}
    async def unlock_next_stage(self,user_project:UserProject)->UserProjectStage|None:
        current=max((item.stage_order_index for item in user_project.stage_progress if item.status=="completed"),default=-1);next_stage=next((item for item in user_project.stage_progress if item.stage_order_index==current+1 and item.status=="locked"),None)
        if not next_stage:return None
        next_stage.status="active";next_stage.started_at=datetime.now(timezone.utc);user_project.current_stage_index=next_stage.stage_order_index;context=await TutorService(self.db).build_learner_context(str(user_project.user_id));await self.mentor._conversation(user_project,next_stage,context);return next_stage
    async def finalize_project(self,user_project_id:str,user_id:str,commit:bool=True)->dict[str,object]:
        up=await self.get_user_project(user_project_id,user_id)
        if not up:raise HTTPException(404,"Project workspace not found")
        if any(item.status!="completed" for item in up.stage_progress):raise HTTPException(409,"Complete every project stage first")
        if up.status!="completed":
            now=datetime.now(timezone.utc);up.status="completed";up.completed_at=now;up.current_stage_index=max(0,up.total_stages-1)
            for requirement in up.project.required_skills:
                skill=(await self.db.execute(select(Skill).where(Skill.slug==str(requirement.get("skill_slug"))))).scalars().one_or_none()
                if not skill:continue
                user_skill=(await self.db.execute(select(UserSkill).where(UserSkill.user_id==up.user_id,UserSkill.skill_id==skill.id))).scalars().one_or_none()
                if not user_skill:user_skill=UserSkill(user_id=up.user_id,skill_id=skill.id);self.db.add(user_skill);await self.db.flush()
                user_skill.mastery_score=min(1,user_skill.mastery_score+.05);user_skill.last_practiced_at=now;self.db.add(SkillHistory(user_skill_id=user_skill.id,mastery_score=user_skill.mastery_score,change_reason=f"Completed project: {up.project.title}",recorded_at=now))
            await GamificationService(self.db).check_and_award_achievements(user_id)
        if commit:await self.db.commit()
        scores=[float(item.ai_score or 0) for item in up.stage_progress];return {"project_title":up.project.title,"average_stage_score":sum(scores)/max(1,len(scores)),"total_xp_earned":up.xp_earned}
    async def submit_final_project(self,user_project_id:str,user_id:str,project_description:str,final_code:str|None,reflection:str,challenges_faced:str,github_url:str|None)->dict[str,object]:
        up=await self.get_user_project(user_project_id,user_id)
        if not up or any(item.status!="completed" for item in up.stage_progress):raise HTTPException(409,"Complete all stages before final submission")
        if up.final_submission_id:
            existing=await self.db.get(ProjectSubmission,up.final_submission_id)
            if existing:return self._completion(up,existing)
        submission=ProjectSubmission(user_project_id=up.id,user_id=up.user_id,project_description=project_description,final_code=final_code,reflection=reflection,challenges_faced=challenges_faced,github_url=github_url,evaluation_status="evaluating");self.db.add(submission);await self.db.flush();stages=[{"stage":item.stage.title,"score":float(item.ai_score or 0),"feedback":(item.ai_feedback or {}).get("overall_feedback","")} for item in up.stage_progress];evaluation=await self.evaluator.evaluate_final_submission(up.project,up,submission,stages);submission.overall_score=float(evaluation["overall_score"]);submission.ai_evaluation=evaluation;submission.xp_awarded=int(evaluation["xp_awarded"]);submission.evaluation_status="complete";submission.evaluated_at=datetime.now(timezone.utc);up.final_submission_id=submission.id;up.xp_earned+=submission.xp_awarded;await GamificationService(self.db).award_xp(user_id,"project_completed",submission.xp_awarded,f"[project:{up.id}] Final project evaluation");await GamificationService(self.db).check_and_award_achievements(user_id);await self.db.commit();return self._completion(up,submission)
    async def get_recommended_projects(self,user_id:str)->list[ProjectLibraryItem]:
        library=await self.get_project_library(user_id);candidates=[item for item in library if item.user_status!="completed"];candidates.sort(key=lambda item:(not item.is_eligible,item.user_status!="active",item.difficulty_level));
        for item in candidates[:3]:item.recommendation_reason="Continue your active build" if item.user_status=="active" else "Matches your current skill readiness" if item.is_eligible else "A useful next challenge after prerequisites"
        return candidates[:3]
    @staticmethod
    def serialize_stage(stage:ProjectStage)->ProjectStageResponse:return ProjectStageResponse(id=str(stage.id),title=stage.title,description=stage.description,order_index=stage.order_index,stage_type=stage.stage_type,instructions=stage.instructions,deliverables=stage.deliverables,hints=stage.hints,resources=stage.resources,estimated_minutes=stage.estimated_minutes,validation_criteria=stage.validation_criteria)
    @classmethod
    def serialize_project(cls,item:Project,include_stages:bool=True)->ProjectResponse:return ProjectResponse(id=str(item.id),title=item.title,slug=item.slug,description=item.description,short_description=item.short_description,difficulty_level=item.difficulty_level,estimated_hours=item.estimated_hours,category=item.category,required_skills=item.required_skills,prerequisite_skills=item.prerequisite_skills,tech_stack=item.tech_stack,learning_outcomes=item.learning_outcomes,is_featured=item.is_featured,stages_count=len(item.stages),stages=[cls.serialize_stage(stage) for stage in item.stages] if include_stages else [])
    @classmethod
    def serialize_user_project(cls,up:UserProject)->UserProjectResponse:
        completed=sum(item.status=="completed" for item in up.stage_progress);return UserProjectResponse(id=str(up.id),project_id=str(up.project_id),status=up.status,current_stage_index=up.current_stage_index,total_stages=up.total_stages,xp_earned=up.xp_earned,progress_percentage=round(completed/max(1,up.total_stages)*100,1),started_at=up.started_at,completed_at=up.completed_at,last_active_at=up.last_active_at,work_data=up.work_data or {},project=cls.serialize_project(up.project),stage_progress=[UserProjectStageResponse(id=str(item.id),stage_id=str(item.stage_id),stage_order_index=item.stage_order_index,status=item.status,hints_used=item.hints_used,ai_score=item.ai_score,ai_feedback=item.ai_feedback,submitted_code=item.submitted_code,submitted_notes=item.submitted_notes,mentor_conversation_id=str(item.mentor_conversation_id) if item.mentor_conversation_id else None,started_at=item.started_at,completed_at=item.completed_at,stage=cls.serialize_stage(item.stage)) for item in up.stage_progress])
    @classmethod
    def serialize_library(cls,item:Project,up:UserProject|None,eligibility:dict[str,object])->ProjectLibraryItem:
        base=cls.serialize_project(item,False).model_dump();completed=sum(stage.status=="completed" for stage in up.stage_progress) if up else 0;return ProjectLibraryItem(**base,user_status=up.status if up else None,user_progress_percentage=round(completed/max(1,up.total_stages)*100,1) if up else 0,is_eligible=bool(eligibility["eligible"]),missing_prerequisites=list(eligibility["missing_prerequisites"]),user_project_id=str(up.id) if up else None)
    @staticmethod
    def _completion(up:UserProject,submission:ProjectSubmission)->dict[str,object]:
        evaluation=submission.ai_evaluation or {};scores=[float(item.ai_score or 0) for item in up.stage_progress];skills=[str(item.get("skill_slug","")).replace("-"," ").title() for item in up.project.required_skills];date=up.completed_at or submission.evaluated_at or datetime.now(timezone.utc);return {"project_title":up.project.title,"total_stages":up.total_stages,"completion_date":date,"average_stage_score":round(sum(scores)/max(1,len(scores)),3),"total_xp_earned":up.xp_earned,"skills_improved":skills,"completion_message":str(evaluation.get("completion_message",f"You completed {up.project.title}!")),"certificate_data":{"learner_name":up.user.full_name,"project_title":up.project.title,"grade":evaluation.get("grade","Completed"),"score_percentage":round(float(submission.overall_score or 0)*100),"completion_date":date.isoformat(),"xp_earned":submission.xp_awarded},"evaluation":evaluation}
    @staticmethod
    def _workspace_query():return select(UserProject).options(selectinload(UserProject.user),selectinload(UserProject.project).selectinload(Project.stages),selectinload(UserProject.stage_progress).selectinload(UserProjectStage.stage))
