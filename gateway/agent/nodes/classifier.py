from agent.state import AgentState
from core.config import settings

async def classifier_node(state: AgentState) -> dict:
    """
    복잡도 판단 → 모델 선택
    
    현재 정책:
    - Tool Calling(검색 도구)을 지원하는 모델(qwen2.5:7b)을 기본 사용
    - llama3.2:3b는 경량 모델이라 tool calling 미지원
    - 추후 tool calling 지원 경량 모델이 나오면 분기 로직 복원 가능
    """
    
    query = state["query"]
    word_count = len(query.split())

    if word_count < settings.complexity_threshold:
        complexity = "simple"
    else:
        complexity = "complex"
    
    # Tool Calling 지원을 위해 항상 qwen2.5:7b 사용
    return {
        "complexity": complexity,
        "model": settings.model_complex,  # qwen2.5:7b (tool calling 지원)
    }