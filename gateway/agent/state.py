"""
Agent State — LangGraph 상태 정의

Before: 6개 필드 (messages, query, complexity, model, response, tokens)
After:  13개 필드 — 의도 분류, 보안, 재시도, 서브그래프 지원 필드 추가
"""
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # ─── 메시지 관리 ───
    # LangGraph 전용: 기존 리스트에 새 메시지를 누적(append 또는 update)
    messages: Annotated[list, add_messages]

    # ─── 사용자 입력 ───
    query: str                   # 사용자 원본 질문

    # ─── Intent Classifier 출력 ───
    intent: Literal["search", "analysis", "creative", "general"]  # 의도 분류 결과
    confidence: float            # 분류 확신도 (0.0 ~ 1.0)
    complexity: Literal["simple", "complex"]   # 복잡도 (의도에서 파생)
    model: str                   # 사용할 LLM 모델명

    # ─── Guard Rail ───
    is_blocked: bool             # Input Guard 차단 여부
    block_reason: str            # 차단 사유

    # ─── Output Quality & Retry ───
    output_quality: Literal["pass", "retry", "fallback"]  # Output Guard 판정
    retry_count: int             # 재시도 횟수

    # ─── 서브그래프 공유 데이터 ───
    sub_queries: list[str]       # 분해된 하위 질문들
    search_results: list[str]    # 검색/조사 결과 리스트

    # ─── LLM 응답 ───
    response: str                # LLM 최종 응답
    prompt_tokens: int           # 입력 토큰 수
    completion_tokens: int       # 출력 토큰 수