# LLM Gateway

LangGraph 기반 지능형 LLM API 게이트웨이.
사용자 질의의 의도를 LLM으로 분석하여 검색, 분석, 창작, 일반 대화 등 목적에 맞는 전문 에이전트로 자동 라우팅한다.

---

## 주요 기능

- **LLM 기반 Intent 분류** - LLM Structured Output으로 의도를 4방향(search/analysis/creative/general) 분류
- **멀티 에이전트 아키텍처** - 의도별 전문 서브그래프(검색, 분석) + Tool Calling 에이전트(창작, 일반)
- **Guard Rails** - 입력 보안 검증(프롬프트 인젝션 탐지, 유해 콘텐츠 필터링) + 출력 품질 검증
- **Tool Calling** - 웹 검색, 수학 계산, 현재 시간, URL 텍스트 추출 (4개 도구)
- **SSE 스트리밍** - 토큰 단위 실시간 응답 전송 + 노드별 진행 상태 알림
- **대화 관리** - 대화 세션 생성/조회/삭제, 메시지 DB 저장
- **JWT 인증** - Access/Refresh Token 이중 토큰, API Key 인증 지원
- **RBAC** - 역할 기반 접근 제어 (user/admin)
- **응답 캐싱** - Redis 기반 동일 질의 캐시 (TTL 1시간)
- **Rate Limiting** - 분당 20회 요청 제한
- **구조화된 로깅** - JSON 형식 로그, 요청별 추적 ID (X-Request-ID)
- **메트릭 수집** - 요청 수, 응답 시간, 상태코드 분포, 느린 요청 Top 5
- **에러 복구** - 재시도 루프(최대 2회) + Fallback 안내 메시지

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| API 서버 | Python, FastAPI, Uvicorn |
| LLM 프레임워크 | LangGraph, LangChain |
| LLM 추론 | Ollama (llama3.2:3b, qwen2.5:7b) |
| 데이터베이스 | PostgreSQL, SQLAlchemy Async, Alembic |
| 캐시/쿼터/로깅 | Redis |
| 인증 | JWT (python-jose), bcrypt |
| 리버스 프록시 | Nginx (Rate Limit, SSE Proxy) |
| 테스트 | pytest, pytest-asyncio |
| 인프라 | Docker, Docker Compose |

---

## 아키텍처

```
Client
  |
  v
Nginx (Rate Limit 10r/s, SSE Proxy, LLM 타임아웃 300s)
  |
  v
FastAPI Gateway
  |
  +-- JWT / API Key 인증
  +-- Rate Limiting (Redis, 분당 20회)
  +-- 캐시 확인 (Redis, MD5 해시)
  |
  +-- LangGraph Agent (10+ 노드, 5+ 조건부 분기)
  |     |
  |     +-- Input Guard -----(차단)----> 차단 응답 -> END
  |     |       |
  |     |     (안전)
  |     |       |
  |     +-- Intent Classifier (llama3.2:3b, 4방향 분류)
  |     |       |
  |     |       +-- search ----> 검색 서브그래프 (query_refiner -> web_search -> synthesizer)
  |     |       +-- analysis --> 분석 서브그래프 (decomposer -> researcher -> synthesizer)
  |     |       +-- creative --> Tool Calling LLM (qwen2.5:7b + 4개 도구)
  |     |       +-- general --> 직접 LLM 응답 (llama3.2:3b)
  |     |                                |
  |     +-- Output Guard -----(retry)---> Classifier로 재시도 (최대 2회)
  |     |       |           `-(fallback)-> 안내 메시지 -> END
  |     |     (pass)
  |     |       |
  |     +------ END
  |
  +-- 대화 저장 (PostgreSQL)
  +-- 토큰 사용량 로깅 (Redis Pipeline)
  +-- 메트릭 수집 + JSON 로깅
