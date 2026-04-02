from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

# 법령 원문
class LawArticle(BaseModel):
    """법령정보센터에서 가져온 단일 조문"""
    law_id: str             # 법령 ID (법령정보센터 기준)
    law_name: str           # 법령명
    article_number: str     # 조항 번호 (예: 제6조)
    article_title: str      # 조항 제목
    content: str            # 조문 원문


# 청크 (ChromaDB 저장 단위)
class LawChunk(BaseModel):
    """법령 조문을 청크 단위로 분할하여 저장하는 모델"""
    chunk_id: UUID =Field(default_factory=uuid4)    # 고유한 청크 ID
    law_id: str                                     # 법령 ID (법령정보센터 기준)
    law_name: str                                   # 법령명
    article: str                                    # 조항 번호 및 제목 (예: 제6조 - 목적)
    content: str                                    # 청크로 분할된 텍스트
    embedding: list[float] | None = None            # 저장 전까지 None


# Ingest 요청/응답
class IngestRequest(BaseModel):
    """법령 ID 목록을 받아 해당 법령들을 수집 및 청크화하여 ChromaDB에 저장하는 요청 모델"""
    law_ids: list[str] = Field(..., description="수집할 법령 ID 목록")


class IngestResponse(BaseModel):
    """법령 수집 및 청크화 결과를 반환하는 모델"""
    ingested_laws: list[str]
    total_chunks: int
    finished_at: datetime = Field(default_factory=datetime.utcnow)


# 법령 목록 조회
class LawSummary(BaseModel):
    """법령 목록 조회 시 반환되는 법령 요약 정보 모델"""
    law_id: str
    law_name: str
    chunk_count: int


class LawListResponse(BaseModel):
    """법령 목록 조회 시 반환되는 응답 모델"""
    laws: list[LawSummary]
    total: int
