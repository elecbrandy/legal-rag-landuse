from uuid import UUID
from fastapi import APIRouter, Query
from src.core.deps import ChromaCollectionDep, OpenAIDep
from src.model.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from src.repository import chat_repository
from src.service import rag_service
from src.service.rag_service import AVAILABLE_MODELS, DEFAULT_MODEL

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/models")
async def list_models() -> dict:
    """사용 가능한 모델 목록 반환."""
    return {"models": AVAILABLE_MODELS, "default": DEFAULT_MODEL}


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    collection: ChromaCollectionDep,
    openai_client: OpenAIDep,
    model: str = Query(default=DEFAULT_MODEL, description="사용할 LLM 모델"),
) -> ChatResponse:
    """
    RAG 기반 답변 반환.
    model 쿼리 파라미터로 런타임 모델 교체 가능.
    예: POST /chat?model=openai:gpt-4o-mini
    """
    return await rag_service.answer(request, collection, openai_client, model=model)


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: UUID) -> ChatHistoryResponse:
    messages = await chat_repository.get_history(session_id)
    return ChatHistoryResponse(session_id=session_id, messages=messages)


@router.delete("/history/{session_id}")
async def delete_history(session_id: UUID) -> dict:
    deleted = await chat_repository.delete_session(session_id)
    return {"deleted_count": deleted}