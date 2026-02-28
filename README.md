# LLM Gateway

LangGraph 기반 지능형 LLM API 게이트웨이.
사용자 질의의 복잡도를 분석하여 경량 모델(llama3.2:3b)과 고성능 모델(qwen2.5:7b)을 자동으로 라우팅한다.

## 주요 기능

- **지능형 모델 라우팅** - 질의 복잡도에 따라 경량/고성능 모델 자동 선택
- **Tool Calling** - LangGraph 기반 웹 검색 도구 호출 (DuckDuckGo 뉴스+텍스트 이중 검색)
- **SSE 스트리밍** - ChatGPT처럼 토큰 단위 실시간 응답 전송
- **대화 관리** - 대화 세션 생성/조회/삭제, 메시지 DB 저장 (ChatGPT 사이드바 기능)
- **JWT 인증** - Access/Refresh Token, API Key 인증 지원
- **RBAC** - 역할 기반 접근 제어 (user/admin)
- **응답 캐싱** - Redis 기반 동일 질의 캐시
- **Rate Limiting** - 분당 요청 수 제한 (쿼터)
- **구조화된 로깅** - JSON 형식 로그, 요청별 추적 ID
- **메트릭 수집** - 요청 수, 응답 시간, 상태코드 분포, 느린 요청 Top 5
- **Repository 패턴** - 서비스 레이어와 DB 접근 레이어 분리

## 기술 스택

| 영역 | 기술 |
|------|------|
| API 서버 | Python, FastAPI, Uvicorn |
| LLM 프레임워크 | LangGraph, LangChain |
| LLM 추론 | Ollama (로컬) |
| 데이터베이스 | PostgreSQL (Supabase), SQLAlchemy, Alembic |
| 캐시/큐 | Redis |
| 인증 | JWT (python-jose), bcrypt |
| 테스트 | pytest |
| 인프라 | Docker, Docker Compose, Nginx |

## 프로젝트 구조

```
llm-gateway/
├── docker-compose.yml
├── nginx.conf
├── .env
└── gateway/
    ├── main.py                    # FastAPI 앱 진입점
    ├── requirements.txt
    ├── dockerfile
    ├── pytest.ini
    │
    ├── agent/                     # LangGraph 에이전트
    │   ├── graph.py               # 그래프 정의 (classifier → llm_node → tools)
    │   ├── state.py               # AgentState 정의
    │   ├── tool.py                # 웹 검색 도구 (DuckDuckGo)
    │   └── nodes/
    │       ├── classifier.py      # 복잡도 분류 노드
    │       └── llm_node.py        # LLM 호출 노드 (Tool Calling)
    │
    ├── core/                      # 핵심 설정
    │   ├── config.py              # 환경 변수 관리 (Pydantic Settings)
    │   ├── database.py            # 비동기 DB 엔진, 세션 팩토리
    │   ├── dependencies.py        # Redis 연결 관리
    │   ├── security.py            # JWT 생성/검증, API Key 인증
    │   ├── logger.py              # 구조화된 JSON 로거
    │   └── metrics.py             # 요청 메트릭 미들웨어
    │
    ├── models/                    # SQLAlchemy 모델
    │   ├── base.py                # Base 클래스, TimestampMixin
    │   ├── users.py               # User 모델
    │   ├── api_key.py             # ApiKey 모델
    │   └── conversation.py        # Conversation, Message 모델
    │
    ├── schemas/                   # Pydantic 스키마 (요청/응답)
    │   ├── auth.py                # UserCreate, UserResponse, Token
    │   ├── chat.py                # ChatRequest, ChatResponse
    │   ├── conversation.py        # ConversationCreate, ConversationDetail
    │   ├── api_key.py             # ApiKeyCreate, ApiKeyResponse
    │   └── user.py                # UserUpdate, PasswordChange
    │
    ├── repository/                # DB 접근 레이어
    │   ├── user_repo.py           # User CRUD
    │   ├── api_key_repo.py        # ApiKey CRUD
    │   └── conversation_repo.py   # Conversation, Message CRUD
    │
    ├── service/                   # 비즈니스 로직 레이어
    │   ├── auth_service.py        # 회원가입, 로그인, 비밀번호 검증
    │   ├── api_key_service.py     # API Key 생성/폐기
    │   ├── conversation_service.py# 대화 세션 관리
    │   ├── cache_service.py       # 응답 캐싱
    │   ├── quota_service.py       # Rate Limiting
    │   └── log_service.py         # 사용량 로깅
    │
    ├── router/                    # API 엔드포인트
    │   ├── auth.py                # /api/auth (회원가입, 로그인, 토큰 갱신)
    │   ├── chat.py                # /api/chat (채팅, SSE 스트리밍)
    │   ├── conversation.py        # /api/conversations (대화 CRUD)
    │   ├── user.py                # /api/user (프로필, 비밀번호 변경)
    │   └── admin.py               # /api/admin (사용량 통계)
    │
    ├── tests/                     # 테스트
    │   ├── conftest.py            # 공통 설정 (TestClient, 인증 헤더)
    │   ├── test_auth.py           # 인증 테스트 (5개)
    │   ├── test_conversation.py   # 대화 CRUD 테스트 (4개)
    │   └── test_metrics.py        # 헬스체크/메트릭 테스트 (2개)
    │
    └── alembic/                   # DB 마이그레이션
        ├── env.py
        └── versions/
```

