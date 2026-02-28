from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from core.database import get_db
from core.security import create_access_token, create_refresh_token, verify_refresh_token
from schemas.auth import UserCreate, UserResponse, Token
from service.auth_service import create_user, authenticate_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """새로운 사용자를 등록합니다."""
    # DB에 사용자 생성 (중복 검사는 service에서 처리)
    user = await create_user(db, user_in)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """사용자 자격 증명을 확인하고 JWT 액세스 토큰을 반환합니다."""
    # 사용자 인증
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 발행
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """리프레시 토큰을 사용해 새로운 액세스 토큰을 발급받습니다."""
    user = await verify_refresh_token(request.refresh_token, db)
    
    # 새 토큰 쌍 발급
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)
