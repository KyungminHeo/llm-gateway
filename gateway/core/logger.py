import logging
import json
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar

# 요청별 고유 ID를 저장하는 Context Variable
# (같은 요청 내에서는 어디서든 동일한 request_id에 접근 가능)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    """
    로그를 JSON 형식으로 출력하는 포매터
    
    Before: INFO: 172.19.0.5 - "POST /api/chat/" 200 OK
    After:  {"timestamp": "...", "level": "INFO", "message": "...", "request_id": "abc-123"}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_var.get("-"),
        }

        # 추가 필드가 있으면 병합 (예: user_id, duration_ms 등)
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """구조화된 JSON 로거 생성"""
    logger = logging.getLogger(name)

    # 중복 핸들러 방지
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def generate_request_id() -> str:
    """요청별 고유 추적 ID 생성"""
    return str(uuid.uuid4())[:8]  # 짧게 8자만 사용