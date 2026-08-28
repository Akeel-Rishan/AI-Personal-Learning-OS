"""Career readiness, gap analysis, action planning, and goal alignment."""
from __future__ import annotations
import asyncio,json,math,uuid
from datetime import date,datetime,timezone,timedelta
from fastapi import HTTPException
from sqlalchemy import func,select,update,delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.career import CareerRole,CareerSkillRequirement,UserCareerGoal
from app.models.goal import Goal
from app.models.progress import UserSkill
from app.models.skill import Skill
from app.models.user import UserProfile
from app.services.ai_service import AIService

WEIGHTS={"essential":3.0,"important":2.0,"beneficial":1.0,"optional":.5}
ACTION_CACHE:dict[str,tuple[datetime,tuple[tuple[str,int],...],dict[str,object]]]={}

class CareerService:
    def __init__(self,db:AsyncSession):self.db=db;self.ai=AIService()
    async def get_all_roles(self,category:str|None=None)->list[CareerRole]:
        query=self._role_query().where(CareerRole.is_active.is_(True));
        if category:query=query.where(CareerRole.category==category)
        return list((await self.db.execute(query.order_by(CareerRole.order_index))).scalars().unique())
    async def get_role_by_slug(self,slug:str)->CareerRole|None:return (await self.db.execute(self._role_query().where(CareerRole.slug==slug,CareerRole.is_active.is_(True)))).scalars().unique().one_or_none()
    async def get_role(self,role_id:str)->CareerRole|None:
        try:parsed=uuid.UUID(role_id)
        except ValueError:return None
        return (await self.db.execute(self._role_query().where(CareerRole.id==parsed,CareerRole.is_active.is_(True)))).scalars().unique().one_or_none()
    @staticmethod
    def calculate_readiness_from_inputs(role:CareerRole,current_mastery:dict[str,float],daily_minutes:int=60)->dict[str,object]:
        skills=[];weighted=weight_total=essential_sum=important_sum=0.;essential_count=important_count=0
        for requirement in role.skill_requirements:
            skill=requirement.skill;current=min(1,max(0,float(current_mastery.get(str(skill.id),0))));target=max(.01,float(requirement.target_mastery));minimum=float(requirement.min_mastery_required);readiness=min(current/target,1);gap=max(0,minimum-current)
            status="not_started" if current==0 else "ready" if current>=minimum else "close" if current>=minimum*.75 else "gap";weight=WEIGHTS.get(requirement.importance,1);weighted+=readiness*weight;weight_total+=weight
            if requirement.importance=="essential":essential_sum+=readiness;essential_count+=1
            if requirement.importance=="important":important_sum+=readiness;important_count+=1
            skills.append({"skill_id":str(skill.id),"skill_name":skill.name,"skill_slug":skill.slug,"category":skill.category,"importance":requirement.importance,"current_mastery":round(current,4),"current_mastery_percentage":round(current*100),"min_required":minimum,"min_required_percentage":round(minimum*100),"target_mastery":target,"target_mastery_percentage":round(target*100),"gap":round(gap,4),"gap_percentage":round(gap*100),"skill_readiness":round(readiness,4),"status":status,"relevance_note":requirement.relevance_note,"estimated_hours":float(skill.estimated_hours or 15)})
        overall=weighted/weight_total if weight_total else 0;essential=essential_sum/essential_count if essential_count else overall;important=important_sum/important_count if important_count else overall
        level="job_ready" if overall>=.85 and essential>=.90 else "nearly_ready" if overall>=.70 and essential>=.75 else "on_track" if overall>=.50 else "building_foundation" if overall>=.25 else "just_starting"
        gaps=[item for item in skills if item["status"] in {"gap","not_started","close"}];hours=sum(float(item["gap"])*float(item["estimated_hours"]) for item in gaps);weekly=max(1,daily_minutes)/60*7;weeks=math.ceil(hours/weekly) if hours else 0
        public=[{key:value for key,value in item.items() if key!="estimated_hours"} for item in skills]
        result={"role_id":str(role.id),"role_title":role.title,"role_slug":role.slug,"overall_readiness":round(overall,4),"overall_readiness_percentage":round(overall*100),"essential_readiness":round(essential,4),"important_readiness":round(important,4),"readiness_level":level,"skills":public,"estimated_weeks_to_ready":weeks}
        for name,statuses in [("ready_skills",{"ready"}),("close_skills",{"close"}),("gap_skills",{"gap"}),("not_started_skills",{"not_started"})]:result[name]=[item for item in public if item["status"] in statuses]
        result["critical_gaps"]=[item for item in public if item["importance"]=="essential" and item["status"] in {"gap","not_started"}];return result
    async def calculate_career_readiness(self,user_id:str,role_id:str)->dict[str,object]:
        role=await self.get_role(role_id)
        if not role:raise HTTPException(404,"Career role not found")
        uid=uuid.UUID(user_id);rows=(await self.db.execute(select(UserSkill).where(UserSkill.user_id==uid))).scalars().all();mastery={str(item.skill_id):float(item.mastery_score) for item in rows};daily=await self.db.scalar(select(UserProfile.daily_study_minutes).where(UserProfile.user_id==uid)) or 60;return self.calculate_readiness_from_inputs(role,mastery,daily)
    async def calculate_estimated_weeks(self,gap_skills:list[dict[str,object]],daily_minutes:int)->int:
        """Estimate calendar weeks from proportional skill gaps and study time."""
        total_hours=sum(float(item.get("gap",0))*float(item.get("estimated_hours",15)) for item in gap_skills)
        weekly_hours=max(1,daily_minutes)/60*7
        return math.ceil(total_hours/weekly_hours) if total_hours else 0
    async def generate_action_plan(self,user_id:str,role_id:str,readiness:dict[str,object]|None=None)->dict[str,object]:
        data=readiness or await self.calculate_career_readiness(user_id,role_id);role=await self.get_role(role_id)
        if not role:raise HTTPException(404,"Career role not found")
        signature=tuple(sorted((str(item["skill_id"]),int(item["current_mastery_percentage"])) for item in data["skills"]));key=f"action_plan_{user_id}_{role_id}";cached=ACTION_CACHE.get(key)
        if cached and datetime.now(timezone.utc)-cached[0]<timedelta(hours=1) and all(abs(dict(signature).get(k,0)-v)<=5 for k,v in cached[1]):return cached[2]
        fallback=self._fallback_plan(role,data);schema={"type":"object","properties":{"executive_summary":{"type":"string"},"estimated_job_ready_weeks":{"type":"integer"},"priority_phases":{"type":"array","items":{"type":"object","properties":{"phase_number":{"type":"integer"},"title":{"type":"string"},"duration_weeks":{"type":"integer"},"focus_skills":{"type":"array","items":{"type":"string"}},"description":{"type":"string"},"key_actions":{"type":"array","items":{"type":"string"}}},"required":["phase_number","title","duration_weeks","focus_skills","description","key_actions"],"additionalProperties":False}},"quick_wins":{"type":"array","items":{"type":"object","properties":{"skill":{"type":"string"},"skill_slug":{"type":"string"},"current":{"type":"integer"},"required":{"type":"integer"},"gap_percentage":{"type":"integer"},"action":{"type":"string"},"estimated_days":{"type":"integer"}},"required":["skill","skill_slug","current","required","gap_percentage","action","estimated_days"],"additionalProperties":False}},"encouragement":{"type":"string"},"market_note":{"type":"string"}},"required":["executive_summary","estimated_job_ready_weeks","priority_phases","quick_wins","encouragement","market_note"],"additionalProperties":False}
        try:plan=await asyncio.wait_for(self.ai.generate_structured(instructions="You are a practical career coach. Build a sequenced plan from prerequisite gaps. Return strict JSON.",prompt=f"Role: {role.title}\nReadiness: {data['overall_readiness_percentage']}%\nLevel: {data['readiness_level']}\nCritical gaps: {json.dumps(data['critical_gaps'])}\nOther gaps: {json.dumps(data['gap_skills'])}\nClose skills: {json.dumps(data['close_skills'])}",schema_name="career_action_plan",schema=schema,max_output_tokens=1700),timeout=20)
        except Exception:plan=fallback
        result={"role_id":role_id,"role_title":role.title,**plan,"generated_at":datetime.now(timezone.utc)};ACTION_CACHE[key]=(datetime.now(timezone.utc),signature,result);return result
    async def compare_roles(self,user_id:str,role_ids:list[str])->list[dict[str,object]]:return [await self.calculate_career_readiness(user_id,item) for item in role_ids]
    async def set_primary_career_goal(self,user_id:str,role_id:str,target_date:date|None=None,job_ready_alert:bool=False)->dict[str,object]:
        role=await self.get_role(role_id)
        if not role:raise HTTPException(404,"Career role not found")
        uid=uuid.UUID(user_id);await self.db.execute(update(UserCareerGoal).where(UserCareerGoal.user_id==uid).values(is_primary=False));goal=(await self.db.execute(select(UserCareerGoal).where(UserCareerGoal.user_id==uid,UserCareerGoal.career_role_id==role.id))).scalars().one_or_none();readiness=await self.calculate_career_readiness(user_id,role_id)
        if not goal:goal=UserCareerGoal(user_id=uid,career_role_id=role.id,initial_readiness=float(readiness["overall_readiness"]));self.db.add(goal)
        goal.is_primary=True;goal.current_readiness=float(readiness["overall_readiness"]);goal.target_date=target_date;goal.notes=json.dumps({"job_ready_alert":job_ready_alert});await self.db.commit();await self.db.refresh(goal);alignment=await self.sync_career_goal_with_learning_goal(user_id,role);return {"career_goal":{**self.serialize_goal(goal,role),"job_ready_alert":job_ready_alert},"role":self.serialize_role(role),"readiness":readiness,"readiness_change":round(float(goal.current_readiness or 0)-float(goal.initial_readiness or 0),4),"roadmap_alignment":alignment}
    async def get_primary_career_goal(self,user_id:str)->dict[str,object]|None:
        goal=(await self.db.execute(select(UserCareerGoal).options(selectinload(UserCareerGoal.career_role).selectinload(CareerRole.skill_requirements).selectinload(CareerSkillRequirement.skill)).where(UserCareerGoal.user_id==uuid.UUID(user_id),UserCareerGoal.is_primary.is_(True)))).scalars().unique().one_or_none()
        if not goal:return None
        readiness=await self.calculate_career_readiness(user_id,str(goal.career_role_id));goal.current_readiness=float(readiness["overall_readiness"]);await self.db.commit();notes=json.loads(goal.notes or "{}") if goal.notes else {};return {"career_goal":{**self.serialize_goal(goal,goal.career_role),"job_ready_alert":bool(notes.get("job_ready_alert",False))},"role":self.serialize_role(goal.career_role),"readiness":readiness,"readiness_change":round(float(goal.current_readiness or 0)-float(goal.initial_readiness or 0),4)}
    async def remove_primary_goal(self,user_id:str)->None:await self.db.execute(delete(UserCareerGoal).where(UserCareerGoal.user_id==uuid.UUID(user_id),UserCareerGoal.is_primary.is_(True)));await self.db.commit()
    async def sync_career_goal_with_learning_goal(self,user_id:str,role:CareerRole)->dict[str,object]:
        goal=(await self.db.execute(select(Goal).options(selectinload(Goal.goal_skills)).where(Goal.user_id==uuid.UUID(user_id),Goal.status=="active").order_by(Goal.created_at.desc()))).scalars().first();essential={item.skill_id:item.skill.name for item in role.skill_requirements if item.importance=="essential"}
        if not goal:return {"missing_from_roadmap":list(essential.values()),"suggestion":"Create a learning goal to turn this career target into a roadmap."}
        present={item.skill_id for item in goal.goal_skills};missing=[name for skill_id,name in essential.items() if skill_id not in present];return {"missing_from_roadmap":missing,"suggestion":f"Your {role.title} goal requires {', '.join(missing)} outside your current roadmap. Consider adding them." if missing else "Your current roadmap covers every essential career skill."}
    async def get_role_categories(self)->list[dict[str,object]]:
        rows=(await self.db.execute(select(CareerRole.category,func.count(CareerRole.id)).where(CareerRole.is_active.is_(True)).group_by(CareerRole.category))).all();labels={"ml-ai":"ML & AI","data-science":"Data Science","devops":"DevOps","research":"Research"};return [{"category":category,"label":labels.get(category,category.title()),"count":count} for category,count in rows]
    async def get_market_insights(self,role_id:str)->dict[str,object]:
        role=await self.get_role(role_id)
        if not role:raise HTTPException(404,"Career role not found")
        skills=[item.skill.name for item in role.skill_requirements[:6]]
        fallback={"demand_description":f"{role.title} roles show {role.demand_level.replace('-',' ')} general demand across technology-focused organizations.","key_skills_in_demand":skills,"emerging_technologies":["AI-assisted development","Cloud-native platforms","Responsible AI"],"typical_interview_topics":["System design","Practical coding","Trade-off analysis"],"portfolio_recommendations":["Publish one end-to-end project","Document measurable results","Include tests and deployment notes"],"disclaimer":"These are general trends and may not reflect current market conditions."}
        schema={"type":"object","properties":{"demand_description":{"type":"string"},"key_skills_in_demand":{"type":"array","items":{"type":"string"}},"emerging_technologies":{"type":"array","items":{"type":"string"}},"typical_interview_topics":{"type":"array","items":{"type":"string"}},"portfolio_recommendations":{"type":"array","items":{"type":"string"}},"disclaimer":{"type":"string"}},"required":["demand_description","key_skills_in_demand","emerging_technologies","typical_interview_topics","portfolio_recommendations","disclaimer"],"additionalProperties":False}
        try:
            insights=await asyncio.wait_for(self.ai.generate_structured(instructions="Generate general career market trends from broad knowledge, never claim real-time data, and return strict JSON.",prompt=f"Role: {role.title}\nSkills: {', '.join(skills)}\nDemand label: {role.demand_level}\nThe disclaimer must say these are general trends and may not reflect current market conditions.",schema_name="career_market_insights",schema=schema,max_output_tokens=900),timeout=20)
        except Exception:insights=fallback
        insights["disclaimer"]="These are general trends and may not reflect current market conditions."
        return {"role_title":role.title,**insights}
    @classmethod
    def serialize_role(cls,role:CareerRole,include_skills:bool=True)->dict[str,object]:return {"id":str(role.id),"title":role.title,"slug":role.slug,"description":role.description,"short_description":role.short_description,"category":role.category,"seniority_level":role.seniority_level,"average_salary_usd":role.average_salary_usd,"demand_level":role.demand_level,"typical_companies":role.typical_companies,"responsibilities":role.responsibilities,"related_role_slugs":role.related_role_slugs,"is_featured":role.is_featured,"skill_requirements":[{"skill_id":str(item.skill_id),"skill_name":item.skill.name,"skill_slug":item.skill.slug,"skill_category":item.skill.category,"importance":item.importance,"min_mastery_required":item.min_mastery_required,"min_mastery_percentage":round(item.min_mastery_required*100),"target_mastery":item.target_mastery,"target_mastery_percentage":round(item.target_mastery*100),"relevance_note":item.relevance_note,"order_index":item.order_index} for item in role.skill_requirements] if include_skills else []}
    @staticmethod
    def serialize_goal(goal:UserCareerGoal,role:CareerRole)->dict[str,object]:return {"id":str(goal.id),"role_id":str(role.id),"role_title":role.title,"role_slug":role.slug,"is_primary":goal.is_primary,"initial_readiness":goal.initial_readiness,"current_readiness":goal.current_readiness,"target_date":goal.target_date,"created_at":goal.created_at}
    @staticmethod
    def _fallback_plan(role:CareerRole,data:dict[str,object])->dict[str,object]:
        critical=list(data["critical_gaps"]);other=[item for item in list(data["gap_skills"])+list(data["not_started_skills"]) if item not in critical];groups=[critical,other,list(data["close_skills"])];titles=["Build Essential Foundations","Develop Role Skills","Finish Quick Wins"];phases=[]
        for index,items in enumerate(groups):
            if not items:continue
            names=[str(item["skill_name"]) for item in items[:5]];phases.append({"phase_number":len(phases)+1,"title":titles[index],"duration_weeks":max(1,math.ceil(int(data["estimated_weeks_to_ready"] or 1)/max(1,len([g for g in groups if g])))),"focus_skills":names,"description":f"Build measurable mastery in {', '.join(names)}.","key_actions":[f"Practice {name} consistently and complete its exercises" for name in names[:3]]})
        close=list(data["close_skills"]);quick=[{"skill":item["skill_name"],"skill_slug":item["skill_slug"],"current":item["current_mastery_percentage"],"required":item["min_required_percentage"],"gap_percentage":item["gap_percentage"],"action":f"Practice {item['skill_name']} for 30 minutes daily","estimated_days":max(3,int(item["gap_percentage"]))} for item in (close or list(data["critical_gaps"])[:2])]
        return {"executive_summary":f"You are {data['overall_readiness_percentage']}% ready for {role.title}. Start with essential foundations, then close the smaller role-specific gaps.","estimated_job_ready_weeks":int(data["estimated_weeks_to_ready"] or 0),"priority_phases":phases,"quick_wins":quick,"encouragement":"Every completed skill moves your profile closer to the target role. Focus on one measurable improvement at a time.","market_note":f"{role.title} has {role.demand_level.replace('-',' ')} general demand."}
    @staticmethod
    def _role_query():return select(CareerRole).options(selectinload(CareerRole.skill_requirements).selectinload(CareerSkillRequirement.skill))
