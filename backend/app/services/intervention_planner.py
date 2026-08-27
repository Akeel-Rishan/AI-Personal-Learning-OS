"""Personalized, timeout-bounded intervention plans and tutor hand-offs."""
from __future__ import annotations
import asyncio, json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.adaptive import KnowledgeGap
from app.models.conversation import TutorConversation, TutorMessage
from app.models.skill import Skill
from app.services.ai_service import AIService

class InterventionPlanner:
    def __init__(self,db:AsyncSession): self.db=db; self.ai=AIService()
    async def plan_intervention(self,gap:KnowledgeGap,skill:Skill,user_context:dict[str,object])->dict[str,object]:
        first=str(user_context.get("user_name","Learner")); fallback={"learner_message":f"{first}, I noticed a gap in {skill.name}. We added a focused review to help you recover quickly.","gap_explanation":gap.misconception or gap.description,"learning_objectives":[f"Explain the core ideas in {skill.name}","Apply the concept in guided practice","Verify understanding independently"],"study_approach":"Start with a short explanation, then move from guided to independent practice.","estimated_fix_time":"About 45 minutes across 1-2 sessions","encouragement":"This is a normal, fixable part of learning."}
        schema={"type":"object","properties":{key:{"type":"array","items":{"type":"string"}} if key=="learning_objectives" else {"type":"string"} for key in fallback},"required":list(fallback),"additionalProperties":False}
        try:
            return await asyncio.wait_for(self.ai.generate_structured(instructions="Design a concise, encouraging adaptive learning intervention. Return JSON only.",prompt=f"Learner context: {json.dumps(user_context,default=str)}\nSkill: {skill.name}\nGap: {gap.description}\nMisconception: {gap.misconception}",schema_name="adaptive_intervention",schema=schema,max_output_tokens=1000),timeout=15)
        except Exception:return fallback
    @staticmethod
    async def should_notify_user(gap_severity:str,adaptation_type:str)->bool: return gap_severity in {"critical","high","medium"} or adaptation_type=="paused_phase"
    async def generate_tutor_conversation_for_gap(self,user_id:str,gap:KnowledgeGap,skill:Skill,intervention_plan:dict[str,object])->str:
        conversation=TutorConversation(user_id=gap.user_id,skill_id=gap.skill_id,title=f"Fixing gap: {skill.name}",message_count=1); self.db.add(conversation); await self.db.flush()
        content=f"{intervention_plan['gap_explanation']}\n\n{intervention_plan['study_approach']}\n\nWould you like to go through this together, or try the exercises first?"
        self.db.add(TutorMessage(conversation_id=conversation.id,role="assistant",content=content,message_metadata={"source":"adaptive_engine","gap_id":str(gap.id)})); return str(conversation.id)
