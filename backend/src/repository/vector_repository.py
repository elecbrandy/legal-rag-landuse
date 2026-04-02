from src.model.law import LawChunk, LawSummary
from src.model.chat import SourceChunk

TOP_K = 5  # 기본 검색 결과 수

async def search(
    query_embedding: list[float],
    collection,
    top_k: int = TOP_K,
    law_id: str | None = None,  # 특정 법령만 검색 시 사용
) -> list[SourceChunk]:
    """
    쿼리 임베딩으로 유사 청크 검색
    Args:
        query_embedding (list[float]): 검색 쿼리 임베딩 벡터
        collection: ChromaDB 컬렉션 객체
        top_k (int): 반환할 유사 청크 수
        law_id (str | None): 특정 법령 ID로 검색 범위 제한 (선택 사항)
    Returns:
        list[SourceChunk]: 유사 청크 리스트
    """
    where = {"law_id": law_id} if law_id else None

    results = await collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[SourceChunk] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            SourceChunk(
                law_name=meta.get("law_name", ""),
                article=meta.get("article", ""),
                content=doc,
                score=round(1 - dist, 4),  # cosine distance → similarity
            )
        )

    return chunks


async def list_laws(collection) -> list[LawSummary]:
    """
    ChromaDB에 저장된 법령 목록과 청크 수 반환
    Args:
        collection: ChromaDB 컬렉션 객체
    Returns:
        list[LawSummary]: 법령 요약 리스트
    """
    result = await collection.get(include=["metadatas"])
    metadatas = result.get("metadatas", [])

    # law_id 기준으로 집계
    law_map: dict[str, LawSummary] = {}
    for meta in metadatas:
        law_id = meta.get("law_id", "")
        if law_id not in law_map:
            law_map[law_id] = LawSummary(
                law_id=law_id,
                law_name=meta.get("law_name", ""),
                chunk_count=0,
            )
        law_map[law_id].chunk_count += 1

    return list(law_map.values())


async def delete_law(law_id: str, collection) -> int:
    """
    특정 법령의 청크 전체 삭제. 삭제된 청크 수 반환.
    Args:
        law_id (str): 삭제할 법령 ID
        collection: ChromaDB 컬렉션 객체
    Returns:
        int: 삭제된 청크 수
    """
    result = await collection.get(
        where={"law_id": law_id},
        include=[],
    )
    ids = result.get("ids", [])
    if ids:
        await collection.delete(ids=ids)
    return len(ids)