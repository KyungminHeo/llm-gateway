from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

# 1. Async 엔진 생성
#    - echo=True: 실행되는 SQL을 콘솔에 출력 (개발용, 프로덕션에서는 False)
#    - pool_size: 커넥션 풀에 유지할 연결 수
#    - max_overflow: pool_size 초과 시 추가 허용 연결 수
engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_size=5,
    max_overflow=10
)


# 2. 세션 팩토리
#    - expire_on_commit=False: commit 후에도 객체 속성에 접근 가능
#      (True면 commit 후 속성 접근 시 LazyLoad → async에서 에러 발생)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# 3. Base 클래스 — 모든 모델이 상속받는 부모
#    여기서 선언하면 순환 import 방지 가능
class Base(DeclarativeBase):
    pass


# 4. DB 세션 DI (Dependency Injection)
#    FastAPI의 Depends()에서 사용
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()