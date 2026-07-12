"""
AI Recommendation Workflow - Node: RRF Fusion

Fuse results from Milvus and Neo4j using Reciprocal Rank Fusion
"""
from loguru import logger

from ..state import AIRecommendState


async def rrf_fusion_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: RRF fusion of Milvus and Neo4j results

    Uses Reciprocal Rank Fusion algorithm with score scaling
    """
    logger.info("=" * 80)
    logger.info("[RRFFusion] Starting RRF fusion")
    logger.info("=" * 80)

    milvus_results = state.get("milvus_results", [])
    neo4j_results = state.get("neo4j_results", [])

    logger.info(f"[RRFFusion] Input: Milvus {len(milvus_results)}, Neo4j {len(neo4j_results)}")

    try:
        from app.core.rrf_client import get_rrf_engine

        rrf_engine = get_rrf_engine()

        fused_results = await rrf_engine.fuse(
            vector_results=milvus_results,
            graph_results=neo4j_results if neo4j_results else None,
            top_k=10
        )

        state["rrf_results"] = fused_results
        logger.success(f"[RRFFusion] RRF fusion completed: {len(fused_results)} results")

        if fused_results:
            logger.info(f"[RRFFusion] Top result score: {fused_results[0].get('score', 0):.4f}")

    except Exception as e:
        logger.error(f"[RRFFusion] Fusion failed: {e}")
        state["rrf_results"] = milvus_results

    logger.info("=" * 80)
    logger.success("[RRFFusion] Node completed")
    logger.info("=" * 80)

    return state
