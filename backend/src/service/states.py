from typing import Annotated, Literal
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from model.chat import SourceChunk
from model.exam import ExamQuestion, ExamAnswerResult, Difficulty

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

class ExamState(BaseModel):
    # 설정
    topic: str
    num_questions: int = 10
    difficulty: Difficulty = Difficulty.MEDIUM

    # 문제 생성
    context: list[SourceChunk] = Field(default_factory=list)
    questions: list[ExamQuestion] = Field(default_factory=list)
    validation_passed: bool = False
    generate_retry: int = 0         # 문제 재생성 방지 (최대 2회)

    # 채점
    answers: list[dict] = Field(default_factory=list)   # ExamAnswer 직렬화
    results: list[ExamAnswerResult] = Field(default_factory=list)
    score: float = 0.0
    feedback: str = ""