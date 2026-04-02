from typing import Annotated, Literal
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from src.model.chat import SourceChunk

class RAGState(BaseModel):
    # 대화
    session_id: UUID
    query: str
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)

    # 라우팅
    query_type: Literal["law", "general"] | None = None

    # 검색
    sources: list[SourceChunk] = Field(default_factory=list)
    retrieval_grade: Literal["sufficient", "insufficient"] | None = None
    rewrite_count: int = 0          # 무한 재검색 방지 (최대 2회)

    # 생성
    answer: str = ""
