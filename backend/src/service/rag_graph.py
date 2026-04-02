from functools import partial

from langgraph.graph import END, START, StateGraph

from service.nodes.rag_nodes import (
    analyze_query,
    generate,
    grade_documents,
    retrieve,
    route_after_grade,
    route_query,
    transform_query,
)
from service.states import RAGState


def build_rag_graph(collection):
    """ChromaDB 컬렉션을 주입받아 RAG Graph를 빌드."""
    builder = StateGraph(RAGState)

    # 노드 등록 (collection 부분 적용)
    builder.add_node("analyze_query", partial(analyze_query, collection=collection))
    builder.add_node("retrieve", partial(retrieve, collection=collection))
    builder.add_node("grade_documents", grade_documents)
    builder.add_node("transform_query", transform_query)
    builder.add_node("generate", generate)

    # 엣지 연결
    builder.add_edge(START, "analyze_query")
    builder.add_conditional_edges("analyze_query", route_query, {
        "retrieve": "retrieve",
        "generate": "generate",
    })
    builder.add_edge("retrieve", "grade_documents")
    builder.add_conditional_edges("grade_documents", route_after_grade, {
        "generate": "generate",
        "transform_query": "transform_query",
    })
    builder.add_edge("transform_query", "retrieve")
    builder.add_edge("generate", END)

    return builder.compile()