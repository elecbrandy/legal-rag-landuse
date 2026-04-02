import re

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from src.core.config import get_settings
from src.ingestion.embedder import embed_query
from src.model.chat import ChatMessage, ChatRequest, ChatResponse, SourceChunk
from src.repository import chat_repository, vector_repository

settings = get_settings()

SYSTEM_PROMPT = """당신은 대한민국 부동산공법 전문 AI 어시스턴트입니다.

[행동 규칙]
1. 반드시 search_law 툴을 호출해 관련 법령 조문을 검색한 뒤 답변하세요.
2. 검색 결과가 질문에 불충분하다면, 다른 키워드로 search_law를 재호출하세요. (최대 2회)
3. 답변 마지막에는 반드시 근거 조항을 명시하세요. (예: 근거: 국토계획법 제6조)
4. 조문에 없는 내용은 "해당 내용은 제공된 법령에서 확인할 수 없습니다"라고 답하세요.
""".strip()

# 프론트엔드 셀렉터에 노출할 모델 목록
AVAILABLE_MODELS = {
    "gpt-4o":        "openai:gpt-4o",
    "gpt-4o-mini":   "openai:gpt-4o-mini",
    "gpt-4.1":       "openai:gpt-4.1",
    "gpt-4.1-mini":  "openai:gpt-4.1-mini",
}
DEFAULT_MODEL = f"openai:{settings.llm_model}"


def build_law_search_tool(collection, openai_client):
    @tool
    async def search_law(query: str) -> str:
        """
        부동산공법 관련 법령 조문을 벡터 검색.
        질문과 관련된 법령 키워드를 query 로 전달해야함.
        예: '건폐율 정의', '용도지역 종류', '개발행위허가 기준'
        """
        query_embedding = await embed_query(query, openai_client)
        sources: list[SourceChunk] = await vector_repository.search(
            query_embedding=query_embedding,
            collection=collection,
        )
        if not sources:
            return "관련 법령 조문을 찾을 수 없습니다."
        return "\n\n---\n\n".join(
            f"[{s.law_name} {s.article}] (유사도: {s.score:.2f})\n{s.content}"
            for s in sources
        )

    return search_law


def build_agent(collection, openai_client):
    """
    LangChain 1.0 configurable 에이전트 빌드
    """
    configurable_model = init_chat_model(
        model=DEFAULT_MODEL, 
        api_key=settings.openai_api_key
    )

    return create_agent(
        model=configurable_model,
        tools=[build_law_search_tool(collection, openai_client)],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            SummarizationMiddleware(
                model=configurable_model,
                max_tokens_before_summary=3000,
                messages_to_keep=6,
            ),
        ],
    )

_agent_cache: dict = {}

def get_agent(collection, openai_client):
    key = id(collection)
    if key not in _agent_cache:
        _agent_cache[key] = build_agent(collection, openai_client)
    return _agent_cache[key]


async def answer(
    request: ChatRequest,
    collection,
    openai_client,
    model: str = DEFAULT_MODEL,
) -> ChatResponse:
    # 1. 히스토리 로드 → LangChain 메시지 변환
    history = await chat_repository.get_history(request.session_id)
    messages = []
    for msg in history:
        messages.append(
            HumanMessage(content=msg.content)
            if msg.role == "user"
            else AIMessage(content=msg.content)
        )
    messages.append(HumanMessage(content=request.message))

    # 2. 싱글톤 에이전트
    agent = get_agent(collection, openai_client)

    # 3. 실행 — config 로 모델 런타임 주입 (LangChain 1.0 핵심 패턴)
    result = await agent.ainvoke(
        {"messages": messages},
        config={"configurable": {"model": model}},
    )

    # 4. 최종 AIMessage 추출
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    answer_text = ai_messages[-1].content if ai_messages else "답변을 생성할 수 없습니다."

    # 5. 대화 저장
    await chat_repository.save_message(
        ChatMessage(session_id=request.session_id, role="user", content=request.message)
    )
    await chat_repository.save_message(
        ChatMessage(session_id=request.session_id, role="assistant", content=answer_text)
    )

    return ChatResponse(
        session_id=request.session_id,
        answer=answer_text,
        sources=_extract_sources(result["messages"]),
    )


def _extract_sources(messages: list) -> list[SourceChunk]:
    sources: list[SourceChunk] = []
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            for block in (msg.content or "").split("\n\n---\n\n"):
                block = block.strip()
                if not block or "찾을 수 없습니다" in block:
                    continue
                first_line, _, body = block.partition("\n")
                law_name, article, score = _parse_header(first_line)
                sources.append(SourceChunk(
                    law_name=law_name, article=article,
                    content=body.strip(), score=score,
                ))
    return sources


def _parse_header(header: str) -> tuple[str, str, float]:
    score = 0.0
    if m := re.search(r"유사도:\s*([\d.]+)", header):
        score = float(m.group(1))
    if bm := re.match(r"\[(.+?)\]", header):
        parts = bm.group(1).rsplit(" ", 1)
        return (parts[0], parts[1], score) if len(parts) == 2 else (parts[0], "", score)
    return header, "", score