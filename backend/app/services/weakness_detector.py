"""Fast attempt-pattern analysis and AI-assisted misconception detection."""
from __future__ import annotations
import asyncio, json, uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.assessment import Assessment, AssessmentAttempt, AssessmentQuestion
from app.models.exercise import Exercise, ExerciseAttempt
from app.models.progress import UserSkill
from app.models.skill import Skill, SkillPrerequisite
from app.services.ai_service import AIService
from app.services.spaced_repetition import SpacedRepetitionScheduler

class WeaknessDetector:
    def __init__(self, db: AsyncSession): self.db=db; self.ai=AIService()

    async def _attempts(self, user_id: str, skill_id: str, limit: int) -> list[dict[str, object]]:
        user, skill=uuid.UUID(user_id),uuid.UUID(skill_id)
        exercise_rows=(await self.db.execute(select(ExerciseAttempt,Exercise).join(Exercise).where(ExerciseAttempt.user_id==user,Exercise.skill_id==skill,ExerciseAttempt.is_correct.is_not(None)).order_by(ExerciseAttempt.created_at.desc()).limit(limit))).all()
        assessment_rows=(await self.db.execute(select(AssessmentAttempt,AssessmentQuestion).join(AssessmentQuestion).join(Assessment).where(Assessment.user_id==user,AssessmentQuestion.skill_id==skill,AssessmentAttempt.is_correct.is_not(None)).order_by(AssessmentAttempt.created_at.desc()).limit(limit))).all()
        rows=[{"created_at":a.created_at,"is_correct":bool(a.is_correct),"score":float(a.score or 0),"question":e.content.get("problem_statement",e.title),"user_answer":a.user_answer or "","correct":e.solution or "","difficulty":e.difficulty} for a,e in exercise_rows]
        rows += [{"created_at":a.created_at,"is_correct":bool(a.is_correct),"score":float(a.score or 0),"question":q.question_text,"user_answer":a.user_answer or "","correct":q.correct_answer or "","difficulty":q.difficulty} for a,q in assessment_rows]
        return sorted(rows,key=lambda item:item["created_at"],reverse=True)[:limit]

    async def analyze_skill_attempts(self,user_id:str,skill_id:str,recent_n:int=10)->dict[str,object]:
        parsed=uuid.UUID(skill_id); skill=await self.db.get(Skill,parsed); attempts=await self._attempts(user_id,skill_id,recent_n)
        user_skill=(await self.db.execute(select(UserSkill).options(selectinload(UserSkill.history)).where(UserSkill.user_id==uuid.UUID(user_id),UserSkill.skill_id==parsed))).scalars().one_or_none()
        consecutive=0
        for item in attempts:
            if item["is_correct"]: break
            consecutive+=1
        accuracy=sum(bool(item["is_correct"]) for item in attempts)/len(attempts) if attempts else 1.0; recent=attempts[:5]; recent_accuracy=sum(bool(item["is_correct"]) for item in recent)/len(recent) if recent else 1.0
        history=sorted(user_skill.history,key=lambda item:item.recorded_at) if user_skill else []; delta=(history[-1].mastery_score-history[-2].mastery_score) if len(history)>1 else 0
        prereq_ids=list((await self.db.execute(select(SkillPrerequisite.prerequisite_id).where(SkillPrerequisite.skill_id==parsed))).scalars()); prereq_weak=False
        if prereq_ids: prereq_weak=bool((await self.db.execute(select(UserSkill.id).where(UserSkill.user_id==uuid.UUID(user_id),UserSkill.skill_id.in_(prereq_ids),UserSkill.mastery_score<.4).limit(1))).scalar_one_or_none())
        distribution={"easy":0,"medium":0,"hard":0}
        for item in attempts:
            if not item["is_correct"]: distribution["easy" if int(item["difficulty"])<=2 else "medium" if int(item["difficulty"])<=4 else "hard"]+=1
        urgency="critical" if consecutive>=5 or (attempts and recent_accuracy<.25) else "high" if consecutive>=3 or (len(attempts)>=5 and recent_accuracy<.4) else "medium" if len(attempts)>=3 and recent_accuracy<.5 else "none"
        return {"skill_id":skill_id,"skill_name":skill.name if skill else "Unknown skill","total_attempts":len(attempts),"consecutive_incorrect":consecutive,"overall_accuracy":round(accuracy,3),"recent_accuracy":round(recent_accuracy,3),"current_mastery":float(user_skill.mastery_score) if user_skill else 0,"mastery_trend":"improving" if delta>.01 else "declining" if delta<-.01 else "stagnant","wrong_answers":[{k:v for k,v in item.items() if k not in {"created_at","is_correct","score","difficulty"}} for item in attempts if not item["is_correct"]],"difficulty_distribution":distribution,"prerequisite_weak":prereq_weak,"needs_intervention":urgency!="none","intervention_urgency":urgency}

    async def scan_all_user_skills(self,user_id:str)->list[dict[str,object]]:
        ids=list((await self.db.execute(select(UserSkill.skill_id).where(UserSkill.user_id==uuid.UUID(user_id),UserSkill.times_practiced>0))).scalars()); results=[]
        for skill_id in ids:
            analysis=await self.analyze_skill_attempts(user_id,str(skill_id))
            if analysis["needs_intervention"]: results.append(analysis)
        order={"critical":0,"high":1,"medium":2,"low":3,"none":4}; return sorted(results,key=lambda item:order[str(item["intervention_urgency"])])

    async def detect_consecutive_failures(self,user_id:str,skill_id:str,threshold:int=3)->dict[str,object]|None:
        attempts=await self._attempts(user_id,skill_id,max(6,threshold)); count=0
        for item in attempts:
            if item["is_correct"]: break
            count+=1
        if count<threshold:return None
        skill=await self.db.get(Skill,uuid.UUID(skill_id)); return {"detected":True,"consecutive_count":count,"skill_id":skill_id,"skill_name":skill.name if skill else "Unknown skill","recent_wrong_answers":attempts[:count],"urgency":"critical" if count>=5 else "high" if count>=3 else "medium"}

    async def detect_accuracy_decline(self,user_id:str,skill_id:str,window:int=10,threshold:float=.5)->dict[str,object]|None:
        attempts=await self._attempts(user_id,skill_id,window)
        if len(attempts)<3:return None
        accuracy=sum(bool(item["is_correct"]) for item in attempts)/len(attempts)
        if accuracy>=threshold:return None
        skill=await self.db.get(Skill,uuid.UUID(skill_id)); return {"detected":True,"accuracy":round(accuracy,3),"attempts_analyzed":len(attempts),"skill_id":skill_id,"skill_name":skill.name if skill else "Unknown skill","urgency":"high" if accuracy<.3 else "medium"}

    async def detect_mastery_decay(self,user_id:str,days_inactive:int=14)->list[dict[str,object]]:
        cutoff=datetime.now(timezone.utc)-timedelta(days=days_inactive); rows=list((await self.db.execute(select(UserSkill).options(selectinload(UserSkill.skill)).where(UserSkill.user_id==uuid.UUID(user_id),UserSkill.mastery_score>.5,UserSkill.last_practiced_at<cutoff))).scalars()); result=[]
        for row in rows:
            days=(datetime.now(timezone.utc).date()-row.last_practiced_at.date()).days; retention=SpacedRepetitionScheduler.calculate_retention(row.mastery_score,days)
            if retention<.6: result.append({"skill_id":str(row.skill_id),"skill_name":row.skill.name,"last_mastery":row.mastery_score,"estimated_retention":retention,"days_inactive":days,"mastery_decay":True,"decay_severity":"critical" if retention<.3 else "high" if retention<.45 else "medium"})
        return result

    async def identify_misconception(self,skill_name:str,wrong_answers:list[dict[str,object]])->dict[str,object]:
        fallback={"misconception":f"Difficulty with {skill_name} concepts","confused_concepts":[],"root_cause":"Insufficient practice with core concepts","correction":f"Review the fundamentals of {skill_name} with focused examples","confidence":"low"}
        schema={"type":"object","properties":{"misconception":{"type":"string"},"confused_concepts":{"type":"array","items":{"type":"string"}},"root_cause":{"type":"string"},"correction":{"type":"string"},"confidence":{"type":"string","enum":["high","medium","low"]}},"required":["misconception","confused_concepts","root_cause","correction","confidence"],"additionalProperties":False}
        try:
            return await asyncio.wait_for(self.ai.generate_structured(instructions="You are an educational psychologist. Identify the precise root misconception. Return JSON only.",prompt=f"Skill: {skill_name}\nWrong answers:\n{json.dumps(wrong_answers,default=str)}",schema_name="knowledge_gap_misconception",schema=schema,max_output_tokens=700),timeout=15)
        except Exception:return fallback
