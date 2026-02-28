from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageResponse(BaseModel):
    """개별 메시지 응답"""
    id: str
    role: str           # "user" 또는 "assistant"
    content: str
    created_at: datetime


class ConversationCreate(BaseModel):
    """대화 생성 요청 — 첫 질문이 제목"""
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    """대화 목록용 (메시지 내용 제외, 가볍게)"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """대화 상세 조회 (메시지 전체 포함)"""
    id: str
    title: str
    created_at: datetime
    messages: List[MessageResponse]
