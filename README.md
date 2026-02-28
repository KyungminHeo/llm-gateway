# LLM Gateway

LangGraph 기반 지능형 LLM API 게이트웨이.
사용자 질의의 복잡도를 분석하여 경량 모델(llama3.2:3b)과 고성능 모델(qwen2.5:7b)을 자동으로 라우팅한다.

## 구성 요소

- **Gateway** - FastAPI 기반 API 서버 (인증, 캐싱, 요청 라우팅)
- **Ollama** - 로컬 LLM 추론 서버
- **Redis** - 응답 캐싱 및 Rate Limiting
- **Nginx** - 리버스 프록시
- **PostgreSQL** - 사용자/대화 이력 저장 (Supabase)

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

### API 접근

- Health Check: `GET http://localhost/health`
- 인증: `POST http://localhost/api/auth/...`
- 채팅: `POST http://localhost/api/chat/...`
- 관리: `GET http://localhost/api/admin/...`

## 기술 스택

Python, FastAPI, LangGraph, Ollama, Redis, PostgreSQL, Nginx, Docker

## 상태

개발 진행 중 (v0.1.0)
