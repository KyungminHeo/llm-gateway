import time
from fastapi import HTTPException, status
from redis.asyncio import Redis

# 분당 최대 요청 수
MAX_REQUESTS_PER_MINUTE = 20
# 슬라이딩 윈도우 크기 (초)
WINDOW_SECONDS = 60


def _make_quota_key(user_id: str) -> str:
    return f"quota:sliding:{user_id}"


async def check_quota(redis: Redis, user_id: str) -> int:
    """
    슬라이딩 윈도우 방식 쿼터 확인 + 카운트 증가

    Redis Sorted Set을 사용해 분 경계 우회 문제를 해결합니다.
    - score = 요청 시각(unix timestamp)
    - 60초 이전 기록은 자동 제거하여 항상 최근 1분 기준으로 계산

    Returns:
        현재 윈도우 내 사용 횟수 (증가 후)
    Raises:
        429 Too Many Requests: 쿼터 초과 시
    """
    key = _make_quota_key(user_id)
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = redis.pipeline()
    # 60초 이전 기록 제거
    pipe.zremrangebyscore(key, "-inf", window_start)
    # 현재 요청 추가 (score=timestamp, member=고유값으로 timestamp 사용)
    pipe.zadd(key, {str(now): now})
    # 윈도우 내 총 요청 수 조회
    pipe.zcard(key)
    # TTL 갱신 (마지막 요청 기준 60초)
    pipe.expire(key, WINDOW_SECONDS)
    results = await pipe.execute()

    current = results[2]  # zcard 결과

    if current > MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"분당 {MAX_REQUESTS_PER_MINUTE}회 요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요."
        )
    return current


async def get_remaining_quota(redis: Redis, user_id: str) -> dict:
    """
    남은 쿼터 조회 (admin 대시보드용)
    Returns:
        {"user_id": "admin", "used": 7, "limit": 20, "remaining": 13}
    """
    key = _make_quota_key(user_id)
    window_start = time.time() - WINDOW_SECONDS

    # 만료된 기록 제거 후 현재 윈도우 카운트 조회
    await redis.zremrangebyscore(key, "-inf", window_start)
    used = await redis.zcard(key)

    return {
        "user_id": user_id,
        "used": used,
        "limit": MAX_REQUESTS_PER_MINUTE,
        "remaining": max(0, MAX_REQUESTS_PER_MINUTE - used),
    }