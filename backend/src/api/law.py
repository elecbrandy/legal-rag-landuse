from fastapi import APIRouter, HTTPException

from core.deps import ChromaCollectionDep, OpenAIDep
from ingestion.embedder import embed_and_store
from ingestion.law_fetcher import fetch_law_articles
from ingestion.text_splitter import split_articles
from model.law import IngestRequest, IngestResponse, LawListResponse
from repsitory import vector_repository

router = APIRouter(prefix="/law", tags=["law"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_laws(
    request: IngestRequest,
    collection: ChromaCollectionDep,
    openai_client: OpenAIDep,
) -> IngestResponse:
    """
    법령 ID 목록으로 데이터 수집 → 임베딩 → ChromaDB 저장
    Args:
        request (IngestRequest): 법령 ID 목록
        collection: ChromaDB 컬렉션 객체
        openai_client: OpenAI 비동기 클라이언트
    Returns:
        IngestResponse: 수집된 법령 목록과 총 청크 수
    """
    ingested_laws: list[str] = []
    total_chunks = 0

    for law_id in request.law_ids:
        try:
            articles = await fetch_law_articles(law_id)
            chunks = split_articles(articles)
            stored = await embed_and_store(chunks, collection, openai_client)

            ingested_laws.append(law_id)
            total_chunks += stored
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"법령 {law_id} 수집 실패: {str(e)}",
            )

    return IngestResponse(ingested_laws=ingested_laws, total_chunks=total_chunks)


@router.get("/list", response_model=LawListResponse)
async def list_laws(collection: ChromaCollectionDep) -> LawListResponse:
    """
    ChromaDB에 저장된 법령 목록 조회
    Args:
        collection: ChromaDB 컬렉션 객체
    Returns:
        LawListResponse: 법령 목록과 총 수
    """
    laws = await vector_repository.list_laws(collection)
    return LawListResponse(laws=laws, total=len(laws))


@router.delete("/{law_id}")
async def delete_law(law_id: str, collection: ChromaCollectionDep) -> dict:
    """
    특정 법령 청크 전체 삭제
    Args:
        law_id (str): 법령 ID
        collection: ChromaDB 컬렉션 객체
    Returns:
        dict: 삭제된 청크 수
    """
    deleted = await vector_repository.delete_law(law_id, collection)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"법령 {law_id} 를 찾을 수 없습니다.")
    return {"law_id": law_id, "deleted_chunks": deleted}