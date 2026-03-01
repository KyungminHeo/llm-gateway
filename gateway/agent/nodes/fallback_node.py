"""
Fallback 응답 노드

재시도 횟수 초과 시 안전한 기본 응답을 생성합니다.
사용자에게 친화적인 메시지와 함께 문제 상황을 안내합니다.
"""
from agent.state import AgentState


async def fallback_node(state: AgentState) -> dict:
    """
    Fallback 응답 생성
    
    트리거 조건:
    - output_guard에서 retry_count >= MAX_RETRY_COUNT
    
    동작:
    - 의도(intent)에 맞는 안내 메시지 반환
    - 에러가 아닌 '도움 안내' 톤으로 작성
    """
    intent = state.get("intent", "general")
    query = state["query"]
    
    fallback_messages = {
        "search": (
            f"죄송합니다. '{query[:50]}...'에 대한 검색 결과를 "
            "충분히 수집하지 못했습니다.\n\n"
            "다음을 시도해보세요:\n"
            "- 질문을 더 구체적으로 바꿔보세요\n"
            "- 다른 키워드로 다시 질문해보세요\n"
            "- 시간을 두고 다시 시도해주세요 (일시적 검색 오류일 수 있음)"
        ),
        "analysis": (
            f"'{query[:50]}...'에 대한 분석을 완료하지 못했습니다.\n\n"
            "질문이 매우 복잡하거나 범위가 넓을 수 있습니다.\n"
            "다음을 시도해보세요:\n"
            "- 질문의 범위를 좁혀보세요\n"
            "- 비교 대상을 명확히 지정해보세요\n"
            "- 한 번에 하나의 주제에 집중해보세요"
        ),
        "creative": (
            f"'{query[:50]}...'에 대한 창작 결과를 생성하지 못했습니다.\n\n"
            "다음을 시도해보세요:\n"
            "- 원하는 형식이나 스타일을 구체적으로 알려주세요\n"
            "- 예시를 함께 제공해보세요\n"
            "- 요청을 더 짧게 나눠서 시도해보세요"
        ),
        "general": (
            "죄송합니다. 현재 요청을 처리하는 데 어려움이 있습니다.\n\n"
            "잠시 후 다시 시도해주세요. "
            "문제가 지속되면 질문을 다르게 표현해보시는 것도 도움이 됩니다."
        ),
    }
    
    response = fallback_messages.get(intent, fallback_messages["general"])
    
    return {
        "response": response,
    }
