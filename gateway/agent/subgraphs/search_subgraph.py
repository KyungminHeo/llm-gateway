"""
검색 전문 에이전트 서브그래프

단순 검색이 아닌 3단계 검색 파이프라인:
1. query_refiner: 검색어를 최적화
2. web_search: 최적화된 검색어로 검색 수행
3. result_synthesizer: 검색 결과를 종합하여 정리
"""
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.tool import search_web
from core.config import settings


async def query_refiner_node(state: AgentState) -> dict:
    """사용자의 자연어 질문을 검색에 최적화된 키워드로 변환"""
    query = state["query"]
    
    try:
        llm = ChatOllama(
            model=settings.model_simple,
            base_url=settings.ollama_url,
            temperature=0.0,
        )
        
        messages = [
            SystemMessage(content=(
                "당신은 검색어 최적화 전문가입니다. "
                "사용자의 자연어 질문을 웹 검색에 최적화된 핵심 키워드로 변환하세요.\n"
                "규칙:\n"
                "1. 핵심 키워드만 추출 (5~10단어)\n"
                "2. 최신 정보가 필요하면 연도 포함\n"
                "3. 검색 키워드만 출력하세요, 다른 설명 없이\n"
                "4. 반드시 한국어로 출력"
            )),
            HumanMessage(content=query),
        ]
        
        response = await llm.ainvoke(messages)
        refined_query = response.content.strip()
        
        if not refined_query or len(refined_query) < 2:
            refined_query = query
            
    except Exception:
        refined_query = query
    
    return {
        "sub_queries": [refined_query],
    }


async def web_search_node(state: AgentState) -> dict:
    """최적화 검색어 + 원본 질문으로 이중 검색"""
    sub_queries = state.get("sub_queries", [state["query"]])
    original_query = state["query"]
    
    all_results = []
    
    for sq in sub_queries:
        result = search_web.invoke({"query": sq})
        if result and "검색 결과가 없습니다" not in result:
            all_results.append(f"[검색어: {sq}]\n{result}")
    
    if sub_queries and sub_queries[0] != original_query:
        result = search_web.invoke({"query": original_query})
        if result and "검색 결과가 없습니다" not in result:
            all_results.append(f"[원본 검색: {original_query}]\n{result}")
    
    search_results = all_results if all_results else ["검색 결과를 찾지 못했습니다."]
    
    return {
        "search_results": search_results,
    }


async def result_synthesizer_node(state: AgentState) -> dict:
    """수집된 검색 결과를 LLM으로 종합 정리"""
    query = state["query"]
    search_results = state.get("search_results", [])
    
    llm = ChatOllama(
        model=state["model"],
        base_url=settings.ollama_url,
    )
    
    context = "\n\n".join(search_results)
    
    messages = [
        SystemMessage(content=(
            "당신은 검색 결과를 종합 분석하는 전문 에이전트입니다.\n"
            "반드시 한국어로만 답변하세요.\n\n"
            "규칙:\n"
            "1. 아래 검색 결과를 기반으로 사용자 질문에 정확히 답변하세요\n"
            "2. 출처가 다른 정보를 교차 검증하여 정확도를 높이세요\n"
            "3. 정보가 부족하면 솔직히 말하되, 있는 정보는 최대한 활용하세요\n"
            "4. 구조화된 답변을 제공하세요 (핵심 요약 → 상세 설명)"
        )),
        HumanMessage(content=(
            f"사용자 질문: {query}\n\n"
            f"검색 결과:\n{context}"
        )),
    ]
    
    response = await llm.ainvoke(messages)
    
    return {
        "messages": [response],
        "response": response.content if isinstance(response.content, str) else "",
        "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
        "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
    }


def create_search_subgraph():
    """검색 전문 서브그래프 생성"""
    graph = StateGraph(AgentState)
    
    graph.add_node("query_refiner", query_refiner_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("result_synthesizer", result_synthesizer_node)
    
    graph.add_edge(START, "query_refiner")
    graph.add_edge("query_refiner", "web_search")
    graph.add_edge("web_search", "result_synthesizer")
    graph.add_edge("result_synthesizer", END)
    
    return graph.compile()
