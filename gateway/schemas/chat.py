from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    query: str                                     # 이번 질문
    messages: List[Dict[str, Any]] = []            # 과거 대화 기록
    conversation_id: Optional[str] = None          # 기존 대화에 이어서 할 때

class ChatResponse(BaseModel):
    query: str
    intent: str                                    # 의도 분류 결과 (search/analysis/creative/general)
    complexity: str
    model: str
    response: str
    conversation_id: str
    confidence: Optional[float] = None             # 분류 확신도
    is_blocked: bool = False                       # 차단 여부