```

---

## 프로젝트 구조

```
llm-gateway/
├── .env                          # 환경변수
├── docker-compose.yml            # Nginx + Gateway + Ollama + Redis
│
├── nginx/
│   └── nginx.conf                # Rate Limit, SSE Proxy
│
├── docs/
│   ├── ARCHITECTURE_ROADMAP.md   # 아키텍처 로드맵
│   ├── LANGGRAPH_UPGRADE.md      # LangGraph 고도화 기록
│   ├── LANGGRAPH_FLOW.md         # LangGraph 처리 흐름 상세
│   └── DEVELOPMENT.md            # 전체 개발 문서
│
└── gateway/                      # FastAPI 애플리케이션
    ├── main.py                   # 앱 진입점 (lifespan, 미들웨어, 라우터 등록)
    ├── dockerfile
    ├── requirements.txt
    │
    ├── core/                     # 핵심 인프라
    │   ├── config.py             # 환경 변수 관리 (Pydantic Settings)
    │   ├── database.py           # SQLAlchemy Async 엔진 + 세션
    │   ├── dependencies.py       # Redis/Ollama DI (lifespan 관리)
    │   ├── security.py           # JWT 발행/검증, API Key, RBAC
    │   ├── logger.py             # JSON 구조화 로깅 + Request ID
    │   └── metrics.py            # 요청 메트릭 미들웨어
    │
    ├── models/                   # SQLAlchemy ORM
    │   ├── base.py               # TimestampMixin (created_at, updated_at)
    │   ├── users.py              # User (UUID PK, bcrypt, role)
    │   ├── api_key.py            # ApiKey (sk-... 형식)
    │   └── conversation.py       # Conversation + Message (1:N)
    │
    ├── schemas/                  # Pydantic 요청/응답 스키마
    │   ├── auth.py               # UserCreate, UserResponse, Token
    │   ├── chat.py               # ChatRequest, ChatResponse
    │   ├── conversation.py       # ConversationCreate/Summary/Detail
    │   └── api_key.py            # ApiKeyCreate, ApiKeyResponse
    │
    ├── repository/               # DB 접근 레이어
    │   ├── user_repo.py
    │   ├── api_key_repo.py
    │   └── conversation_repo.py
    │
    ├── service/                  # 비즈니스 로직
    │   ├── auth_service.py       # bcrypt 해싱, 회원가입, 로그인 검증
    │   ├── api_key_service.py    # API Key 생성/조회/폐기
    │   ├── conversation_service.py # 대화 세션 관리
    │   ├── cache_service.py      # Redis MD5 해시 캐시
    │   ├── quota_service.py      # 분당 20회 요청 제한
    │   └── log_service.py        # Redis Pipeline 토큰 로깅
    │
    ├── router/                   # API 엔드포인트
    │   ├── auth.py               # /api/auth
    │   ├── chat.py               # /api/chat (동기 + SSE 스트리밍)
    │   ├── conversation.py       # /api/conversations
    │   ├── user.py               # /api/user (API Key 관리)
    │   └── admin.py              # /api/admin (관리자 전용)
    │
    ├── agent/                    # LangGraph 에이전트
    │   ├── graph.py              # 메인 그래프 (10+ 노드, 5+ 조건부 분기)
    │   ├── state.py              # AgentState (16개 필드)
    │   ├── tool.py               # 도구 4개 (search, calculate, datetime, url)
    │   ├── nodes/
    │   │   ├── intent_schema.py  # 의도 분류 스키마 + 매핑 테이블
    │   │   ├── classifier.py     # LLM 기반 4방향 Intent Classifier
    │   │   ├── llm_node.py       # LLM 호출 (의도별 프롬프트 + Tool Binding)
    │   │   ├── input_guard.py    # 입력 보안 검증 (인젝션 탐지 10패턴)
    │   │   ├── output_guard.py   # 출력 품질 검증 + 재시도
    │   │   └── fallback_node.py  # 재시도 초과 시 안내 메시지
    │   └── subgraphs/
    │       ├── search_subgraph.py    # 검색: query_refiner -> web_search -> synthesizer
    │       └── analysis_subgraph.py  # 분석: decomposer -> researcher -> synthesizer
    │
    ├── alembic/                  # DB 마이그레이션
    │
    └── tests/
        ├── conftest.py
        ├── test_auth.py
        ├── test_conversation.py
        └── test_metrics.py
```

---

## LangGraph 처리 흐름

사용자 요청부터 응답까지의 전체 파이프라인:

```
1. Router 전처리
   JWT 인증 -> 쿼터 확인 -> 캐시 확인 -> 대화 세션 로드 -> 사용자 메시지 DB 저장

