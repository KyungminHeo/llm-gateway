import json
from datetime import datetime, timezone
from redis.asyncio import Redis

"""
토큰 사용량 로깅 서비스

Redis에 유저별/모델별 토큰 사용량을 누적 저장

Redis 키 구조:
  log:{user_id}:total_tokens      → 누적 총 토큰 수 (INCRBY)
  log:{user_id}:request_count     → 누적 요청 횟수 (INCR)
  log:{user_id}:history           → 최근 요청 기록 리스트 (LPUSH, 최대 100개)
  
chat-platform과 비교:
  chat-platform: 최근 메시지 30개를 Redis List로 캐싱
  여기: 최근 요청 기록 100개를 Redis List로 저장
  → 둘 다 LPUSH + LTRIM 패턴
"""

# 최근 기록 보관 개수
MAX_HISTORY = 100

async def log_usage(
    redis: Redis, user_id: str, query: str, model: str, prompt_tokens: int, completion_tokens: int
) -> None:
    """
    요청 1건의 토큰 사용량 기록
    3가지 데이터를 동시에 업데이트:
    1. 총 토큰 수 누적
    2. 요청 횟수 +1
    3. 상세 기록 리스트에 추가
    """
    total_tokens = prompt_tokens + completion_tokens
    
    # Pipeline: 여러 Redis 명령을 한 번에 보냄 (네트워크 왕복 1번)
    pipe = redis.pipeline()
    
    # 1. 누적 토큰 수
    pipe.incrby(f"log:{user_id}:total_tokens", total_tokens)
    
    # 2. 요청 횟수
    pipe.incr(f"log:{user_id}:request_count")
    
    # 3. 상세 기록 (최근 100건만 유지)
    record = json.dumps({
        "query": query[:100],      # 질문 앞 100자만 저장 (메모리 절약)
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False)
    
    pipe.lpush(f"log:{user_id}:history", record)
    pipe.ltrim(f"log:{user_id}:history", 0, MAX_HISTORY - 1)
    
    # 한 번에 실행
    await pipe.execute()
    
async def get_usage_summary(redis: Redis, user_id: str) -> dict:
    """
    유저별 사용량 요약 조회
    
    Returns:
        {
            "user_id": "admin",
            "total_tokens": 12345,
            "request_count": 67,
            "recent_history": [...]   ← 최근 10건
        }
    """
    # Pipeline으로 3개 키를 한 번에 조회
    pipe = redis.pipeline()
    pipe.get(f"log:{user_id}:total_tokens")
    pipe.get(f"log:{user_id}:request_count")
    pipe.lrange(f"log:{user_id}:history", 0, 9)  # 최근 10건만
    results = await pipe.execute()
    
    total_tokens = int(results[0]) if results[0] else 0
    request_count = int(results[1]) if results[1] else 0
    history = [json.loads(h) for h in results[2]] if results[2] else []
    
    return {
        "user_id": user_id,
        "total_tokens": total_tokens,
        "request_count": request_count,
        "recent_history": history
    }