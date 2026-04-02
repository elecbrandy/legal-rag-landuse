# from fastapi import APIRouter

# from core.deps import ChromaCollectionDep, OpenAIDep
# from model.exam import (
#     ExamResult,
#     ExamStartRequest,
#     ExamStartResponse,
#     ExamSubmitRequest,
# )
# from service import exam_service

# router = APIRouter(prefix="/exam", tags=["exam"])


# @router.post("/start", response_model=ExamStartResponse)
# async def start_exam(
#     request: ExamStartRequest,
#     collection: ChromaCollectionDep,
#     openai_client: OpenAIDep,
# ) -> ExamStartResponse:
#     """시험 시작 — 법령 기반 문제 생성."""
#     return await exam_service.start_exam(request, collection, openai_client)


# @router.post("/submit", response_model=ExamResult)
# async def submit_exam(
#     request: ExamSubmitRequest,
#     openai_client: OpenAIDep,
# ) -> ExamResult:
#     """답안 제출 — 채점 및 해설 반환."""
#     return await exam_service.submit_exam(request, openai_client)