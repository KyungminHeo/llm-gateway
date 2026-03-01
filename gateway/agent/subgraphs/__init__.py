"""
서브그래프 패키지

전문 에이전트 서브그래프를 관리합니다:
- search_subgraph: 검색 전문 (query_refiner → web_search → result_synthesizer)
- analysis_subgraph: 분석 전문 (decomposer → researcher → synthesizer)
"""
from agent.subgraphs.search_subgraph import create_search_subgraph
from agent.subgraphs.analysis_subgraph import create_analysis_subgraph

__all__ = ["create_search_subgraph", "create_analysis_subgraph"]