2. agent.ainvoke(initial_state) 호출

3. Input Guard
   빈 입력 / 길이 초과(4000자) / 인젝션 패턴(10종) / 유해 키워드 검사
   -> 차단 시: 차단 응답 반환 후 즉시 END
   -> 통과 시: 다음 노드로

4. Intent Classifier
   llama3.2:3b가 질문 의도를 JSON으로 분류
   -> {"intent": "search", "confidence": 0.95, "reasoning": "..."}
   -> 확신도 < 0.7이면 general로 폴백
   -> 의도에 따라 모델 할당:
      search/analysis/creative -> qwen2.5:7b
      general                  -> llama3.2:3b

5. 의도별 에이전트 실행
   search   -> 검색 서브그래프 (검색어 최적화 -> 이중 검색 -> 결과 종합)
   analysis -> 분석 서브그래프 (질문 분해 -> 개별 조사 -> 종합 분석)
   creative -> llm_node + Tool Calling 루프 (도구 호출 시 반복)
   general  -> llm_node 직접 응답

6. Output Guard
   빈 응답, 짧은 응답, 무의미한 응답 검증
   -> pass: END
   -> retry: Classifier로 복귀 (최대 2회)
   -> fallback: 의도별 안내 메시지 반환 후 END

7. Router 후처리
   AI 응답 DB 저장 -> 토큰 사용량 Redis 로깅 -> 캐시 저장 -> 응답 반환
```

---

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
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### 실행

```bash
docker compose up --build -d
```

첫 실행 시 `ollama-pull` 서비스가 모델(llama3.2:3b, qwen2.5:7b)을 자동으로 다운로드한다.

### DB 마이그레이션

```bash
docker compose exec gateway alembic upgrade head
```

### 테스트 실행

```bash
docker compose exec gateway pytest tests/ -v
```

### API 문서

`http://localhost/docs`에서 Swagger UI로 전체 API를 확인하고 테스트할 수 있다.

---

## API 목록

### 인증 (/api/auth)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/auth/register` | 없음 | 회원가입 |
| POST | `/api/auth/login` | 없음 | 로그인 (JWT 발급) |
| POST | `/api/auth/refresh` | 없음 | Access Token 갱신 |

### 채팅 (/api/chat)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/chat/` | JWT/APIKey | 채팅 (동기 응답) |
| POST | `/api/chat/stream` | JWT/APIKey | SSE 스트리밍 응답 |

### 대화 관리 (/api/conversations)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/conversations/` | JWT/APIKey | 대화 생성 |
| GET | `/api/conversations/` | JWT/APIKey | 대화 목록 조회 |
| GET | `/api/conversations/{id}` | JWT/APIKey | 대화 상세 (메시지 포함) |
| DELETE | `/api/conversations/{id}` | JWT/APIKey | 대화 삭제 |

### 사용자 (/api/user)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/user/api-keys` | JWT | API Key 생성 |
| GET | `/api/user/api-keys` | JWT | API Key 목록 |
| DELETE | `/api/user/api-keys/{id}` | JWT | API Key 폐기 |

### 관리자 (/api/admin)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| GET | `/api/admin/models` | JWT (admin) | Ollama 모델 목록 |
| GET | `/api/admin/usage` | JWT (admin) | 토큰 사용량 요약 |

### 모니터링

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| GET | `/health` | 없음 | 서버 상태 확인 |
| GET | `/api/metrics` | 없음 | 실시간 메트릭 조회 |

---

## 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| 개발 문서 | `docs/DEVELOPMENT.md` | 전체 프로젝트 아키텍처, DB 스키마, API, 인증 흐름 |
| LangGraph 흐름 | `docs/LANGGRAPH_FLOW.md` | 그래프 처리 흐름 Phase별 상세 추적 |
| 고도화 기록 | `docs/LANGGRAPH_UPGRADE.md` | LangGraph 3노드 -> 10+노드 변경 이력 |
| 아키텍처 로드맵 | `docs/ARCHITECTURE_ROADMAP.md` | 프로젝트 분석 및 향후 개선 방향 |
