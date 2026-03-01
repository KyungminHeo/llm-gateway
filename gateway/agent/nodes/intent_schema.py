"""
Intent Classification Schema — LLM Structured Output용 Pydantic 모델

LLM이 사용자 의도를 4가지 카테고리로 분류한 결과를 파싱합니다.
"""
from pydantic import BaseModel, Field
from typing import Literal


class IntentClassification(BaseModel):
    """LLM 기반 의도 분류 결과"""
    
    intent: Literal["search", "analysis", "creative", "general"] = Field(
        description=(
            "사용자 질문의 의도를 분류합니다.\n"
            "- search: 최신 뉴스, 실시간 정보, 날씨, 특정 사실 조회 등 '검색'이 필요한 질문\n"
            "- analysis: 비교, 분석, 장단점, 추론, 복잡한 설명 요청 등 '분석적 사고'가 필요한 질문\n"
            "- creative: 글쓰기, 번역, 시, 코드 생성, 이메일 작성 등 '창작/생성'이 필요한 질문\n"
            "- general: 인사, 간단한 지식 질문, 잡담 등 위에 해당하지 않는 일반 질문"
        )
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="분류 확신도 (0.0 ~ 1.0). 0.7 미만이면 general로 폴백"
    )
    reasoning: str = Field(
        description="왜 이 의도로 분류했는지 간단한 근거 (한국어)"
    )


# 의도 → 모델 매핑 설정
INTENT_MODEL_MAP = {
    "search": "qwen2.5:7b",      # Tool calling 필요 → 고성능 모델
    "analysis": "qwen2.5:7b",    # 복잡한 추론 → 고성능 모델
    "creative": "qwen2.5:7b",    # 창작 품질 → 고성능 모델
    "general": "llama3.2:3b",    # 간단 응답 → 경량 모델 (빠른 응답)
}

# 의도 → 복잡도 매핑
INTENT_COMPLEXITY_MAP = {
    "search": "complex",
    "analysis": "complex",
    "creative": "complex",
    "general": "simple",
}
