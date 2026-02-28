from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from core.database import get_db
from models.users import User
from models.api_key import ApiKey

# HTTPBearer: Authorization 헤더에서 "Bearer <token>" 자동 추출
# APIKeyHeader: "X-API-Key" 헤더에서 추출
# auto_error=False: 둘 중 하나라도 있으면 되기 때문에 자동 에러를 끕니다.
security_schema = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id, 
        "exp": expire, 
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {
        "sub": user_id, 
        "exp": expire, 
        "type": "refresh"
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

async def get_current_user(
    credencials: HTTPAuthorizationCredentials = Depends(security_schema),
    api_key_str: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """JWT 접근 토큰 또는 API Key를 검증하고 DB에서 User 객체를 반환합니다."""
    
    if api_key_str:
        # 1. API Key 검증
        stmt = select(ApiKey).where(ApiKey.key == api_key_str, ApiKey.is_active == True)
        result = await db.execute(stmt)
        api_key = result.scalars().first()
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않거나 만료된 API 키입니다")
            
        stmt = select(User).where(User.id == api_key.user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다")
        return user
        
    elif credencials:
        # 2. JWT 검증
        token = credencials.credentials
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type", "access")  # 이전 토큰 호환을 위해 기본값 access
            
            if user_id is None or token_type != "access":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 접근 토큰입니다")
                
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 검증에 실패했습니다")
            
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다")
            
        return user
        
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 정보(토큰 또는 API 키)가 제공되지 않았습니다")

async def verify_refresh_token(refresh_token: str, db: AsyncSession) -> User:
    """리프레시 토큰을 검증하고 User 객체를 반환합니다."""
    try:
        payload = jwt.decode(refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 리프레시 토큰입니다")
            
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="리프레시 토큰 검증에 실패했습니다")
        
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용할 수 없는 계정입니다")
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """활성화된 사용자만 통과시킵니다."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비활성화된 계정입니다")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """관리자 권한이 있는 사용자만 통과시킵니다."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다")
    return current_user