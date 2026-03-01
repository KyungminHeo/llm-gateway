"""
분석 전문 에이전트 서브그래프

복잡한 분석 질문을 처리하는 3단계 파이프라인:
1. decomposer: 복잡한 질문을 하위 질문들로 분해
2. researcher: 각 하위 질문을 개별 조사
3. synthesizer: 조사 결과를 종합 분석하여 최종 답변 생성
"""
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from core.config import settings
import json


async def decomposer_node(state: AgentState) -> dict:
    """
    질문 분해 노드
    
    복잡한 질문을 2~4개의 하위 질문으로 분해합니다.
    예: "A와 B의 장단점을 비교해줘" 
      → ["A의 장점은?", "A의 단점은?", "B의 장점은?", "B의 단점은?"]
    """
    query = state["query"]
    
    try:
        llm = ChatOllama(
            model=settings.model_simple,
            base_url=settings.ollama_url,
            temperature=0.0,
        )
        
        messages = [
            SystemMessage(content=(
                "당신은 복잡한 질문을 분석 가능한 하위 질문들로 분해하는 전문가입니다.\n"
                "규칙:\n"
                "1. 주어진 질문을 2~4개의 하위 질문으로 분해하세요\n"
                "2. 각 하위 질문은 독립적으로 답변 가능해야 합니다\n"
                "3. JSON 배열 형식으로만 출력하세요\n"
                "4. 한국어로 작성하세요\n"
                "5. 단순한 질문이면 원본 질문 하나만 배열에 넣으세요\n\n"
                '출력 형식: ["하위질문1", "하위질문2", ...]'
            )),
            HumanMessage(content=query),
        ]
        
        response = await llm.ainvoke(messages)
        raw_text = response.content.strip()
        
        # JSON 배열 파싱
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        
        sub_queries = json.loads(raw_text)
        
        if not isinstance(sub_queries, list) or len(sub_queries) == 0:
            sub_queries = [query]
            
    except Exception:
        sub_queries = [query]
    
    return {
        "sub_queries": sub_queries,
    }


async def researcher_node(state: AgentState) -> dict:
    """
    개별 조사 노드
    
    각 하위 질문에 대해 LLM으로 답변을 생성합니다.
    (외부 검색 없이 LLM 지식 기반 분석)
    """
    sub_queries = state.get("sub_queries", [state["query"]])
    
    llm = ChatOllama(
        model=state["model"],
        base_url=settings.ollama_url,
    )
    
    research_results = []
    total_prompt = 0
    total_completion = 0
    
    for i, sq in enumerate(sub_queries, 1):
        messages = [
            SystemMessage(content=(
                "당신은 분석 전문가입니다. 주어진 질문에 대해 깊이 있는 분석을 제공하세요.\n"
                "반드시 한국어로 답변하세요.\n"
                "핵심 포인트 위주로 간결하지만 통찰력 있게 답변하세요."
            )),
            HumanMessage(content=sq),
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else ""
        research_results.append(f"[분석 {i}: {sq}]\n{content}")
        
        if response.usage_metadata:
            total_prompt += response.usage_metadata.get("input_tokens", 0)
            total_completion += response.usage_metadata.get("output_tokens", 0)
    
    return {
        "search_results": research_results,  # search_results 필드를 재활용
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
    }


async def synthesizer_node(state: AgentState) -> dict:
    """
    종합 분석 노드
    
    개별 조사 결과를 하나의 구조화된 분석 보고서로 종합합니다.
    """
    query = state["query"]
    research_results = state.get("search_results", [])
    
    llm = ChatOllama(
        model=state["model"],
        base_url=settings.ollama_url,
    )
    
    context = "\n\n".join(research_results)
    
    messages = [
        SystemMessage(content=(
            "당신은 종합 분석 전문가입니다.\n"
            "반드시 한국어로만 답변하세요.\n\n"
            "규칙:\n"
            "1. 아래 개별 분석 결과를 종합하여 하나의 완성된 답변을 작성하세요\n"
            "2. 구조: 핵심 요약 → 상세 분석 → 결론/시사점\n"
            "3. 중복 내용은 통합하고, 서로 다른 관점은 비교 대조하세요\n"
            "4. 논리적이고 읽기 쉬운 구조로 작성하세요"
        )),
        HumanMessage(content=(
            f"원래 질문: {query}\n\n"
            f"개별 분석 결과:\n{context}"
        )),
    ]
    
    response = await llm.ainvoke(messages)
    
    prev_prompt = state.get("prompt_tokens", 0)
    prev_completion = state.get("completion_tokens", 0)
    
    return {
        "messages": [response],
        "response": response.content if isinstance(response.content, str) else "",
        "prompt_tokens": prev_prompt + (response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0),
        "completion_tokens": prev_completion + (response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0),
    }


def create_analysis_subgraph():
    """분석 전문 서브그래프 생성"""
    graph = StateGraph(AgentState)
    
    graph.add_node("decomposer", decomposer_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("synthesizer", synthesizer_node)
    
    graph.add_edge(START, "decomposer")
    graph.add_edge("decomposer", "researcher")
    graph.add_edge("researcher", "synthesizer")
    graph.add_edge("synthesizer", END)
    
    return graph.compile()
