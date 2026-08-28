"""Authenticated project library, workspace, mentor, and submission routes."""
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.conversation import TutorConversation
from app.models.user import User
from app.schemas.project import FinalSubmitRequest,HintResponse,MentorMessageRequest,MentorMessageResponse,ProjectCompletionResponse,ProjectLibraryItem,ProjectResponse,StageEvaluationResponse,StageSubmitRequest,UserProjectResponse,WorkSaveRequest,WorkSaveResponse
from app.schemas.tutor import MessageResponse
from app.services.project_service import ProjectService

router=APIRouter()

@router.get("/",response_model=list[ProjectLibraryItem])
async def library(current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)],category:str|None=None,difficulty:Annotated[int|None,Query(ge=1,le=5)]=None,status:str|None=None)->list[ProjectLibraryItem]:return await ProjectService(db).get_project_library(str(current_user.id),category,difficulty,status)
@router.get("/recommended",response_model=list[ProjectLibraryItem])
async def recommended(current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->list[ProjectLibraryItem]:return await ProjectService(db).get_recommended_projects(str(current_user.id))
@router.get("/my-projects",response_model=list[UserProjectResponse])
async def my_projects(current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)],status:str|None=None)->list[UserProjectResponse]:return [ProjectService.serialize_user_project(item) for item in await ProjectService(db).get_user_projects(str(current_user.id),status)]
@router.get("/workspace/{user_project_id}",response_model=UserProjectResponse)
async def workspace(user_project_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->UserProjectResponse:
    item=await ProjectService(db).get_user_project(user_project_id,str(current_user.id))
    if not item:raise HTTPException(404,"Project workspace not found")
    return ProjectService.serialize_user_project(item)
@router.patch("/workspace/{user_project_id}/save-work",response_model=WorkSaveResponse)
async def save_work(user_project_id:str,payload:WorkSaveRequest,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->WorkSaveResponse:return WorkSaveResponse(saved=True,saved_at=await ProjectService(db).save_work(user_project_id,str(current_user.id),payload.stage_id,payload.code,payload.notes))
@router.post("/workspace/{user_project_id}/stages/{stage_id}/submit",response_model=StageEvaluationResponse)
async def submit_stage(user_project_id:str,stage_id:str,payload:StageSubmitRequest,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->StageEvaluationResponse:return StageEvaluationResponse(**await ProjectService(db).submit_stage(user_project_id,stage_id,str(current_user.id),payload.submitted_code,payload.submitted_notes))
@router.get("/workspace/{user_project_id}/stages/{stage_id}/hint",response_model=HintResponse)
async def hint(user_project_id:str,stage_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)],hint_index:Annotated[int,Query(ge=0)]=0)->HintResponse:return HintResponse(**await ProjectService(db).mentor.get_stage_hint(user_project_id,stage_id,str(current_user.id),hint_index))
@router.post("/workspace/{user_project_id}/mentor/message",response_model=MentorMessageResponse)
async def mentor_message(user_project_id:str,payload:MentorMessageRequest,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->MentorMessageResponse:return MentorMessageResponse(**await ProjectService(db).mentor.send_mentor_message(user_project_id,payload.stage_id,str(current_user.id),payload.message))
@router.get("/workspace/{user_project_id}/mentor/history/{stage_id}",response_model=list[MessageResponse])
async def mentor_history(user_project_id:str,stage_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->list[MessageResponse]:
    up=await ProjectService(db).get_user_project(user_project_id,str(current_user.id));progress=next((item for item in up.stage_progress if str(item.stage_id)==stage_id),None) if up else None
    if not progress or not progress.mentor_conversation_id:return []
    conversation=(await db.execute(select(TutorConversation).options(selectinload(TutorConversation.messages)).where(TutorConversation.id==progress.mentor_conversation_id,TutorConversation.user_id==current_user.id))).scalars().unique().one_or_none()
    return [MessageResponse(id=str(item.id),role=item.role,content=item.content,metadata=item.message_metadata,created_at=item.created_at) for item in (conversation.messages if conversation else [])]
@router.post("/workspace/{user_project_id}/submit-final",response_model=ProjectCompletionResponse)
async def submit_final(user_project_id:str,payload:FinalSubmitRequest,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->ProjectCompletionResponse:return ProjectCompletionResponse(**await ProjectService(db).submit_final_project(user_project_id,str(current_user.id),payload.project_description,payload.final_code,payload.reflection,payload.challenges_faced,payload.github_url))
@router.get("/{project_id}/eligibility")
async def eligibility(project_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->dict[str,object]:
    project=await ProjectService(db).get_project(project_id)
    if not project:raise HTTPException(404,"Project not found")
    return await ProjectService(db).check_eligibility(str(current_user.id),project)
@router.post("/{project_id}/start",response_model=UserProjectResponse)
async def start(project_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->UserProjectResponse:return ProjectService.serialize_user_project(await ProjectService(db).start_project(str(current_user.id),project_id))
@router.get("/{project_id}",response_model=ProjectResponse)
async def detail(project_id:str,current_user:Annotated[User,Depends(get_current_active_user)],db:Annotated[AsyncSession,Depends(get_db)])->ProjectResponse:
    item=await ProjectService(db).get_project(project_id)
    if not item:raise HTTPException(404,"Project not found")
    return ProjectService.serialize_project(item)
