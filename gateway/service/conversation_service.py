from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from models.conversation import Conversation, Message
from repository import conversation_repo


async def create_conversation(db: AsyncSession, user_id: str, title: str = "새 대화") -> Conversation:
    """새 대화 세션 생성"""
    conversation = Conversation(user_id=user_id, title=title)
    return await conversation_repo.create(db, conversation)


async def add_message(db: AsyncSession, conversation_id: str, role: str, content: str) -> Message:
    """대화에 메시지 추가"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    return await conversation_repo.add_message(db, message)


async def get_conversations(db: AsyncSession, user_id: str) -> list[Conversation]:
    """내 대화 목록 조회"""
    return await conversation_repo.find_by_user_id(db, user_id)


async def get_conversation_detail(db: AsyncSession, conversation_id: str, user_id: str) -> Conversation:
    """대화 상세 조회 (메시지 포함) — 없으면 404"""
    conversation = await conversation_repo.find_by_id_and_user(db, conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다."
        )
    return conversation


async def delete_conversation(db: AsyncSession, conversation_id: str, user_id: str) -> None:
    """대화 삭제 — 없으면 404"""
    conversation = await conversation_repo.find_by_id_and_user(db, conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다."
        )
    await conversation_repo.delete(db, conversation)