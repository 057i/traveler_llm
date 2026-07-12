"""
AI Recommendation Workflow - Node: Rerank

Rerank results using BGE Reranker model
"""
from loguru import logger

from ..state import AIRecommendState


async def rerank_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Rerank results

    Uses bge-reranker-v2-m3 for deep semantic reranking
    """
    logger.info("=" * 80)
    logger.info("[Rerank] Starting reranking")
    logger.info("=" * 80)

    rrf_results = state.get("rrf_results", [])
    query = state.get("query", "")

    logger.info(f"[Rerank] Input: {len(rrf_results)} results")

    if not rrf_results:
        logger.warning("[Rerank] No results to rerank")
        state["reranked_results"] = []
        logger.info("=" * 80)
        logger.success("[Rerank] Node completed")
        logger.info("=" * 80)
        return state

    try:
        from app.core.rerank_client import get_rerank_engine
        from app.models.schemas import QueryRequest

        rerank_engine = get_rerank_engine()

        query_request = QueryRequest(query=query)

        # Perform reranking
        reranked = await rerank_engine.rerank(
            query_request=query_request,
            candidates=rrf_results
        )

        state["reranked_results"] = reranked
        logger.success(f"[Rerank] Reranking completed: {len(reranked)} results")

        if reranked:
            logger.info(f"[Rerank] Top result score: {reranked[0].get('score', 0):.4f}")

    except Exception as e:
        logger.error(f"[Rerank] Reranking failed: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: use RRF results
        state["reranked_results"] = rrf_results

    logger.info("=" * 80)
    logger.success("[Rerank] Node completed")
    logger.info("=" * 80)

    return state
