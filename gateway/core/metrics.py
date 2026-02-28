import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.logger import get_logger, generate_request_id, request_id_var

logger = get_logger("metrics")


class MetricsStore:
    """메트릭 저장소 — 인메모리 집계"""

    def __init__(self):
        self.total_requests = 0
        self.by_status = defaultdict(int)     # {200: 42, 404: 3, 500: 1}
        self.by_path = defaultdict(int)        # {"/api/chat/": 30, "/api/auth/login": 12}
        self.total_duration_ms = 0.0
        self.slowest = []                      # [(duration_ms, method, path), ...]

    def record(self, method: str, path: str, status: int, duration_ms: float):
        self.total_requests += 1
        self.by_status[status] += 1
        self.by_path[f"{method} {path}"] += 1
        self.total_duration_ms += duration_ms

        # 가장 느린 요청 Top 5 유지
        self.slowest.append({
            "duration_ms": round(duration_ms, 1),
            "method": method,
            "path": path,
            "status": status,
        })
        self.slowest.sort(key=lambda x: x["duration_ms"], reverse=True)
        self.slowest = self.slowest[:5]

    def summary(self) -> dict:
        avg = round(self.total_duration_ms / self.total_requests, 1) if self.total_requests else 0
        return {
            "total_requests": self.total_requests,
            "avg_response_time_ms": avg,
            "by_status": dict(self.by_status),
            "by_path": dict(self.by_path),
            "slowest_top5": self.slowest,
        }


# 싱글톤 인스턴스
metrics_store = MetricsStore()


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """
    모든 HTTP 요청을 자동 계측하는 미들웨어
    
    기능:
    1. 요청마다 고유 request_id 부여
    2. 응답 시간 측정
    3. JSON 로그 출력
    4. 메트릭 집계
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. 요청 추적 ID 생성 및 ContextVar에 저장
        req_id = generate_request_id()
        request_id_var.set(req_id)

        # 2. 시작 시간 기록
        start = time.perf_counter()

        # 3. 다음 핸들러 실행 (실제 API 로직)
        response = await call_next(request)

        # 4. 응답 시간 계산
        duration_ms = (time.perf_counter() - start) * 1000

        # 5. 메트릭 기록
        metrics_store.record(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

        # 6. 구조화된 로그 출력
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {duration_ms:.0f}ms",
            extra={"extra_data": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 1),
            }}
        )

        # 7. 응답 헤더에 request_id 포함 (디버깅용)
        response.headers["X-Request-ID"] = req_id

        return response
