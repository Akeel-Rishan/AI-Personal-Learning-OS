"""Transactional roadmap and daily-plan adaptation strategies."""
from __future__ import annotations
import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.adaptive import AdaptationEvent, KnowledgeGap
from app.models.learning import DailyPlan, DailyPlanItem
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.skill import Skill

ITEM_MAP={"focused_lesson":("lesson","Targeted Review",25),"visual_examples":("lesson","Visual Walkthrough",20),"comprehension_check":("assessment","Understanding Check",10),"step_by_step_exercise":("exercise","Step-by-Step Practice",20),"guided_exercise":("exercise","Guided Exercise",20),"independent_exercise":("exercise","Independent Challenge",25),"practice_exercise":("exercise","Targeted Practice",15),"spaced_review":("review","Spaced Review",15),"recall_exercise":("exercise","Recall Challenge",20),"application_exercise":("exercise","Application Challenge",20),"prerequisite_review":("review","Prerequisite Review",20),"bridge_exercise":("exercise","Bridge Exercise",20),"skill_check":("assessment","Skill Check",15)}

class RoadmapAdapter:
    def __init__(self,db:AsyncSession): self.db=db
    async def _roadmap(self,user_id:str)->Roadmap|None:
        return (await self.db.execute(select(Roadmap).options(selectinload(Roadmap.phases).selectinload(RoadmapPhase.items)).where(Roadmap.user_id==uuid.UUID(user_id),Roadmap.status=="active").order_by(Roadmap.created_at.desc()).limit(1))).scalars().unique().one_or_none()
    async def generate_intervention_items(self,skill:Skill,gap:KnowledgeGap,template:dict[str,object],start_order_index:int=0)->list[dict[str,object]]:
        result=[]
        for index,key in enumerate(template.get("items",[])):
            kind,label,minutes=ITEM_MAP.get(str(key),("review","Focused Review",15)); suffix=f" #{index+1}" if key=="practice_exercise" else ""
            result.append({"item_type":kind,"title":f"{skill.name}: {label}{suffix}","description":gap.misconception or gap.description,"order_index":start_order_index+index,"estimated_minutes":minutes,"skill_id":skill.id,"status":"active" if index==0 else "pending"})
        return result
    async def create_intervention_phase(self,roadmap:Roadmap,skill:Skill,gap:KnowledgeGap,template:dict[str,object],insert_index:int)->RoadmapPhase:
        await self.db.execute(update(RoadmapPhase).where(RoadmapPhase.roadmap_id==roadmap.id,RoadmapPhase.order_index>=insert_index).values(order_index=RoadmapPhase.order_index+1))
        phase=RoadmapPhase(roadmap_id=roadmap.id,title=f"Gap Fix: {skill.name}",description=gap.misconception or gap.description,order_index=insert_index,status="active",estimated_weeks=1,started_at=datetime.now(timezone.utc),phase_metadata={"source":"adaptive_engine","gap_id":str(gap.id),"trigger":gap.evidence}); self.db.add(phase); await self.db.flush()
        for values in await self.generate_intervention_items(skill,gap,template): self.db.add(RoadmapItem(phase=phase,**values))
        await self.db.flush()
        roadmap.total_phases+=1; roadmap.current_phase_index=insert_index; return phase
    async def insert_items_into_current_phase(self,roadmap:Roadmap,skill:Skill,gap:KnowledgeGap,template:dict[str,object])->list[RoadmapItem]:
        phase=next((p for p in roadmap.phases if p.status=="active"),None) or next((p for p in roadmap.phases if p.status!="completed"),None)
        if not phase:return []
        first=min((item.order_index for item in phase.items if item.status in {"pending","active"}),default=len(phase.items)); count=len(template.get("items",[])); await self.db.execute(update(RoadmapItem).where(RoadmapItem.phase_id==phase.id,RoadmapItem.order_index>=first).values(order_index=RoadmapItem.order_index+count))
        items=[]
        for values in await self.generate_intervention_items(skill,gap,template,first): item=RoadmapItem(phase_id=phase.id,**values); self.db.add(item); items.append(item)
        await self.db.flush(); return items
    async def _insert_daily(self,user_id:str,skill:Skill,gap:KnowledgeGap,template:dict[str,object])->list[DailyPlanItem]:
        target=date.today(); plan=(await self.db.execute(select(DailyPlan).options(selectinload(DailyPlan.items)).where(DailyPlan.user_id==uuid.UUID(user_id),DailyPlan.plan_date==target))).scalars().unique().one_or_none()
        if plan is None: plan=DailyPlan(user_id=uuid.UUID(user_id),plan_date=target,status="pending",total_estimated_minutes=0,ai_generated_note="Adaptive intervention plan"); self.db.add(plan); await self.db.flush()
        await self.db.execute(update(DailyPlanItem).where(DailyPlanItem.daily_plan_id==plan.id).values(order_index=DailyPlanItem.order_index+3)); items=[]
        for values in (await self.generate_intervention_items(skill,gap,template))[:3]:
            item=DailyPlanItem(daily_plan_id=plan.id,skill_id=skill.id,title=str(values["title"]),description=str(values["description"]),item_type=str(values["item_type"]),order_index=int(values["order_index"]),estimated_minutes=int(values["estimated_minutes"]),status="pending"); self.db.add(item); items.append(item); plan.total_estimated_minutes+=item.estimated_minutes
        await self.db.flush(); return items
    async def adapt_roadmap_for_gap(self,user_id:str,gap:KnowledgeGap,classification:dict[str,object])->dict[str,object]:
        skill=await self.db.get(Skill,gap.skill_id); roadmap=await self._roadmap(user_id); severity=str(classification["gap_severity"]); template=dict(classification["intervention_template"]); inserted=[]; phase_paused=False; new_phase=False; action="flagged_for_review"
        async with self.db.begin_nested():
            if severity=="critical" and roadmap:
                active=next((p for p in roadmap.phases if p.status=="active"),None); index=active.order_index if active else roadmap.current_phase_index
                if active: active.status="paused"; phase_paused=True
                phase=await self.create_intervention_phase(roadmap,skill,gap,template,index); inserted=[str(item.id) for item in phase.items]; new_phase=True; action="paused_phase"
            elif severity=="high" and roadmap:
                items=await self.insert_items_into_current_phase(roadmap,skill,gap,template); inserted=[str(item.id) for item in items]; action="inserted_review"
            elif severity=="medium":
                items=await self._insert_daily(user_id,skill,gap,template); inserted=[str(item.id) for item in items]; action="inserted_exercises"
            roadmap_id=roadmap.id if roadmap else None; description=f"Added {len(inserted)} targeted items for {skill.name}" if inserted else f"Flagged {skill.name} for review"
            event=AdaptationEvent(user_id=gap.user_id,roadmap_id=roadmap_id,skill_id=gap.skill_id,trigger_type=str(gap.evidence.get("trigger_type","repeated_mistakes")),gap_type=gap.gap_type,gap_severity=gap.gap_severity,gap_description=gap.description,misconception_identified=gap.misconception,action_taken=action,action_description=description,items_inserted={"inserted_item_ids":inserted,"modified_item_ids":[]},ai_reasoning=gap.misconception); self.db.add(event); gap.intervention_created=bool(inserted); gap.intervention_items={"inserted_item_ids":inserted,"action":action}
            if roadmap: roadmap.last_adapted_at=datetime.now(timezone.utc)
        return {"adapted":bool(inserted),"adaptation_type":action,"items_inserted":inserted,"items_modified":[],"new_phase_created":new_phase,"phase_paused":phase_paused,"description":description}
    async def resolve_gap_if_mastered(self,gap_id:str,current_mastery:float,resolution_threshold:float=.65)->bool:
        gap=await self.db.get(KnowledgeGap,uuid.UUID(gap_id));
        if not gap or gap.status=="resolved" or current_mastery<resolution_threshold:return False
        gap.status="resolved"; gap.resolved_at=datetime.now(timezone.utc); gap.mastery_at_resolution=current_mastery
        events=list((await self.db.execute(select(AdaptationEvent).where(AdaptationEvent.user_id==gap.user_id,AdaptationEvent.skill_id==gap.skill_id,AdaptationEvent.is_resolved.is_(False)))).scalars())
        for event in events:event.is_resolved=True;event.resolved_at=gap.resolved_at;event.resolution_mastery_score=current_mastery
        roadmap=await self._roadmap(str(gap.user_id))
        if roadmap: await self.resume_paused_phase(roadmap,gap)
        return True
    async def resume_paused_phase(self,roadmap:Roadmap,gap:KnowledgeGap)->RoadmapPhase|None:
        intervention=next((p for p in roadmap.phases if p.phase_metadata and p.phase_metadata.get("gap_id")==str(gap.id)),None)
        if intervention: intervention.status="completed"; intervention.completed_at=datetime.now(timezone.utc)
        paused=next((p for p in roadmap.phases if p.status=="paused"),None)
        if paused: paused.status="active"; paused.started_at=paused.started_at or datetime.now(timezone.utc); roadmap.current_phase_index=paused.order_index
        return paused
