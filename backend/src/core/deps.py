from functools import lru_cache
from typing import Annotated

import chromadb
from fastapi import Depends
from openai import AsyncOpenAI

from core.config import Settings, get_settings

# <Note>
# deps.py는 의존성 주입(Dependency Injection) 관련 코드들을 모아놓은 모듈
# FastAPI의 Depends()와 함께 사용하여 싱글톤 객체를 생성하거나,
# 라우터에서 필요한 객체들을 간편하게 주입할 수 있도록 도와줌
# 예를 들어, OpenAI 클라이언트나 ChromaDB 클라이언트를 싱글톤으로 생성하여 App 전체에서 공유 가능
# Spring Framework의 @Bean과 유사한 역할을 하는 함수들을 정의하여,
# 라우터에서 간결하게 사용할 수 있도록 타입 별칭도 제공

# ── OpenAI 클라이언트 ──────────────────────────────────────────
@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


# ── ChromaDB 클라이언트 ────────────────────────────────────────
@lru_cache
def get_chroma_client() -> chromadb.AsyncHttpClient:
    settings = get_settings()
    return chromadb.AsyncHttpClient(
        host=settings.chroma_server_host,
        port=settings.chroma_server_http_port,
    )


async def get_chroma_collection(
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[chromadb.AsyncHttpClient, Depends(get_chroma_client)],
):
    """라우터에서 Depends()로 주입받는 ChromaDB 컬렉션."""
    return await client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# ── 타입 별칭 (라우터에서 간결하게 사용) ──────────────────────
SettingsDep = Annotated[Settings, Depends(get_settings)]
OpenAIDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]
ChromaCollectionDep = Annotated[object, Depends(get_chroma_collection)]