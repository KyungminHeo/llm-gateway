from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.dependencies import init_connections, close_connections
from core.database import engine
from router import chat, admin, auth, user

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

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(user.router, prefix="/api/user", tags=["User"])

@app.get("/health")
async def health():
    return {"status": "ok"}