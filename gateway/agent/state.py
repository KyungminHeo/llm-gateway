from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # LangGraph 전용 문법: 기존 리스트 내역에 새 메시지들을 누적(append 또는 update)합니다.
    messages: Annotated[list, add_messages]

    # 사용자 입력 (라우터에서 채움)
    query: str
    
    # classifier 노드가 채우는 필드
    complexity: Literal["simple", "complex"]  # 판단 결과
    model: str                                # 사용할 모델명
    
    # llm_node 
    response: str               # LLM 최종 응답
    prompt_tokens: int          # ← 추가: 입력 토큰 수
    completion_tokens: int      # ← 추가: 생성 토큰 수