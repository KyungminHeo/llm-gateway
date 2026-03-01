"""
LLM 기반 Intent Classifier 노드

기존: 단어 수(word_count)로 복잡도 판단 → 항상 동일 모델
변경: LLM Structured Output으로 의도를 4가지(search/analysis/creative/general)로 분류
      → 의도에 따라 적절한 모델과 복잡도를 자동 결정
"""
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.nodes.intent_schema import (
    IntentClassification,
    INTENT_MODEL_MAP,
    INTENT_COMPLEXITY_MAP,
)
from core.config import settings

# 분류기 전용 시스템 프롬프트 — 경량 모델이 빠르게 분류할 수 있도록 간결하게
CLASSIFIER_SYSTEM_PROMPT = """당신은 사용자 질문의 의도를 분류하는 분류기입니다.
반드시 아래 JSON 형식으로만 답변하세요. 다른 텍스트를 포함하지 마세요.

분류 기준:
- "search": 최신 뉴스, 실시간 정보, 날씨, 특정 사실 조회 (웹 검색 필요)
- "analysis": 비교, 분석, 장단점, 추론, 복잡한 설명 요청
- "creative": 글쓰기, 번역, 시, 코드 생성, 이메일 작성
- "general": 인사, 간단한 지식 질문, 잡담

응답 형식 (JSON만):
{"intent": "분류값", "confidence": 0.0~1.0, "reasoning": "근거"}"""


async def classifier_node(state: AgentState) -> dict:
    """
    LLM 기반 Intent Classifier
    
    흐름:
    1. 경량 모델(llama3.2:3b)로 빠르게 의도 분류
    2. JSON 파싱 → IntentClassification 검증
    3. 확신도 < 0.7이면 general로 폴백
    4. 의도 → 모델/복잡도 매핑 결과를 state에 기록
    """
    query = state["query"]
    
    try:
        # 경량 모델로 빠르게 분류 — 응답 시간 최소화
        classifier_llm = ChatOllama(
            model=settings.model_simple,  # llama3.2:3b
            base_url=settings.ollama_url,
            temperature=0.0,  # 결정론적 분류
        )
        
        messages = [
            SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
            HumanMessage(content=f"다음 질문을 분류하세요: {query}"),
        ]
        
        response = await classifier_llm.ainvoke(messages)
        raw_text = response.content.strip()
        
        # JSON 파싱 시도 — LLM이 ```json 블록으로 감쌀 수 있으므로 정리
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        
        parsed = json.loads(raw_text)
        classification = IntentClassification(**parsed)
        
        # 확신도가 낮으면 general로 폴백
        intent = classification.intent
        confidence = classification.confidence
        if confidence < 0.7:
            intent = "general"
        
    except (json.JSONDecodeError, Exception):
        # 파싱 실패 시 안전하게 general로 폴백
        intent = "general"
        confidence = 0.0
        classification = None
    
    # 의도 → 모델/복잡도 매핑
    model = INTENT_MODEL_MAP.get(intent, settings.model_complex)
    complexity = INTENT_COMPLEXITY_MAP.get(intent, "simple")
    
    return {
        "intent": intent,
        "confidence": confidence,
        "complexity": complexity,
        "model": model,
    }