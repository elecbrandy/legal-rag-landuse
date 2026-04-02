from fastapi import APIRouter, HTTPException
from src.core.deps import ChromaCollectionDep, OpenAIDep
from src.model.law import IngestByNameRequest
from src.ingestion.embedder import embed_and_store
from src.ingestion.law_fetcher import fetch_law_articles, search_law_id_by_name
from src.ingestion.text_splitter import split_articles
from src.model.law import IngestRequest, IngestResponse, LawListResponse
from src.repository import vector_repository

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

@router.post("/ingest/names", response_model=IngestResponse)
async def ingest_laws_by_names(
    request: IngestByNameRequest,
    collection: ChromaCollectionDep,
    openai_client: OpenAIDep,
) -> IngestResponse:
    """
    법령명 목록으로 MST를 검색한 뒤 데이터 수집 → 임베딩 → ChromaDB 저장
    Args:
        request (IngestByNameRequest): 법령명 목록
        collection: ChromaDB 컬렉션 객체
        openai_client: OpenAI 비동기 클라이언트
    Returns:
        IngestResponse: 수집된 법령명 목록과 총 청크 수
    """
    ingested_laws: list[str] = []
    total_chunks = 0

    for name in request.law_names:
        try:
            # 1. 이름으로 MST 검색
            mst = await search_law_id_by_name(name)
            if not mst:
                print(f"❌ {name}: 검색 결과 없음")
                continue
                
            # 2. 기존 수집 로직 재사용
            articles = await fetch_law_articles(mst)
            chunks = split_articles(articles)
            stored = await embed_and_store(chunks, collection, openai_client)

            ingested_laws.append(name)
            total_chunks += stored
            print(f"✅ {name}: MST={mst} 수집 완료")
            
        except Exception as e:
            # 중간에 하나 실패해도 나머지 법령은 계속 수집되도록 예외 처리
            print(f"⚠️ 법령 '{name}' 수집 실패: {str(e)}")

    return IngestResponse(ingested_laws=ingested_laws, total_chunks=total_chunks)