from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class TimestampMixin:
    """
    모든 모델에 공통 적용할 생성/수정 시간
    
    사용법:
        class User(TimestampMixin, Base):
            __tablename__ = "users"
            ...
    
    실무 포인트:
    - server_default=func.now(): DB 서버 시간 기준 (앱 서버 시간 X)
    - onupdate=func.now(): UPDATE 쿼리 시 자동으로 갱신
    - timezone.utc: UTC 기준 저장 → 클라이언트에서 로컬 변환
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
