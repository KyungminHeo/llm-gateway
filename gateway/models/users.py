import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from models.base import TimestampMixin
from core.database import Base


class User(TimestampMixin, Base):
    """
    사용자 모델
    
    - id: UUID v4 사용 (auto-increment 대비 보안 우수 — 예측 불가)
    - hashed_password: 평문 비밀번호를 절대 저장하지 않음
    - is_active: 소프트 삭제(soft delete) 패턴 — 실제 삭제 대신 비활성화
    - role: 향후 RBAC(역할 기반 접근 제어)의 기반
    """
    __tablename__ = "users"
    
    # PK: UUID v4 — auto-increment보다 보안적으로 우수
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # 사용자 식별 정보
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,          # 로그인 시 빈번하게 조회 → 인덱스 필수
        nullable=False,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    # bcrypt 해시값 저장 (평문 비밀번호 절대 저장 금지!)
    # bcrypt 해시는 보통 60자, 여유있게 255로 설정
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # 소프트 삭제 + 계정 잠금용
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    
    # 역할: user / admin (향후 RBAC 확장 기반)
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        server_default="user",
    )
