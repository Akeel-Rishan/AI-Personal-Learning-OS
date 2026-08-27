"""Re-export every ORM model so metadata discovery is deterministic."""

from app.models.assessment import Assessment, AssessmentAttempt, AssessmentQuestion
from app.models.adaptive import AdaptationEvent, KnowledgeGap
from app.models.conversation import TutorConversation, TutorMessage
from app.models.exercise import Exercise, ExerciseAttempt
from app.models.gamification import Achievement, UserAchievement, XPEvent
from app.models.goal import Goal, GoalSkill
from app.models.learning import DailyPlan, DailyPlanItem, LearningSession
from app.models.progress import SkillHistory, UserSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapPhase
from app.models.skill import Skill, SkillPrerequisite
from app.models.user import User, UserProfile

__all__ = [
    "Achievement",
    "AdaptationEvent",
    "Assessment",
    "AssessmentAttempt",
    "AssessmentQuestion",
    "DailyPlan",
    "DailyPlanItem",
    "Exercise",
    "ExerciseAttempt",
    "Goal",
    "GoalSkill",
    "LearningSession",
    "KnowledgeGap",
    "Roadmap",
    "RoadmapItem",
    "RoadmapPhase",
    "Skill",
    "SkillHistory",
    "SkillPrerequisite",
    "TutorConversation",
    "TutorMessage",
    "User",
    "UserAchievement",
    "UserProfile",
    "UserSkill",
    "XPEvent",
]
