from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from agent.state import AgentState
from agent.nodes.classifier import classifier_node
from agent.nodes.llm_node import llm_node
from agent.tool import search_web

def create_graph():
    graph = StateGraph(AgentState)
    
    # 1. 노드 등록
    graph.add_node("classifier", classifier_node)
    graph.add_node("llm_node", llm_node)
    graph.add_node("tools", ToolNode([search_web]))
    
    # 2. 엣지 연결
    graph.add_edge(START, "classifier")
    graph.add_edge("classifier", "llm_node")
    
    # 3. 조건부 엣지 (핵심!)
    # LLM 응답에 tool_calls가 있으면 → "tools" 노드로
    # tool_calls가 없으면 → END (직접 답변)
    graph.add_conditional_edges("llm_node", tools_condition)
    
    # 4. 도구 실행 후 → 다시 LLM으로 (검색 결과 기반 답변 생성)
    graph.add_edge("tools", "llm_node")
    
    return graph.compile()

# 싱글톤 — 앱 시작 시 한 번만 생성
agent = create_graph()