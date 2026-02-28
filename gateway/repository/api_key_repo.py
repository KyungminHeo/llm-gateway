from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.api_key import ApiKey


async def create(db: AsyncSession, api_key: ApiKey) -> ApiKey:
    """API 키 저장"""
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def find_by_user_id(db: AsyncSession, user_id: str) -> list[ApiKey]:
    """유저의 API 키 목록 조회 (최신순)"""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def find_by_id_and_user(db: AsyncSession, key_id: str, user_id: str) -> ApiKey | None:
    """특정 API 키 조회 (본인 것만)"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    )
    return result.scalars().first()


async def deactivate(db: AsyncSession, api_key: ApiKey) -> None:
    """API 키 비활성화"""
    api_key.is_active = False
    await db.commit()
