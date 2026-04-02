from typing import Annotated
import chromadb
from fastapi import Depends
from openai import AsyncOpenAI
from src.core.config import Settings, get_settings

_openai_client: AsyncOpenAI | None = None

def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


# ── ChromaDB: AsyncHttpClient는 await 필요 → 전역 캐싱 ────────
_chroma_client: chromadb.AsyncClientAPI | None = None

async def get_chroma_client() -> chromadb.AsyncClientAPI:
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = await chromadb.AsyncHttpClient(
            host=settings.chroma_server_host,
            port=settings.chroma_server_http_port,
        )
    return _chroma_client


async def get_chroma_collection(
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[chromadb.AsyncClientAPI, Depends(get_chroma_client)],
):
    return await client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# 타입 별칭 정의
SettingsDep = Annotated[Settings, Depends(get_settings)]
OpenAIDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]
ChromaCollectionDep = Annotated[object, Depends(get_chroma_collection)]