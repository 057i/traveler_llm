"""
AI Recommendation Workflow - Graph Builder
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from .state import AIRecommendState
from .nodes import (
    query_rewriter_node,
    parallel_retrieval_node,
    rrf_fusion_node,
    confidence_check_node,
    tavily_search_node,
    rrf_fusion_with_tavily_node,
    rerank_node,
    synthesizer_node
)


def build_ai_recommend_graph():
    """
    Build AI recommendation workflow graph

    Flow:
    START
      -> query_rewriter (query rewrite + entity extraction)
      -> parallel_retrieval (ChromaDB + Neo4j parallel search)
      -> rrf_fusion (RRF fusion)
      -> confidence_check (confidence score check)
      -> tavily_search (optional web search if confidence is low)
      -> rrf_fusion_with_tavily (merge web results)
      -> rerank (rerank results)
      -> synthesizer (LLM generate answer)
      -> END
    """
    logger.info("[GraphBuilder] Building AI recommendation workflow graph")

    workflow = StateGraph(AIRecommendState)

    workflow.add_node("query_rewriter", query_rewriter_node)
    workflow.add_node("parallel_retrieval", parallel_retrieval_node)
    workflow.add_node("rrf_fusion", rrf_fusion_node)
    workflow.add_node("confidence_check", confidence_check_node)
    workflow.add_node("tavily_search", tavily_search_node)
    workflow.add_node("rrf_fusion_with_tavily", rrf_fusion_with_tavily_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("query_rewriter")

    workflow.add_edge("query_rewriter", "parallel_retrieval")
    workflow.add_edge("parallel_retrieval", "rrf_fusion")
    workflow.add_edge("rrf_fusion", "confidence_check")
    workflow.add_edge("confidence_check", "tavily_search")
    workflow.add_edge("tavily_search", "rrf_fusion_with_tavily")
    workflow.add_edge("rrf_fusion_with_tavily", "rerank")
    workflow.add_edge("rerank", "synthesizer")
    workflow.add_edge("synthesizer", END)

    app = workflow.compile()

    logger.success("[GraphBuilder] AI recommendation workflow graph built successfully")
    logger.info("[GraphBuilder] Total nodes: 8")
    logger.info("[GraphBuilder] Flow: Rewrite -> Parallel -> RRF1 -> Confidence -> [Tavily] -> RRF2 -> Rerank -> Synthesize")

    return app


_workflow_instance = None


def get_ai_recommend_workflow():
    """Get AI recommendation workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = build_ai_recommend_graph()
    return _workflow_instance
