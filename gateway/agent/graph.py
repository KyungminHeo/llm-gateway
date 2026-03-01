"""
LangGraph 메인 그래프 — 고도화 아키텍처

Before: 3노드 직선형 (classifier → llm_node → tools)
After:  10+ 노드, 5+ 조건부 분기, 2개 서브그래프

그래프 흐름:
  START → input_guard ──blocked──→ blocked_response → END
                      └──safe──→ classifier → intent_router
                                              ├── search_agent (서브그래프)
                                              ├── analysis_agent (서브그래프)
                                              ├── creative_agent (llm + tool loop)
                                              └── general_agent (llm 직접 호출)
                                                    ↓
                                              output_guard ──pass──→ END
                                              ├── retry → classifier (재시도)
                                              └── fallback → END
"""
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from agent.nodes.input_guard import input_guard_node
from agent.nodes.classifier import classifier_node
from agent.nodes.llm_node import llm_node
from agent.nodes.output_guard import output_guard_node
from agent.nodes.fallback_node import fallback_node
from agent.tool import ALL_TOOLS
from agent.subgraphs.search_subgraph import create_search_subgraph
from agent.subgraphs.analysis_subgraph import create_analysis_subgraph


# ── 서브그래프 인스턴스 생성 (싱글톤) ──
search_agent = create_search_subgraph()
analysis_agent = create_analysis_subgraph()


# ── Wrapper 노드 (서브그래프 호출용) ──
async def search_agent_node(state: AgentState) -> dict:
    """검색 전문 서브그래프 실행"""
    result = await search_agent.ainvoke(state)
    return {
        "messages": result.get("messages", []),
        "response": result.get("response", ""),
        "search_results": result.get("search_results", []),
        "sub_queries": result.get("sub_queries", []),
        "prompt_tokens": result.get("prompt_tokens", 0),
        "completion_tokens": result.get("completion_tokens", 0)
    }


async def analysis_agent_node(state: AgentState) -> dict:
    """분석 전문 서브그래프 실행"""
    result = await analysis_agent.ainvoke(state)
    return {
        "messages": result.get("messages", []),
        "response": result.get("response", ""),
        "search_results": result.get("search_results", []),
        "sub_queries": result.get("sub_queries", []),
        "prompt_tokens": result.get("prompt_tokens", 0),
        "completion_tokens": result.get("completion_tokens", 0)
    }


async def blocked_response_node(state: AgentState) -> dict:
    """차단된 입력에 대한 응답 생성"""
    return {
        "response": state.get("block_reason", "요청이 차단되었습니다."),
        "model": "none",
        "complexity": "simple",
        "intent": "general",
        "confidence": 0.0
    }


# ── 조건부 라우팅 함수들 ──

def input_guard_router(state: AgentState) -> str:
    """Input Guard 결과에 따른 분기"""
    if state.get("is_blocked", False):
        return "blocked_response"
    return "classifier"


def intent_router(state: AgentState) -> str:
    """의도(Intent)에 따른 에이전트 분기"""
    intent = state.get("intent", "general")
    
    routing_map = {
        "search": "search_agent",
        "analysis": "analysis_agent",
        "creative": "creative_agent",     # Tool 사용 가능한 LLM
        "general": "general_agent"       # Tool 없는 경량 LLM
    }
    
    return routing_map.get(intent, "general_agent")


def output_quality_router(state: AgentState) -> str:
    """Output Guard 결과에 따른 분기"""
    quality = state.get("output_quality", "pass")
    
    if quality == "pass":
        return END
    elif quality == "retry":
        return "classifier"   # 재시도: 다시 분류부터
    else:  # fallback
        return "fallback"


def creative_tools_router(state: AgentState) -> str:
    """Creative Agent의 tool 호출 판단"""
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
    return "output_guard"


# ── 그래프 빌드 ──

def create_graph():
    graph = StateGraph(AgentState)
    
    # ═══ 노드 등록 ═══
    
    # Guard Rails
    graph.add_node("input_guard", input_guard_node)
    graph.add_node("blocked_response", blocked_response_node)
    
    # Classifier > 질의 분류
    graph.add_node("classifier", classifier_node)
    
    # 전문 에이전트들
    graph.add_node("search_agent", search_agent_node)        # 서브그래프
    graph.add_node("analysis_agent", analysis_agent_node)    # 서브그래프

    graph.add_node("creative_agent", llm_node)               # Tool Calling 지원
    graph.add_node("general_agent", llm_node)                # 직접 응답
    graph.add_node("tools", ToolNode(ALL_TOOLS))             # 도구 실행기
    
    # Output 검증
    graph.add_node("output_guard", output_guard_node)
    graph.add_node("fallback", fallback_node)
    
    # ═══ 엣지 연결 ═══
    
    # 1. START → Input Guard
    graph.add_edge(START, "input_guard")
    
    # 2. Input Guard → (차단 / 통과)
    graph.add_conditional_edges("input_guard", input_guard_router, 
        ["blocked_response", "classifier"])
    
    # 3. 차단 → END
    graph.add_edge("blocked_response", END)
    
    # 4. Classifier → Intent Router (4방향 분기)
    graph.add_conditional_edges("classifier", intent_router,
        ["search_agent", "analysis_agent", "creative_agent", "general_agent"])
    
    # 5. 서브그래프/에이전트 → Output Guard
    graph.add_edge("search_agent", "output_guard")
    graph.add_edge("analysis_agent", "output_guard")
    graph.add_edge("general_agent", "output_guard")
    
    # 6. Creative Agent → (Tool 호출 / Output Guard)
    graph.add_conditional_edges("creative_agent", creative_tools_router,
        ["tools", "output_guard"])
    
    # 7. Tool 실행 후 → Creative Agent로 복귀 (결과 반영)
    graph.add_edge("tools", "creative_agent")
    
    # 8. Output Guard → (통과 / 재시도 / Fallback)
    graph.add_conditional_edges("output_guard", output_quality_router,
        ["classifier", "fallback", END])
    
    # 9. Fallback → END
    graph.add_edge("fallback", END)
    
    return graph.compile()


# ── 싱글톤 인스턴스 ──
agent = create_graph()