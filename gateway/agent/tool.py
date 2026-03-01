"""
Agent Tools — LLM이 호출할 수 있는 도구 모음

기존: search_web 1개
변경: search_web + calculate + summarize_url + get_datetime (4개)
"""
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from datetime import datetime, timezone, timedelta
import re
import math
import httpx


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


@tool
def calculate(expression: str) -> str:
    """수학 계산을 수행합니다. 사칙연산, 거듭제곱, 제곱근, 삼각함수 등을 지원합니다.
    예시: '2 + 3 * 4', 'sqrt(144)', 'sin(3.14)', '2 ** 10'"""
    try:
        # 안전한 수학 환경 — 위험한 내장 함수 차단
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            # math 모듈 함수들
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
            "ceil": math.ceil,
            "floor": math.floor,
            "factorial": math.factorial,
        }
        
        # 위험한 패턴 차단
        blocked = ["import", "exec", "eval", "open", "os.", "sys.", "__", "lambda"]
        expr_lower = expression.lower()
        for b in blocked:
            if b in expr_lower:
                return f"보안상 허용되지 않는 표현입니다: {b}"
        
        result = eval(expression, safe_dict)
        return f"계산 결과: {expression} = {result}"
    
    except ZeroDivisionError:
        return "오류: 0으로 나눌 수 없습니다."
    except Exception as e:
        return f"계산 중 오류가 발생했습니다: {str(e)}"


@tool
def get_datetime(timezone_offset: int = 9) -> str:
    """현재 날짜와 시간을 반환합니다. timezone_offset은 UTC 기준 시차입니다 (한국: 9)."""
    try:
        tz = timezone(timedelta(hours=timezone_offset))
        now = datetime.now(tz)
        
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        weekday = weekdays[now.weekday()]
        
        return (
            f"현재 시간 (UTC{'+' if timezone_offset >= 0 else ''}{timezone_offset})\n"
            f"날짜: {now.strftime('%Y년 %m월 %d일')} {weekday}\n"
            f"시간: {now.strftime('%H시 %M분 %S초')}"
        )
    except Exception as e:
        return f"시간 조회 중 오류: {str(e)}"


@tool
def summarize_url(url: str) -> str:
    """웹 페이지의 텍스트 내용을 가져옵니다. URL을 입력하면 해당 페이지의 주요 텍스트를 추출합니다."""
    try:
        # 동기 HTTP 클라이언트 사용 (tool은 동기 함수)
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; LLMGateway/1.0)"
            })
            response.raise_for_status()
        
        # HTML에서 텍스트만 추출 (간이 방식)
        text = response.text
        
        # script, style 태그 제거
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        
        # 모든 HTML 태그 제거
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 연속 공백/줄바꿈 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 최대 2000자로 제한
        if len(text) > 2000:
            text = text[:2000] + "... (이하 생략)"
        
        if not text:
            return "페이지에서 텍스트를 추출할 수 없습니다."
        
        return f"[{url} 페이지 내용]\n{text}"
    
    except httpx.HTTPStatusError as e:
        return f"페이지 접근 실패 (HTTP {e.response.status_code}): {url}"
    except Exception as e:
        return f"URL 내용 가져오기 실패: {str(e)}"


# 모든 도구를 리스트로 관리 — graph.py에서 import
ALL_TOOLS = [search_web, calculate, get_datetime, summarize_url]
