"""
Output Guard 노드 — 출력 품질 검증

LLM 응답이 사용자에게 전달되기 전에 품질을 검증합니다.
빈 응답, 너무 짧은 응답, 검색 의도인데 정보가 없는 경우 등을 감지하여
재시도하거나 Fallback으로 분기합니다.
"""
from agent.state import AgentState

# 재시도 최대 횟수
MAX_RETRY_COUNT = 2

# 응답 최소 길이 (문자 수)
MIN_RESPONSE_LENGTH = 5

# 품질 문제 패턴 — 응답이 이런 내용만 있으면 재시도
LOW_QUALITY_INDICATORS = [
    "죄송합니다",
    "알 수 없습니다",
    "정보가 없습니다",
    "답변할 수 없습니다",
    "I don't know",
    "I cannot",
    "I'm sorry",
]


async def output_guard_node(state: AgentState) -> dict:
    """
    출력 품질 검증 노드
    
    검증 로직:
    1. 응답이 비어있거나 너무 짧은지 체크
    2. 검색 의도(search)인데 유용한 정보가 없는 경우 체크
    3. 재시도 횟수가 MAX_RETRY_COUNT 이상이면 Fallback으로 분기
    
    Returns:
        output_quality: "pass" | "retry" | "fallback"
    """
    response = state.get("response", "")
    intent = state.get("intent", "general")
    retry_count = state.get("retry_count", 0)
    
    # 재시도 횟수 초과 → Fallback
    if retry_count >= MAX_RETRY_COUNT:
        return {
            "output_quality": "fallback",
            "retry_count": retry_count,
        }
    
    # 빈 응답 또는 너무 짧은 응답
    if not response or len(response.strip()) < MIN_RESPONSE_LENGTH:
        return {
            "output_quality": "retry",
            "retry_count": retry_count + 1,
        }
    
    # 검색 의도인데 실질 정보가 없는 경우
    if intent == "search":
        response_lower = response.lower()
        # 응답이 온통 "알 수 없다" 류의 내용뿐인지 체크
        is_low_quality = any(
            indicator in response_lower
            for indicator in LOW_QUALITY_INDICATORS
        )
        # 응답이 짧으면서 저품질 패턴에 해당하면 재시도
        if is_low_quality and len(response.strip()) < 100:
            return {
                "output_quality": "retry",
                "retry_count": retry_count + 1,
            }
    
    # 검증 통과
    return {
        "output_quality": "pass",
        "retry_count": retry_count,
    }
