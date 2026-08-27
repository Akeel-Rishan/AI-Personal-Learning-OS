"""Central orchestrator for detection, classification, intervention, and resolution."""
from __future__ import annotations
import asyncio, logging, time, uuid
from collections import Counter
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.adaptive import AdaptationEvent, KnowledgeGap
from app.models.gamification import XPEvent
from app.models.progress import UserSkill
from app.models.skill import Skill
from app.services.gamification_service import GamificationService
from app.services.intervention_planner import InterventionPlanner
from app.services.knowledge_gap_classifier import KnowledgeGapClassifier
from app.services.roadmap_adapter import RoadmapAdapter
from app.services.tutor_service import TutorService
from app.services.weakness_detector import WeaknessDetector

logger=logging.getLogger(__name__); ACTIVE=("active","in_progress","acknowledged")

class AdaptiveEngine:
    def __init__(self,db:AsyncSession): self.db=db; self.detector=WeaknessDetector(db); self.classifier=KnowledgeGapClassifier(); self.adapter=RoadmapAdapter(db); self.planner=InterventionPlanner(db)
    async def process_exercise_attempt(self,user_id:str,skill_id:str,attempt_result:dict[str,object])->dict[str,object]|None:
        if bool(attempt_result.get("is_correct")):
            return await self.check_gap_resolution(user_id,skill_id,float(attempt_result.get("new_mastery",0)))
        failure=await self.detector.detect_consecutive_failures(user_id,skill_id,3)
        if not failure:return None
        analysis=await self.detector.analyze_skill_attempts(user_id,skill_id); schedule_adaptation(user_id,skill_id,analysis); return {"queued":True,"skill_id":skill_id,"severity":failure["urgency"],"message":"A targeted adaptation is being prepared."}
    async def process_assessment_result(self,user_id:str,assessment_id:str,skill_scores:list[dict[str,object]])->list[dict[str,object]]:
        results=[]
        for score in skill_scores:
            value=float(score.get("mastery_score",score.get("score",1)))
            if value>=.45: continue
            skill_id=str(score["skill_id"]); analysis=await self.detector.analyze_skill_attempts(user_id,skill_id); analysis.update({"needs_intervention":True,"recent_accuracy":value,"overall_accuracy":value,"trigger_type":"assessment_low_score"}); result=await self._run_analysis_and_adapt(user_id,skill_id,analysis)
            if result: results.append(result)
        return results
    async def run_full_adaptation_scan(self,user_id:str)->dict[str,object]:
        started=time.perf_counter(); analyses=await self.detector.scan_all_user_skills(user_id); decayed=await self.detector.detect_mastery_decay(user_id); details=[]
        for analysis in analyses:
            result=await self._run_analysis_and_adapt(user_id,str(analysis["skill_id"]),analysis)
            if result:details.append(result)
        for decay in decayed:
            analysis={**decay,"total_attempts":10,"consecutive_incorrect":0,"recent_accuracy":.6,"overall_accuracy":.6,"mastery_trend":"declining","current_mastery":decay["last_mastery"],"needs_intervention":True,"trigger_type":"skill_decay"}; result=await self._run_analysis_and_adapt(user_id,str(decay["skill_id"]),analysis)
            if result:details.append(result)
        resolved=0; active=await self.get_active_gaps(user_id)
        for gap in active:
            mastery=float(await self.db.scalar(select(UserSkill.mastery_score).where(UserSkill.user_id==uuid.UUID(user_id),UserSkill.skill_id==gap.skill_id)) or 0)
            if await self.adapter.resolve_gap_if_mastered(str(gap.id),mastery): await GamificationService(self.db).award_xp(user_id,"gap_resolved",100,f"Resolved knowledge gap {gap.id}"); resolved+=1
        await self.db.commit(); duration=round((time.perf_counter()-started)*1000)
        detected=sum(not bool(item.get("duplicate_prevented")) for item in details)
        return {"gaps_detected":detected,"gaps_resolved":resolved,"adaptations_made":sum(bool(item.get("adapted")) for item in details),"adaptation_details":details,"decayed_skills":[str(item["skill_name"]) for item in decayed],"scan_duration_ms":duration,"message":f"Scan complete: {detected} new gaps detected, {resolved} resolved."}
    async def trigger_manual_adaptation(self,user_id:str,skill_id:str|None=None)->dict[str,object]:
        if not skill_id:return await self.run_full_adaptation_scan(user_id)
        started=time.perf_counter(); analysis=await self.detector.analyze_skill_attempts(user_id,skill_id); analysis["trigger_type"]="manual_request"; analysis["needs_intervention"]=True; result=await self._run_analysis_and_adapt(user_id,skill_id,analysis); await self.db.commit(); return {"gaps_detected":1 if result else 0,"gaps_resolved":0,"adaptations_made":1 if result and result.get("adapted") else 0,"adaptation_details":[result] if result else [],"decayed_skills":[],"scan_duration_ms":round((time.perf_counter()-started)*1000),"message":"Manual adaptation complete."}
    async def get_active_gaps(self,user_id:str)->list[KnowledgeGap]:
        severity_order={"critical":0,"high":1,"medium":2,"low":3}; rows=list((await self.db.execute(select(KnowledgeGap).options(selectinload(KnowledgeGap.skill)).where(KnowledgeGap.user_id==uuid.UUID(user_id),KnowledgeGap.status.in_(ACTIVE)).order_by(KnowledgeGap.detected_at.desc()))).scalars()); return sorted(rows,key=lambda gap:(severity_order.get(gap.gap_severity,4),-gap.detected_at.timestamp()))
    async def get_adaptation_history(self,user_id:str,limit:int=20,skill_id:str|None=None)->list[AdaptationEvent]:
        query=select(AdaptationEvent).options(selectinload(AdaptationEvent.skill)).where(AdaptationEvent.user_id==uuid.UUID(user_id));
        if skill_id:query=query.where(AdaptationEvent.skill_id==uuid.UUID(skill_id))
        return list((await self.db.execute(query.order_by(AdaptationEvent.created_at.desc()).limit(limit))).scalars())
    async def check_gap_resolution(self,user_id:str,skill_id:str,new_mastery:float)->dict[str,object]|None:
        gap=(await self.db.execute(select(KnowledgeGap).options(selectinload(KnowledgeGap.skill)).where(KnowledgeGap.user_id==uuid.UUID(user_id),KnowledgeGap.skill_id==uuid.UUID(skill_id),KnowledgeGap.status.in_(ACTIVE)))).scalars().one_or_none()
        if not gap or not await self.adapter.resolve_gap_if_mastered(str(gap.id),new_mastery):return None
        await GamificationService(self.db).award_xp(user_id,"gap_resolved",100,f"Resolved gap in {gap.skill.name}"); return {"gap_resolved":True,"gap_id":str(gap.id),"skill_name":gap.skill.name,"mastery_improvement":round(new_mastery-gap.mastery_at_detection,3),"xp_awarded":100}
    async def _run_analysis_and_adapt(self,user_id:str,skill_id:str,analysis:dict[str,object])->dict[str,object]|None:
        if not analysis.get("needs_intervention"):return None
        existing=(await self.db.execute(select(KnowledgeGap).where(KnowledgeGap.user_id==uuid.UUID(user_id),KnowledgeGap.skill_id==uuid.UUID(skill_id),KnowledgeGap.status.in_(ACTIVE)))).scalars().one_or_none()
        if existing:
            existing.evidence={**existing.evidence,**{key:value for key,value in analysis.items() if key not in {"wrong_answers"}},"wrong_answers":analysis.get("wrong_answers",[])[:10]}; existing.notification_dismissed=False
            return {"adapted":False,"gap_id":str(existing.id),"duplicate_prevented":True,"description":"Existing active gap evidence updated."}
        skill=await self.db.get(Skill,uuid.UUID(skill_id)); misconception=await self.detector.identify_misconception(skill.name,list(analysis.get("wrong_answers",[]))); classification=self.classifier.classify_gap(analysis,misconception)
        gap=KnowledgeGap(user_id=uuid.UUID(user_id),skill_id=skill.id,gap_type=str(classification["gap_type"]),gap_severity=str(classification["gap_severity"]),description=f"A {classification['gap_type']} gap was detected in {skill.name}.",misconception=str(misconception["misconception"]),evidence={**{key:value for key,value in analysis.items() if key not in {"wrong_answers"}},"wrong_answers":analysis.get("wrong_answers",[])[:10],"trigger_type":analysis.get("trigger_type","consecutive_incorrect")},status="active",mastery_at_detection=float(analysis.get("current_mastery",0))); self.db.add(gap); await self.db.flush()
        context=await TutorService(self.db).build_learner_context(user_id); plan=await self.planner.plan_intervention(gap,skill,context); tutor_id=await self.planner.generate_tutor_conversation_for_gap(user_id,gap,skill,plan); adaptation=await self.adapter.adapt_roadmap_for_gap(user_id,gap,classification)
        gap.status="in_progress" if adaptation.get("adapted") else "active"; gap.intervention_items={**(gap.intervention_items or {}),"tutor_conversation_id":tutor_id,"plan":plan,"estimated_fix_minutes":classification["estimated_intervention_minutes"]}; adaptation.update({"gap_id":str(gap.id),"skill_name":skill.name,"severity":gap.gap_severity,"tutor_conversation_id":tutor_id}); return adaptation

