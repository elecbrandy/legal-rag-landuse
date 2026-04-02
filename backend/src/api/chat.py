from uuid import UUID

from fastapi import APIRouter

from core.deps import ChromaCollectionDep, OpenAIDep
from model.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from repsitory import chat_repository
from service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    collection: ChromaCollectionDep,
    openai_client: OpenAIDep,
) -> ChatResponse:
    """
    사용자 질문에 대해 RAG 기반 답변 반환
    Args:
        request (ChatRequest): 사용자 질문과 세션 정보
        collection: ChromaDB 컬렉션 객체 (의존성 주입)
        openai_client: OpenAI 비동기 클라이언트 (의존성 주입)
    Returns:
        ChatResponse: 생성된 답변과 관련 정보
    """
    return await rag_service.answer(request, collection, openai_client)


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: UUID) -> ChatHistoryResponse:
    """
    세션 ID로 대화 히스토리 조회
    Args:
        session_id (UUID): 세션 ID
    Returns:
        ChatHistoryResponse: 대화 히스토리
    """
    messages = await chat_repository.get_history(session_id)
    return ChatHistoryResponse(session_id=session_id, messages=messages)


@router.delete("/history/{session_id}")
async def delete_history(session_id: UUID) -> dict:
    """
    세션 대화 히스토리 삭제
    Args:
        session_id (UUID): 세션 ID
    Returns:
        dict: 삭제된 메시지 수
    """
    deleted = await chat_repository.delete_session(session_id)
    return {"deleted_count": deleted}