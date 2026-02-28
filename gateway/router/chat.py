from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
import json
from schemas.chat import ChatRequest, ChatResponse
from agent.graph import agent
from core.security import get_current_active_user
from models.users import User
from core.dependencies import get_redis
from service.cache_service import get_cached_response, set_cached_response
from service.quota_service import check_quota
from service.log_service import log_usage

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_active_user), redis: Redis = Depends(get_redis)):
    """
    전체 파이프라인:
    1. JWT 인증
    2. 쿼터 확인 (분당 20회)
    3. 캐시 확인 → 히트 시 즉시 반환
    4. LangGraph Agent 실행 (classifier → llm_node)
    5. 토큰 사용량 로깅
    6. 응답 캐시 저장
    7. 응답 반환
    """

    # 1. 쿼터
    await check_quota(redis, current_user.id)

    # 2. 캐시
    cached = await get_cached_response(redis, request.query)
    if cached:
        return ChatResponse(**cached)

    # 3. LangGraph State 초기화
    # 받아온 과거 대화내역(request.messages)의 끝에 "이번 질문(request.query)"을 덧붙입니다.
    input_messages = request.messages + [{"role": "user", "content": request.query}]
    
    initial_state = {
        "messages": input_messages,  # 배열 통째로 주입!
        "query": request.query,
        "complexity": "",
        "model": "",
        "response": "",
        "prompt_tokens": 0,
        "completion_tokens": 0
    }

    # 실행
    final_state = await agent.ainvoke(initial_state)

    # 4. 로깅 — 토큰 사용량 기록
    await log_usage(
        redis=redis,
        user_id=current_user.id,
        query=request.query,
        model=final_state["model"],
        prompt_tokens=final_state["prompt_tokens"],
        completion_tokens=final_state["completion_tokens"]
    )

    # 5. 응답 구성 + 캐시 저장
    response_data = {
        "query": final_state["query"],
        "complexity": final_state["complexity"],
        "model": final_state["model"],
        "response": final_state["response"],
    }

    await set_cached_response(redis, request.query, response_data)

    return ChatResponse(**response_data)

@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_active_user), redis: Redis = Depends(get_redis)):
    """
    SSE 스트리밍 엔드포인트
    - ChatGPT처럼 답변이 토큰 단위로 실시간 전송됨
    - 프로토콜: Server-Sent Events (text/event-stream)
    """

    # 1. 쿼터 
    await check_quota(redis, current_user.id)

    # 2. State 초기화
    input_messages = request.messages + [{"role": "user", "content": request.query}]

    initial_state = {
        "messages": input_messages,
        "query": request.query,
        "complexity": "",
        "model": "",
        "response": "",
        "prompt_tokens": 0,
        "completion_tokens": 0
    }

    # 3. 스트리밍 제네레이터 함수
    async def event_generator():
        """
        astream_events()로 LangGraph 실행 중 발생하는
        모든 이벤트를 실시간으로 SSE 형식으로 전송
        """
        async for event in agent.astream_events(initial_state, version="v2"):
            kind = event["event"]

            # LLM이 토큰을 하나씩 생성할 때마다 발생하는 이벤트
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content: # 빈 문자열 제외
                    # SSE 형식: "data: {json}\n\n"
                    yield f"data: {json.dumps({'token': content}, ensure_ascii=False)}\n\n"

        # 스트리밍 종료 신호
        yield f"data: {json.dumps({'token': '[DONE]'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
