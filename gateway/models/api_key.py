import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import TimestampMixin
from core.database import Base

class ApiKey(TimestampMixin, Base):
    """
    API Key 테이블
    - 사용자가 여러 개의 API키를 생성해서 다른 앱에 넣고 쓸 수 있음
    """
    __tablename__ = "api_keys"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    
    user = relationship("User", backref="api_keys")