## 아키텍처

```
Client → Nginx (리버스 프록시)
           → FastAPI Gateway
               ├── JWT/API Key 인증
               ├── Rate Limiting (Redis)
               ├── 캐시 확인 (Redis)
               ├── LangGraph Agent
               │   ├── Classifier (복잡도 판단)
               │   ├── LLM Node (Ollama)
               │   └── Tool Node (웹 검색)
               ├── 대화 저장 (PostgreSQL)
               └── 메트릭 수집 + JSON 로깅
```

## 실행 방법

### 사전 준비

- Docker, Docker Compose 설치

### 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성한다.

```
JWT_SECRET=your-secret-key
REDIS_URL=redis://redis:6379
OLLAMA_URL=http://ollama:11434
MODEL_SIMPLE=llama3.2:3b
MODEL_COMPLEX=qwen2.5:7b
COMPLEXITY_THRESHOLD=100
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### 실행

```bash
docker compose up --build
```

첫 실행 시 `ollama-pull` 서비스가 모델을 자동으로 다운로드한다.

### DB 마이그레이션

```bash
docker-compose exec gateway alembic upgrade head
```

### 테스트 실행

```bash
docker-compose exec gateway sh -c "cd /app && PYTHONPATH=/app pytest tests/ -v"
```

## API 목록

### 인증 (Auth)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/auth/refresh` | Access Token 갱신 |

### 채팅 (Chat)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat/` | 채팅 (동기 응답) |
| POST | `/api/chat/stream` | SSE 스트리밍 응답 |

### 대화 관리 (Conversations)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/conversations/` | 대화 생성 |
| GET | `/api/conversations/` | 대화 목록 조회 |
| GET | `/api/conversations/{id}` | 대화 상세 (메시지 포함) |
| DELETE | `/api/conversations/{id}` | 대화 삭제 |

### 사용자 (User)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/user/me` | 내 정보 조회 |
| PUT | `/api/user/me` | 프로필 수정 |
| PUT | `/api/user/me/password` | 비밀번호 변경 |
| POST | `/api/user/api-keys` | API Key 생성 |
| GET | `/api/user/api-keys` | API Key 목록 |
| DELETE | `/api/user/api-keys/{id}` | API Key 폐기 |

### 관리자 (Admin)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/stats` | 사용량 통계 |

### 모니터링 (Monitoring)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 확인 |
| GET | `/api/metrics` | 실시간 메트릭 조회 |

### Swagger UI

`http://localhost/docs` 에서 전체 API 문서를 확인하고 테스트할 수 있다.
