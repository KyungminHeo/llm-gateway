"""
pytest 공통 설정
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from fastapi import FastAPI
from core.database import get_db
from core.config import settings
from core.security import create_access_token
from router import auth, chat, admin, user, conversation

# ===== NullPool 엔진 — 매 요청마다 새 커넥션 (테스트 전용) =====
test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

# ===== 테스트 전용 앱 (미들웨어 없이) =====
test_app = FastAPI()
test_app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
test_app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
test_app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
test_app.include_router(user.router, prefix="/api/user", tags=["User"])
test_app.include_router(conversation.router, prefix="/api/conversations", tags=["Conversations"])

# 핵심: get_db를 NullPool 버전으로 교체
test_app.dependency_overrides[get_db] = override_get_db

@test_app.get("/health")
async def health():
    return {"status": "ok"}

@test_app.get("/api/metrics")
async def metrics():
    return {"total_requests": 0, "avg_response_time_ms": 0, "by_status": {}, "by_path": {}, "slowest_top5": []}


@pytest.fixture
def client():
    """동기식 테스트 클라이언트"""
    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """인증된 헤더 — 회원가입 후 JWT 직접 생성"""
    unique = uuid.uuid4().hex[:6]

    response = client.post("/api/auth/register", json={
        "username": f"authuser_{unique}",
        "email": f"auth_{unique}@example.com",
        "password": "Test1234!",
    })
    user_id = response.json()["id"]
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}
