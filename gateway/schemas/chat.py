from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    query: str                                     # 이번 질문
    messages: List[Dict[str, Any]] = []            # 과거 대화 기록
    conversation_id: Optional[str] = None          # 기존 대화에 이어서 할 때

class ChatResponse(BaseModel):
    query: str
    complexity: str
    model: str
    response: str
    conversation_id: str                           