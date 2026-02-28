import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from models.api_key import ApiKey
from schemas.api_key import ApiKeyCreate
from repository import api_key_repo


async def create_api_key(db: AsyncSession, user_id: str, data: ApiKeyCreate) -> ApiKey:
    """API 키 생성 비즈니스 로직"""
    # 키 생성 (비즈니스 로직)
    raw_key = f"sk-{secrets.token_urlsafe(32)}"
    
    api_key = ApiKey(
        user_id=user_id,
        key=raw_key,
        name=data.name
    )
    
    # DB 저장 (Repository 호출)
    return await api_key_repo.create(db, api_key)

async def get_user_api_keys(db: AsyncSession, user_id: str) -> list[ApiKey]:
    """유저의 API 키 목록 조회"""
    return await api_key_repo.find_by_user_id(db, user_id)

async def revoke_api_key(db: AsyncSession, user_id: str, key_id: str) -> bool:
    """API 키 비활성화 비즈니스 로직"""
    # 본인 키 확인 (Repository 호출)
    api_key = await api_key_repo.find_by_id_and_user(db, key_id, user_id)
    
    if not api_key:
        return False
    
    # 비활성화 (Repository 호출)
    await api_key_repo.deactivate(db, api_key)
    return True
