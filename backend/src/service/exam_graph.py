from functools import partial

from langgraph.graph import END, START, StateGraph

from service.nodes.exam_nodes import (
    generate_feedback,
    generate_questions,
    grade_answers,
    increment_retry,
    retrieve_context,
    route_after_validation,
    validate_questions,
)
from service.states import ExamState


def build_exam_graph(collection):
    """ChromaDB 컬렉션을 주입받아 Exam Graph를 빌드."""
    builder = StateGraph(ExamState)

    # 노드 등록
    builder.add_node("retrieve_context", partial(retrieve_context, collection=collection))
    builder.add_node("generate_questions", generate_questions)
    builder.add_node("validate_questions", validate_questions)
    builder.add_node("increment_retry", increment_retry)
    builder.add_node("grade_answers", grade_answers)
    builder.add_node("generate_feedback", generate_feedback)

    # 문제 생성 흐름
    builder.add_edge(START, "retrieve_context")
    builder.add_edge("retrieve_context", "generate_questions")
    builder.add_edge("generate_questions", "validate_questions")
    builder.add_conditional_edges("validate_questions", route_after_validation, {
        "done": "grade_answers",        # 답안이 없으면 grade_answers에서 빈 결과 반환
        "regenerate": "increment_retry",
    })
    builder.add_edge("increment_retry", "generate_questions")

    # 채점 흐름
    builder.add_edge("grade_answers", "generate_feedback")
    builder.add_edge("generate_feedback", END)

    return builder.compile()