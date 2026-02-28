from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.conversation import Conversation, Message


async def create(db: AsyncSession, conversation: Conversation) -> Conversation:
    """대화 세션 저장"""
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def add_message(db: AsyncSession, message: Message) -> Message:
    """메시지 한 건 저장"""
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def find_by_user_id(db: AsyncSession, user_id: str) -> list[Conversation]:
    """유저의 대화 목록 조회 (최신순)"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def find_by_id_and_user(db: AsyncSession, conversation_id: str, user_id: str) -> Conversation | None:
    """대화 상세 조회 (메시지 포함, 본인 것만)"""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete(db: AsyncSession, conversation: Conversation) -> None:
    """대화 삭제"""
    await db.delete(conversation)
    await db.commit()
