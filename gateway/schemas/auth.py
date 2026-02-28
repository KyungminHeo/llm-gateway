import re
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    """회원가입 요청 시 받을 데이터"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자 아이디")
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError('비밀번호에는 최소 하나의 영문자가 포함되어야 합니다.')
        if not re.search(r"\d", v):
            raise ValueError('비밀번호에는 최소 하나의 숫자가 포함되어야 합니다.')
        if not re.search(r"[\W_]", v):
            raise ValueError('비밀번호에는 최소 하나의 특수문자가 포함되어야 합니다.')
        return v

class UserResponse(BaseModel):
    """회원가입/정보 조회 성공 시 돌려줄 데이터 (비밀번호 제외!)"""
    id: str
    username: str
    email: str
    is_active: bool
    role: str

    model_config = {
        "from_attributes": True  # SQLAlchemy 모델 객체를 Pydantic 모델로 자동 변환
    }

class Token(BaseModel):
    """로그인 성공 시 돌려줄 JWT 토큰 형태"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"