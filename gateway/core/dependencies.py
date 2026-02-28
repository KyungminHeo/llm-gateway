import redis.asyncio as airedis
import httpx
from core.config import settings

# 전역 클라이언트 — lifespan에서 초기화/정리
_redis_client: airedis.Redis | None = None
_ollama_client: httpx.AsyncClient | None = None

# === FastAPI Depends()용 함수 ===

async def get_redis() -> airedis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis가 초기화되지 않았습니다. 서버 시작을 확인하세요.")
    return _redis_client


async def get_ollama() -> httpx.AsyncClient:
    if _ollama_client is None:
        raise RuntimeError("Ollama가 초기화되지 않았습니다. 서버 시작을 확인하세요.")
    return _ollama_client
        
        
# === 수명주기 관리 (main.py의 lifespan에서 호출) ===

async def init_connections():
    global _redis_client, _ollama_client
    
    _redis_client = airedis.from_url(
        settings.redis_url,
        decode_responses=True,  # bytes → str 자동 변환
    )
    _ollama_client = httpx.AsyncClient(
        base_url=settings.ollama_url,
        timeout=120.0,  # LLM 응답은 오래 걸릴 수 있음
    )
    
    # 연결 확인 
    await _redis_client.ping()
    print("Redis 연결 성공")
    print("Ollama 클라이언트 준비 완료")
    
    
async def close_connections():
    global _redis_client, _ollama_client
    
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
    if _ollama_client:
        await _ollama_client.aclose()
        _ollama_client = None
    
    print("모든 연결 종료")