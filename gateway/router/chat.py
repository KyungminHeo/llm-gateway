from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import json
from schemas.chat import ChatRequest, ChatResponse
from agent.graph import agent
from core.security import get_current_active_user
from core.database import get_db
from models.users import User
from core.dependencies import get_redis
from service.cache_service import get_cached_response, set_cached_response
from service.quota_service import check_quota
from service.log_service import log_usage
from service import conversation_service

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_active_user), redis: Redis = Depends(get_redis), db: AsyncSession = Depends(get_db)):
    """
    전체 파이프라인:
    1. JWT 인증
    2. 쿼터 확인 (분당 20회)
    3. 캐시 확인 → 히트 시 즉시 반환
    4. 대화 세션 생성/로드
    5. 사용자 메시지 DB 저장
    6. LangGraph Agent 실행 (고도화된 멀티 에이전트 그래프)
    7. AI 응답 DB 저장
    8. 토큰 사용량 로깅 + 캐시 저장
    """

    # 1. 쿼터
    await check_quota(redis, current_user.id)

    # 2. 캐시
    cached = await get_cached_response(redis, request.query)
    if cached:
        return ChatResponse(**cached)

    # 3. 대화 세션 - 없으면 새로 생성, 있으면 기존 것 사용
    if request.conversation_id:
        conversation = await conversation_service.get_conversation_detail(
            db, request.conversation_id, current_user.id
        )
    else:
        # 첫 질문 앞 30글자를 대화 제목으로 사용
        title = request.query[:30]
        conversation = await conversation_service.create_conversation(
            db, current_user.id, title
        )

    # 4. 사용자 메시지 DB 저장
    await conversation_service.add_message(
        db, conversation.id, "user", request.query
    )

    # 5. LangGraph State 초기화 — 고도화된 상태
    input_messages = request.messages + [{"role": "user", "content": request.query}]
    
    initial_state = {
        "messages": input_messages,
        "query": request.query,
        # Intent Classifier가 채울 필드들
        "intent": "general",
        "confidence": 0.0,
        "complexity": "",
        "model": "",
        # Guard Rail
        "is_blocked": False,
        "block_reason": "",
        # Output Quality
        "output_quality": "pass",
        "retry_count": 0,
        # Subgraph 공유
        "sub_queries": [],
        "search_results": [],
        # 응답
        "response": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }

    # 실행
    final_state = await agent.ainvoke(initial_state)

    # 6. AI 응답 DB 저장 (차단된 경우에도 차단 메시지 저장)
    await conversation_service.add_message(
        db, conversation.id, "assistant", final_state["response"]
    )

    # 7. 로깅 — 토큰 사용량 기록 (차단되지 않은 경우만)
    if not final_state.get("is_blocked", False):
        await log_usage(
            redis=redis,
            user_id=current_user.id,
            query=request.query,
            model=final_state["model"],
            prompt_tokens=final_state["prompt_tokens"],
            completion_tokens=final_state["completion_tokens"]
        )

    # 8. 응답 구성 + 캐시 저장
    response_data = {
        "query": final_state["query"],
        "intent": final_state.get("intent", "general"),
        "complexity": final_state.get("complexity", "simple"),
        "model": final_state.get("model", "none"),
        "response": final_state["response"],
        "conversation_id": conversation.id,
        "confidence": final_state.get("confidence", 0.0),
        "is_blocked": final_state.get("is_blocked", False),
    }

    await set_cached_response(redis, request.query, response_data)

    return ChatResponse(**response_data)

@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_active_user), redis: Redis = Depends(get_redis), db: AsyncSession = Depends(get_db)):
    """
    SSE 스트리밍 엔드포인트
    - ChatGPT처럼 답변이 토큰 단위로 실시간 전송됨
    - 프로토콜: Server-Sent Events (text/event-stream)
    """

    # 1. 쿼터 
    await check_quota(redis, current_user.id)

    # 2. 대화 세션
    if request.conversation_id:
        conversation = await conversation_service.get_conversation_detail(
            db, request.conversation_id, current_user.id
        )
    else:
        title = request.query[:30]
        conversation = await conversation_service.create_conversation(
            db, current_user.id, title
        )

    # 3. 사용자 메시지 저장
    await conversation_service.add_message(
        db, conversation.id, "user", request.query
    )

    # 4. State 초기화 — 고도화된 상태
    input_messages = request.messages + [{"role": "user", "content": request.query}]

    initial_state = {
        "messages": input_messages,
        "query": request.query,
        "intent": "general",
        "confidence": 0.0,
        "complexity": "",
        "model": "",
        "is_blocked": False,
        "block_reason": "",
        "output_quality": "pass",
        "retry_count": 0,
        "sub_queries": [],
        "search_results": [],
        "response": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }

    # 5. 스트리밍 제네레이터 함수
    async def event_generator():
        """
        astream_events()로 LangGraph 실행 중 발생하는
        모든 이벤트를 실시간으로 SSE 형식으로 전송
        """
        full_response = ""
        current_intent = "general"
        is_blocked = False

        async for event in agent.astream_events(initial_state, version="v2"):
            kind = event["event"]
            
            # 노드 시작 이벤트 — 현재 진행 상태를 클라이언트에 전송
            if kind == "on_chain_start" and event.get("name"):
                node_name = event["name"]
                # 주요 노드 진입 시 상태 알림
                if node_name in ("input_guard", "classifier", "search_agent", 
                                 "analysis_agent", "creative_agent", "general_agent",
                                 "output_guard"):
                    status_map = {
                        "input_guard": " 입력 검증 중...",
                        "classifier": " 의도 분석 중...",
                        "search_agent": " 검색 에이전트 실행 중...",
                        "analysis_agent": " 분석 에이전트 실행 중...",
                        "creative_agent": " 창작 에이전트 실행 중...",
                        "general_agent": " 응답 생성 중...",
                        "output_guard": " 응답 검증 중...",
                    }
                    status_msg = status_map.get(node_name, "")
                    if status_msg:
                        yield f"data: {json.dumps({'status': status_msg}, ensure_ascii=False)}\n\n"

            # LLM이 토큰을 하나씩 생성할 때마다 발생하는 이벤트
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content: # 빈 문자열 제외
                    # SSE 형식: "data: {json}\n\n"
                    full_response += content
                    yield f"data: {json.dumps({'token': content}, ensure_ascii=False)}\n\n"

        # 스트림 완료 후 AI 응답 DB 저장
        await conversation_service.add_message(
            db, conversation.id, "assistant", full_response
        )

        # 스트리밍 종료 신호
        yield f"data: {json.dumps({'token': '[DONE]', 'conversation_id': conversation.id})}\\n\\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
