from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # JWT 설정
    jwt_secret: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Redis
    redis_url: str = "redis://redis:6379"

    # Ollama
    ollama_url: str = "http://ollama:11434"

    # 모델 이름 (Ollama에 pull 된 모델)
    model_simple: str = "llama3.2:3b"
    model_complex: str = "qwen2.5:7b"

    # 복잡도 판단 기준 (단어 수)
    complexity_threshold: int = 100

    # Pydantic v2 방식: Config 내부 클래스 대신 model_config 사용
    model_config = SettingsConfigDict(
        # config.py -> core -> gateway -> llm-gateway (루트) 아래의 .env 찾기
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,     # 환경변수 대소문자 무시
        protected_namespaces=(),  # 'model_' 접두사 경고 무시
    )

    # Database
    database_url: str


# 싱글톤 인스턴스 — 앱 어디서든 import해서 사용
settings = Settings()