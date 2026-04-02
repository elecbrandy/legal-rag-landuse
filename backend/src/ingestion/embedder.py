import asyncio

from openai import AsyncOpenAI
from src.core.config import get_settings
from src.model.law import LawChunk

settings = get_settings()

EMBED_BATCH_SIZE = 100   # OpenAI 임베딩 API 한 번에 보낼 청크 수


async def embed_and_store(
    chunks: list[LawChunk],
    collection,                 # chromadb Collection
    openai_client: AsyncOpenAI,
) -> int:
    """
    청크 임베딩 후 ChromaDB에 저장. 저장된 청크 수 반환
    Args:
        chunks (list[LawChunk]): 임베딩할 청크 리스트
        collection: ChromaDB 컬렉션 객체
        openai_client (AsyncOpenAI): OpenAI 비동기 클라이언트
    Returns:
        int: 저장된 청크 수
    """
    stored = 0
    for batch in _batched(chunks, EMBED_BATCH_SIZE):
        texts = [c.content for c in batch]

        # 임베딩 생성
        resp = await openai_client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        embeddings = [item.embedding for item in resp.data]

        # ChromaDB 저장
        await collection.upsert(
            ids=[str(c.chunk_id) for c in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "law_id": c.law_id,
                    "law_name": c.law_name,
                    "article": c.article,
                }
                for c in batch
            ],
        )
        stored += len(batch)

    return stored


async def embed_query(query: str, openai_client: AsyncOpenAI) -> list[float]:
    """
    검색 쿼리 임베딩
    Args:
        query (str): 검색 쿼리
        openai_client (AsyncOpenAI): OpenAI 비동기 클라이언트
    Returns:
        list[float]: 임베딩 벡터
    """
    resp = await openai_client.embeddings.create(
        model=settings.embedding_model,
        input=[query],
    )
    return resp.data[0].embedding


def _batched(items: list, size: int):
    """
    리스트를 size 단위로 나눠 yield
    Args:
        items (list): 나눌 리스트
        size (int): 배치 크기
    Yields:
        list: size 크기의 리스트 조각
    """
    for i in range(0, len(items), size):
        yield items[i : i + size]