from datetime import datetime, timezone
from fastapi import HTTPException, status
from redis.asyncio import Redis

# 분당 최대 요청 수
MAX_REQUESTS_PER_MINUTE = 20
# 쿼터 키 TTL (초) — 2분 (여유분 포함)
QUOTA_TTL = 120

def _make_quota_key(user_id: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return f"quota:{user_id}:{now}"


async def check_quota(redis: Redis, user_id: str) -> int:
    """
    쿼터 확인 + 카운트 증가
    Returns:
        현재 사용 횟수 (증가 후)
    Raises:
        429 Too Many Requests: 쿼터 초과 시
    """
    key = _make_quota_key(user_id)
    
    # INCR: 키가 없으면 1로 생성, 있으면 +1
    # 원자적(atomic) 연산 — 동시 요청에도 안전
    current = await redis.incr(key)
    
    # 첫 요청이면 TTL 설정 (2분 후 자동 삭제)
    if current == 1:
        await redis.expire(key, QUOTA_TTL)
    
    # 쿼터 초과
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
    used = await redis.get(key)
    used = int(used) if used else 0
    
    return{
        "user_id": user_id,
        "used": used,
        "limit": MAX_REQUESTS_PER_MINUTE,
        "remaining": MAX_REQUESTS_PER_MINUTE - used,
    }