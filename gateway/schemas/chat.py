from pydantic import BaseModel
from typing import List, Dict, Any

class ChatRequest(BaseModel):
    query: str  # 이번에 새로 입력한 질문
    messages: List[Dict[str, Any]] = []  # 과거 대화 기록

class ChatResponse(BaseModel):
    query: str
    complexity: str
    model: str
    response: str