from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.dependencies import init_connections, close_connections
from core.database import engine
from core.metrics import RequestMetricsMiddleware, metrics_store
from router import chat, admin, auth, user, conversation

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_connections()
        yield
    finally:
        await close_connections()
        # DB 연결 풀 정리
        await engine.dispose()
        
app = FastAPI(
    title="LLM API Gateway",
    description="LangGraph 기반 지능형 LLM 라우팅 게이트웨이",
    version="0.1.0",
    lifespan=lifespan
)

# 미들웨어 등록 (모든 요청을 자동 계측)
app.add_middleware(RequestMetricsMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(conversation.router, prefix="/api/conversations", tags=["Conversations"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/metrics", tags=["Monitoring"])
async def get_metrics():
    """실시간 메트릭 조회 — 총 요청 수, 응답 시간, 상태코드별 분포 등"""
    return metrics_store.summary()