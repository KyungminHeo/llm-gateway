import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import TimestampMixin
from core.database import Base


class Conversation(TimestampMixin, Base):
    """
    대화 세션 — 하나의 채팅방
    User : Conversation = 1 : N
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 어떤 유저의 대화인지
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 대화 제목 (첫 질문을 자동으로 제목화)
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="새 대화",
    )

    # ORM 관계: conversation.messages로 접근 가능
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(TimestampMixin, Base):
    """
    개별 메시지 — 대화 안의 한 턴
    Conversation : Message = 1 : N
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "user" 또는 "assistant"
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # 메시지 본문
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ORM 역참조
    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )
