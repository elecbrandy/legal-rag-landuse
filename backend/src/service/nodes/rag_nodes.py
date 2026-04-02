from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.config import get_settings
from ingestion.embedder import embed_query
from repsitory import vector_repository
from service.states import RAGState

settings = get_settings()
llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.3,
    api_key=settings.openai_api_key,
)

MAX_REWRITE = 2  # 최대 쿼리 재작성 횟수

SYSTEM_PROMPT = """
당신은 대한민국 부동산공법 전문 AI 어시스턴트입니다.
반드시 제공된 법령 조문을 근거로 답변하고, 마지막에 근거 조항을 명시하세요.
조문에 없는 내용은 "해당 내용은 제공된 법령에서 확인할 수 없습니다"라고 답하세요.
""".strip()


# 노드 1: 쿼리 분석
async def analyze_query(state: RAGState, collection) -> dict:
    """질문이 법령 조회인지 일반 QA인지 분류."""
    prompt = f"""
다음 질문을 분류하세요.
- "law": 특정 법령 조문, 규정, 요건을 묻는 질문
- "general": 개념 설명, 절차 안내 등 일반적인 질문

질문: {state.query}
반드시 "law" 또는 "general" 중 하나만 답하세요.
""".strip()

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    query_type = "law" if "law" in resp.content.lower() else "general"
    return {"query_type": query_type}


# 노드 2: 라우팅 (엣지 조건 함수)
def route_query(state: RAGState) -> Literal["retrieve", "generate"]:
    """query_type에 따라 검색 or 직접 생성으로 분기."""
    return "retrieve" if state.query_type == "law" else "generate"


# 노드 3: 검색
async def retrieve(state: RAGState, collection) -> dict:
    """ChromaDB에서 유사 청크 검색."""
    query_embedding = await embed_query(state.query, None)  # client는 collection에 포함
    sources = await vector_repository.search(
        query_embedding=query_embedding,
        collection=collection,
    )
    return {"sources": sources}


# 노드 4: 검색 결과 품질 판단
async def grade_documents(state: RAGState) -> dict:
    """검색된 청크가 질문에 충분한지 LLM으로 판단."""
    if not state.sources:
        return {"retrieval_grade": "insufficient"}

    context = "\n".join(s.content[:200] for s in state.sources)
    prompt = f"""
질문: {state.query}
검색된 법령 내용 요약:
{context}

위 내용이 질문에 답하기 충분합니까?
반드시 "sufficient" 또는 "insufficient" 중 하나만 답하세요.
""".strip()

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    grade = "sufficient" if "sufficient" in resp.content.lower() else "insufficient"
    return {"retrieval_grade": grade}


# ── 노드 4 이후 라우팅 (엣지 조건 함수) ───────────────────────
def route_after_grade(state: RAGState) -> Literal["generate", "transform_query"]:
    """품질 충분 → 생성 / 부족 + 재작성 한도 미만 → 쿼리 재작성."""
    if state.retrieval_grade == "sufficient":
        return "generate"
    if state.rewrite_count >= MAX_REWRITE:
        return "generate"  # 한도 초과 시 있는 것으로 생성
    return "transform_query"


# ── 노드 5: 쿼리 재작성 ───────────────────────────────────────
async def transform_query(state: RAGState) -> dict:
    """검색 결과가 부족할 때 쿼리를 법령 검색에 최적화된 형태로 재작성."""
    prompt = f"""
다음 질문을 법령 검색에 최적화된 형태로 재작성하세요.
법령 용어와 조항 키워드를 포함하세요.

원래 질문: {state.query}
재작성된 질문만 출력하세요.
""".strip()

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {
        "query": resp.content.strip(),
        "rewrite_count": state.rewrite_count + 1,
    }


# ── 노드 6: 답변 생성 ─────────────────────────────────────────
async def generate(state: RAGState) -> dict:
    """검색된 법령 조문 기반으로 최종 답변 생성."""
    context = "\n\n".join(
        f"[{s.law_name} {s.article}]\n{s.content}" for s in state.sources
    )

    # 이전 대화 히스토리 포함
    messages = [HumanMessage(content=SYSTEM_PROMPT)]
    messages.extend(state.messages)
    messages.append(HumanMessage(
        content=f"[관련 법령]\n{context}\n\n[질문]\n{state.query}"
        if context else state.query
    ))

    resp = await llm.ainvoke(messages)
    answer = resp.content.strip()

    return {
        "answer": answer,
        "messages": [
            HumanMessage(content=state.query),
            AIMessage(content=answer),
        ],
    }