import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from models.users import User
from schemas.auth import UserCreate

def get_password_hash(password: str) -> str:
    """비밀번호 평문을 bcrypt로 해싱"""
    # bcrypt는 72바이트 초과 비밀번호를 허용하지 않으므로, 
    # 원한다면 여기서 hashlib.sha256(password.encode()).hexdigest() 로 먼저 감쌀 수 있습니다.
    # 현재는 기본 동작 사용.
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
    
    # 1. 이메일 중복 확인
    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다."
        )
        
    # 2. 유저네임 중복 확인
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 아이디입니다."
        )
        
    # 3. User 모델 객체 생성 (비밀번호 해싱!)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    
    # 4. DB 저장
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user) # DB에서 생성된 id, created_at 등을 가져옴
    
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """로그인 검증 비즈니스 로직"""
    
    # 1. username으로 유저 조회
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # 2. 유저가 없거나 비밀번호가 틀리면 False 
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
        
    return user