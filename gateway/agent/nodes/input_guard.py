"""
Input Guard 노드 — 입력 안전성 검증

유해 입력, 프롬프트 인젝션, 과도한 길이 등을 사전 차단하여
LLM에 도달하기 전에 불필요한 요청을 걸러냅니다.
"""
import re
from agent.state import AgentState

# 입력 최대 길이 (문자 수)
MAX_INPUT_LENGTH = 4000

# 프롬프트 인젝션 패턴 — 대표적 공격 패턴들
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
    r"(you\s+are|act\s+as|pretend\s+to\s+be)\s+(now\s+)?a?\s*(evil|malicious|hacker|jailbreak)",
    r"system\s*prompt\s*[:=]",
    r"<\|?(system|im_start|im_end)\|?>",
    r"DAN\s*(mode)?",
    r"(do\s+)?anything\s+now",
    r"(override|bypass|disable)\s+(safety|filter|guard|restriction|rule)",
    r"이전\s*(지시|명령|규칙).*?(무시|잊어|삭제)",
    r"(시스템|관리자)\s*프롬프트",
    r"(안전|필터|보안).*?(해제|무시|우회|비활성)",
]

# 유해 키워드 패턴 (한국어 + 영어)
HARMFUL_PATTERNS = [
    r"(how\s+to\s+)?(make|create|build)\s+(a\s+)?(bomb|weapon|explosive|virus|malware)",
    r"(폭탄|무기|폭발물|바이러스|악성코드)\s*(제조|만들|생성)",
]


async def input_guard_node(state: AgentState) -> dict:
    """
    입력 안전성 검증 노드
    
    검증 순서:
    1. 빈 입력 체크
    2. 길이 제한 체크
    3. 프롬프트 인젝션 패턴 탐지
    4. 유해 콘텐츠 패턴 탐지
    
    차단 시: is_blocked=True, block_reason에 사유 기록
    통과 시: is_blocked=False
    """
    query = state["query"].strip()
    
    # 1. 빈 입력
    if not query:
        return {
            "is_blocked": True,
            "block_reason": "빈 질문은 처리할 수 없습니다.",
        }
    
    # 2. 길이 제한
    if len(query) > MAX_INPUT_LENGTH:
        return {
            "is_blocked": True,
            "block_reason": f"질문이 너무 깁니다 (최대 {MAX_INPUT_LENGTH}자). 질문을 줄여주세요.",
        }
    
    # 3. 프롬프트 인젝션 탐지
    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return {
                "is_blocked": True,
                "block_reason": "보안 정책에 의해 차단된 요청입니다.",
            }
    
    # 4. 유해 콘텐츠 탐지
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return {
                "is_blocked": True,
                "block_reason": "안전 정책에 의해 처리할 수 없는 요청입니다.",
            }
    
    # 모든 검증 통과
    return {
        "is_blocked": False,
        "block_reason": "",
    }
