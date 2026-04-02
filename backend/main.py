from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import chat, law
from src.core.config import get_settings
from src.repository.chat_repository import init_db

settings = get_settings()

# FastAPI 애플리케이션 생성 및 라우터 등록
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="부동산공법 RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (일단 개발 단계에서는 모든 출처 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router)
app.include_router(law.router)

# 헬스체크 엔드포인트
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}

# 루트 엔드포인트
@app.get("/")
async def root() -> dict:
    return {"status": "ok", "version": "1.0.0"}