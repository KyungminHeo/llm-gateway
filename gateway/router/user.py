from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.security import get_current_active_user
from models.users import User
from schemas.api_key import ApiKeyCreate, ApiKeyResponse
from service.api_key_service import create_api_key, get_user_api_keys, revoke_api_key

router = APIRouter()

@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """새로운 API 키를 발급합니다."""
    return await create_api_key(db, current_user.id, data)

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """내 API 키 목록을 조회합니다."""
    return await get_user_api_keys(db, current_user.id)

@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """API 키를 폐기(비활성화)합니다."""
    success = await revoke_api_key(db, current_user.id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없거나 권한이 없습니다.")
