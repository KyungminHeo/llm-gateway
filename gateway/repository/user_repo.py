from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.users import User


async def find_by_email(db: AsyncSession, email: str) -> User | None:
    """이메일로 유저 조회"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def find_by_username(db: AsyncSession, username: str) -> User | None:
    """유저네임으로 유저 조회"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def create(db: AsyncSession, user: User) -> User:
    """유저 저장"""
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