async def _background(user_id:str,skill_id:str,analysis:dict[str,object])->None:
    try:
        async with AsyncSessionLocal() as db:
            await AdaptiveEngine(db)._run_analysis_and_adapt(user_id,skill_id,analysis); await db.commit()
    except Exception: logger.exception("Background adaptation failed for user=%s skill=%s",user_id,skill_id)
def schedule_adaptation(user_id:str,skill_id:str,analysis:dict[str,object])->None: asyncio.create_task(_background(user_id,skill_id,analysis))
async def run_full_scan_background(user_id:str)->None:
    try:
        async with AsyncSessionLocal() as db: await AdaptiveEngine(db).run_full_adaptation_scan(user_id)
    except Exception: logger.exception("Background full adaptation scan failed for user=%s",user_id)

async def run_assessment_adaptation_background(user_id:str,assessment_id:str,skill_scores:list[dict[str,object]])->None:
    try:
        async with AsyncSessionLocal() as db:
            await AdaptiveEngine(db).process_assessment_result(user_id,assessment_id,skill_scores)
            await db.commit()
    except Exception: logger.exception("Background assessment adaptation failed for user=%s assessment=%s",user_id,assessment_id)

def schedule_assessment_adaptation(user_id:str,assessment_id:str,skill_scores:list[dict[str,object]])->None:
    asyncio.create_task(run_assessment_adaptation_background(user_id,assessment_id,skill_scores))
