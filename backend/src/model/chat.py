from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

MIN_MESSAGE_LENGTH = 1
MAX_MESSAGE_LENGTH = 2000

# Request 
class ChatRequest(BaseModel):
    """클라이언트에서 서버로 전송되는 채팅 Request"""

    # 세션 ID는 클라이언트에서 제공하거나, 제공하지 않으면 서버에서 새로 생성
    session_id: UUID = Field(default_factory=uuid4)

    # 사용자 메시지 (길이 제한)
    message: str = Field(
        ...,
        min_length=MIN_MESSAGE_LENGTH,
        max_length=MAX_MESSAGE_LENGTH
    )

# Response
class SourceChunk(BaseModel):
    """RAG 검색 결과 출처 청크"""
    law_name: str           # 법령명 (예: 국토의 계획 및 이용에 관한 법률)
    article: str            # 조항 (예: 제6조)
    content: str            # 청크 원문
    score: float            # 유사도 점수 (0~1)

class ChatResponse(BaseModel):
    """서버에서 클라이언트로 전송되는 채팅 Response"""
    session_id: UUID
    answer: str
    sources: list[SourceChunk] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# History 
class ChatMessage(BaseModel):
    """SQLite에 저장되는 단일 메시지."""
    id: int | None = None
    session_id: UUID
    role: str # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatHistoryResponse(BaseModel):
    """특정 세션의 전체 채팅 기록을 반환하는 Response"""
    session_id: UUID
    messages: list[ChatMessage]