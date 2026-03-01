"""
LLM 호출 노드 — Tool Calling 방식

creative_agent와 general_agent 모두 이 노드를 공유합니다.
그래프에서 bind_tools 여부는 state의 intent에 따라 결정됩니다.
"""
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from agent.state import AgentState
from agent.tool import ALL_TOOLS
from core.config import settings

# 시스템 프롬프트: 의도별로 약간의 행동 차이를 가짐
SYSTEM_PROMPTS = {
    "creative": """당신은 창의적 글쓰기, 코드 생성, 번역 등을 수행하는 AI 어시스턴트입니다.
반드시 한국어로만 답변하세요. 절대 중국어나 영어를 섞지 마세요.

규칙:
1. 사용자가 요청한 형식(시, 이메일, 코드 등)에 맞게 창작하세요
2. 필요한 경우 웹 검색이나 계산 도구를 활용할 수 있습니다
3. 창의적이면서도 정확한 결과물을 제공하세요
4. 사용자의 톤과 스타일 요청을 존중하세요""",

    "general": """당신은 친절한 AI 어시스턴트입니다.
반드시 한국어로만 답변하세요. 절대 중국어나 영어를 섞지 마세요.

규칙:
1. 간결하고 정확하게 답변하세요
2. 일반 지식 질문에는 직접 답변하세요
3. 필요한 경우 도구를 활용할 수 있습니다
4. 모르는 것은 솔직히 모른다고 말하세요""",
}

# 기본 시스템 프롬프트 (fallback)
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPTS["general"]


async def llm_node(state: AgentState) -> dict:
    """
    LLM 호출 노드 — Tool Calling 방식
    
    흐름:
    1. 의도(intent)에 맞는 시스템 프롬프트 선택
    2. bind_tools로 전체 도구를 LLM에 장착
    3. LLM이 도구 호출 여부를 자율 판단
    4. tool_calls가 있으면 → graph의 ToolNode로 분기됨
    5. tool_calls가 없으면 → output_guard로 이동
    """
    intent = state.get("intent", "general")
    
    # 1. Ollama 객체 생성
    llm = ChatOllama(
        model=state["model"],
        base_url=settings.ollama_url,
    )
    
    # 2. LLM에게 모든 도구를 장착 (bind)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # 3. 의도에 맞는 시스템 프롬프트 주입
    system_prompt = SYSTEM_PROMPTS.get(intent, DEFAULT_SYSTEM_PROMPT)
    messages = state["messages"]
    if not any(hasattr(m, "type") and m.type == "system" for m in messages):
        messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    # 4. LLM 호출
    response = await llm_with_tools.ainvoke(messages)
    
    # 5. 상태 업데이트
    return {
        "messages": [response],
        "response": response.content if isinstance(response.content, str) else "",
        "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
        "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
    }