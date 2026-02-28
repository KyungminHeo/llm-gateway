import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.users import User
from schemas.auth import UserCreate
from repository import user_repo


def get_password_hash(password: str) -> str:
    """비밀번호 평문을 bcrypt로 해싱"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력받은 평문과 DB의 해시가 일치하는지 검증"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except ValueError:
        return False

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """회원가입 비즈니스 로직"""
    
    # 1. 이메일 중복 확인 (Repository 호출)
    if await user_repo.find_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다."
        )
        
    # 2. 유저네임 중복 확인 (Repository 호출)
    if await user_repo.find_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 아이디입니다."
        )
        
    # 3. User 모델 객체 생성 (비밀번호 해싱 — 비즈니스 로직)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    
    # 4. DB 저장 (Repository 호출)
    return await user_repo.create(db, db_user)

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """로그인 검증 비즈니스 로직"""
    
    # 1. username으로 유저 조회 (Repository 호출)
    user = await user_repo.find_by_username(db, username)
    
    # 2. 비밀번호 검증 (비즈니스 로직)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
        
    return user