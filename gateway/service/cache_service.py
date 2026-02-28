import json
import hashlib
from redis.asyncio import Redis

# 캐시 TTL (초) — 1시간
CACHE_TTL = 3600

def _make_cache_key(query: str) -> str:
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return f"cache:{query_hash}"


async def get_cached_response(redis: Redis, query: str) -> dict | None:
    """
    캐시에서 응답 조회
    Returns:
        캐시 히트: {"query": ..., "complexity": ..., "model": ..., "response": ...}
        캐시 미스: None
    """
    key = _make_cache_key(query)
    cached = await redis.get(key)
    
    if cached:
        return json.loads(cached)
    
    return None


async def set_cached_response(redis: Redis, query: str, response_data: dict) -> None:
    """
    응답을 캐시에 저장
    Args:
        query: 원본 질문 (키 생성용)
        response_data: 저장할 응답 dict
    """
    key = _make_cache_key(query)
    await redis.set(key, json.dumps(response_data, ensure_ascii=False), ex=CACHE_TTL)