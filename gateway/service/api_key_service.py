import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.api_key import ApiKey
from schemas.api_key import ApiKeyCreate

async def create_api_key(db: AsyncSession, user_id: str, data: ApiKeyCreate) -> ApiKey:
    raw_key = f"sk-{secrets.token_urlsafe(32)}"
    
    api_key = ApiKey(
        user_id=user_id,
        key=raw_key,
        name=data.name
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key

async def get_user_api_keys(db: AsyncSession, user_id: str) -> list[ApiKey]:
    stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def revoke_api_key(db: AsyncSession, user_id: str, key_id: str) -> bool:
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    api_key = result.scalars().first()
    
    if not api_key:
        return False
        
    api_key.is_active = False
    await db.commit()
    return True
