import json
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from core.config import get_settings
from ingestion.embedder import embed_query
from model.exam import (
    Difficulty,
    ExamAnswerResult,
    ExamChoice,
    ExamQuestion,
)
from repsitory import vector_repository
from service.states import ExamState

settings = get_settings()
llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.7,
    api_key=settings.openai_api_key,
)
llm_strict = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.2,
    api_key=settings.openai_api_key,
)

MAX_RETRY = 2

QUESTION_PROMPT = """
다음 법령 조문을 바탕으로 부동산공법 5지선다 문제를 {num}개 생성하세요.
난이도: {difficulty}

[법령 조문]
{context}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "questions": [
    {{
      "question": "문제 내용",
      "choices": [
        {{"number": 1, "content": "선택지"}},
        {{"number": 2, "content": "선택지"}},
        {{"number": 3, "content": "선택지"}},
        {{"number": 4, "content": "선택지"}},
        {{"number": 5, "content": "선택지"}}
      ],
      "correct": 정답번호,
      "law_reference": "근거 법령 및 조항",
      "explanation": "해설"
    }}
  ]
}}
""".strip()


# 노드 1: 관련 법령 검색
async def retrieve_context(state: ExamState, collection) -> dict:
    """시험 주제로 관련 법령 청크 검색."""
    query_embedding = await embed_query(state.topic, None)
    sources = await vector_repository.search(
        query_embedding=query_embedding,
        collection=collection,
        top_k=10,
    )
    return {"context": sources}


# 노드 2: 문제 생성
async def generate_questions(state: ExamState) -> dict:
    """법령 컨텍스트 기반 문제 생성."""
    context = "\n\n".join(
        f"[{s.law_name} {s.article}]\n{s.content}" for s in state.context
    )
    prompt = QUESTION_PROMPT.format(
        num=state.num_questions,
        difficulty=state.difficulty.value,
        context=context,
    )
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    questions = _parse_questions(resp.content, state.difficulty)
    return {"questions": questions}


# 노드 3: 문제 품질 검증
async def validate_questions(state: ExamState) -> dict:
    """생성된 문제가 법령 근거가 있고 명확한지 검증."""
    if not state.questions:
        return {"validation_passed": False}

    sample = state.questions[0]
    prompt = f"""
다음 부동산공법 문제가 적절한지 판단하세요.
- 법령 근거가 명확한가
- 선택지가 5개인가
- 문제가 모호하지 않은가

문제: {sample.question}
근거: {sample.law_reference}

반드시 "pass" 또는 "fail" 중 하나만 답하세요.
""".strip()

    resp = await llm_strict.ainvoke([HumanMessage(content=prompt)])
    passed = "pass" in resp.content.lower()
    return {"validation_passed": passed}


# ── 노드 3 이후 라우팅 ────────────────────────────────────────
def route_after_validation(state: ExamState) -> Literal["done", "regenerate"]:
    if state.validation_passed:
        return "done"
    if state.generate_retry >= MAX_RETRY:
        return "done"  # 한도 초과 시 현재 문제 사용
    return "regenerate"


def increment_retry(state: ExamState) -> dict:
    return {"generate_retry": state.generate_retry + 1}


# ── 노드 4: 답안 채점 ─────────────────────────────────────────
async def grade_answers(state: ExamState) -> dict:
    """제출된 답안 채점."""
    q_map = {str(q.question_id): q for q in state.questions}
    results: list[ExamAnswerResult] = []
    correct_count = 0

    for answer in state.answers:
        q = q_map.get(str(answer["question_id"]))
        if not q:
            continue

        correct_num: int = getattr(q, "_correct", 1)
        is_correct = answer["selected"] == correct_num
        if is_correct:
            correct_count += 1

        results.append(ExamAnswerResult(
            question_id=answer["question_id"],
            question=q.question,
            selected=answer["selected"],
            correct=correct_num,
            is_correct=is_correct,
            explanation=getattr(q, "_explanation", ""),
            law_reference=q.law_reference,
        ))

    score = round(correct_count / len(results) * 100, 1) if results else 0.0
    return {"results": results, "score": score}


# ── 노드 5: 피드백 생성 ───────────────────────────────────────
async def generate_feedback(state: ExamState) -> dict:
    """점수와 오답 분석 기반 종합 피드백 생성."""
    wrong = [r for r in state.results if not r.is_correct]
    wrong_summary = "\n".join(
        f"- {r.question} (근거: {r.law_reference})" for r in wrong[:5]
    )

    prompt = f"""
부동산공법 시험 결과를 바탕으로 학습 피드백을 작성하세요.
점수: {state.score}점 ({len([r for r in state.results if r.is_correct])}/{len(state.results)}문항)
틀린 문제 요약:
{wrong_summary if wrong_summary else "없음 (전부 정답)"}

학습 방향과 취약 법령을 포함한 피드백을 3~5문장으로 작성하세요.
""".strip()

    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"feedback": resp.content.strip()}


# ── 유틸 ──────────────────────────────────────────────────────
def _parse_questions(raw: str, difficulty: Difficulty) -> list[ExamQuestion]:
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    data = json.loads(cleaned)
    questions: list[ExamQuestion] = []
    for item in data.get("questions", []):
        q = ExamQuestion(
            question=item["question"],
            choices=[ExamChoice(**c) for c in item["choices"]],
            law_reference=item.get("law_reference", ""),
            difficulty=difficulty,
        )
        object.__setattr__(q, "_correct", item.get("correct", 1))
        object.__setattr__(q, "_explanation", item.get("explanation", ""))
        questions.append(q)
    return questions