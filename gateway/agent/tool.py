from langchain_core.tools import tool
from duckduckgo_search import DDGS


@tool
def search_web(query: str) -> str:
    """최신 뉴스, 실시간 정보, 2024년 이후 사건을 검색합니다."""
    try:
        ddgs = DDGS()
        
        # 1차: 뉴스 검색 (최신 시사/정치 정보에 강함)
        news = ddgs.news(query, region="kr-kr", max_results=3)
        
        # 2차: 일반 텍스트 검색 (배경 지식 보충)
        text = ddgs.text(query, region="kr-kr", max_results=3)

        results = []

        if news:
            results.append("[뉴스 검색 결과]")
            for r in news:
                results.append(f"- {r['title']}: {r['body']}")

        if text:
            results.append("[웹 검색 결과]")
            for r in text:
                results.append(f"- {r['title']}: {r['body']}")

        if not results:
            return "검색 결과가 없습니다."

        return "\n".join(results)

    except Exception as e:
        return f"웹 검색 중 오류가 발생했습니다: {str(e)}"
