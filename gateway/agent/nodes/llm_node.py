from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from agent.state import AgentState
from agent.tool import search_web
from core.config import settings

# 시스템 프롬프트: LLM에게 "도구를 적극 활용하라"고 명확히 지시
SYSTEM_PROMPT = """당신은 웹 검색 도구를 활용할 수 있는 AI 어시스턴트입니다.
반드시 한국어로만 답변하세요. 절대 중국어나 영어를 섞지 마세요.

규칙:
1. 최신 정보, 뉴스, 날씨, 실시간 데이터, 현재 상황 등을 묻는 질문에는 반드시 search_web 도구를 호출하세요.
2. 당신의 학습 데이터에 없을 수 있는 정보(2024년 이후 사건 등)는 반드시 검색하세요.
3. 일반 지식 질문(수학, 프로그래밍, 역사적 사실 등)은 도구 없이 직접 답변하세요.
4. 검색 결과를 받으면, 그 내용을 기반으로 정확하게 한국어로 답변하세요.
"""

async def llm_node(state: AgentState) -> dict:
    """
    LLM 호출 노드 — Tool Calling 방식
    
    흐름:
    1. 시스템 프롬프트로 "도구 활용 지시"를 주입
    2. bind_tools로 검색 도구를 LLM에 장착
    3. LLM이 스스로 판단하여 도구 호출 여부 결정
    4. tool_calls가 있으면 → graph의 ToolNode로 분기됨
    5. tool_calls가 없으면 → 바로 END로 종료
    """
    
    # 1. Ollama 객체 생성
    llm = ChatOllama(
        model=state["model"],
        base_url=settings.ollama_url,
    )
    
    # 2. LLM에게 검색 도구를 장착 (bind)
    llm_with_tools = llm.bind_tools([search_web])
    
    # 3. 시스템 프롬프트를 messages 맨 앞에 주입
    messages = state["messages"]
    if not any(hasattr(m, "type") and m.type == "system" for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    
    # 4. LLM 호출 — 도구를 쓸지 말지는 LLM이 판단
    response = await llm_with_tools.ainvoke(messages)
    
    # 5. 상태 업데이트
    return {
        "messages": [response],
        "response": response.content if isinstance(response.content, str) else "",
        "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
        "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
    }