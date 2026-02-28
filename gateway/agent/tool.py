from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def search_web(query: str) -> str:
    """
    최신 정보, 뉴스, 실시간 데이터를 웹에서 검색할 때 사용하는 도구입니다.
    """
    try:
        # DDGS(DuckDuckGo Search) 객체를 생성하고 검색 결과를 3개까지만 가져옵니다.
        results = DDGS().text(query, max_results=3)

        if not results:
            return "검색 결과가 없습니다."
        
        # 검색 결과 (제목과 요약본)를 하나의 텍스트로 합쳐서 LLM에게 반납 합니다.
        result_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return result_text

    except Exception as e:
        return f"웹 검색 중 오류가 발생했습니다: {str(e)}"