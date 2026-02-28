from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import get_current_active_user
from core.database import get_db
from models.users import User
from schemas.conversation import ConversationCreate, ConversationSummary, ConversationDetail
from service import conversation_service

router = APIRouter()

@router.post("/", response_model=ConversationSummary, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """새 대화 세션 생성"""
    title = data.title or "새 대화"
    conversation = await conversation_service.create_conversation(db, current_user.id, title)
    return conversation


@router.get("/", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """내 대화 목록 조회 (최신순)"""
    return await conversation_service.get_conversations(db, current_user.id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """대화 상세 조회 (메시지 전체 포함)"""
    return await conversation_service.get_conversation_detail(db, conversation_id, current_user.id)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """대화 삭제"""
    return await conversation_service.delete_conversation(db, conversation_id, current_user.id)