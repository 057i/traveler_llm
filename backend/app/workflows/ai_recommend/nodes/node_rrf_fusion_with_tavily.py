"""
AI Recommendation Workflow - Node: RRF Fusion with Tavily

Second RRF fusion including Tavily web search results
"""
from loguru import logger

from ..state import AIRecommendState


async def rrf_fusion_with_tavily_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: RRF fusion with Tavily results

    Fuses previous RRF results with Tavily web search results
    """
    logger.info("=" * 80)
    logger.info("[RRFFusionWithTavily] Starting fusion with Tavily")
    logger.info("=" * 80)

    rrf_results = state.get("rrf_results", [])
    tavily_results = state.get("tavily_results")

    if not tavily_results:
        logger.info("[RRFFusionWithTavily] No Tavily results, skipping")
        logger.info("=" * 80)
        logger.success("[RRFFusionWithTavily] Node completed")
        logger.info("=" * 80)
        return state

    logger.info(f"[RRFFusionWithTavily] Input: RRF {len(rrf_results)}, Tavily {len(tavily_results)}")

    try:
        from app.core.rrf_client import get_rrf_engine

        rrf_engine = get_rrf_engine()

        # Convert to compatible format
        all_results = rrf_results + tavily_results

        # Perform second RRF fusion
        fused_results = await rrf_engine.fuse(
            vector_results=all_results,
            graph_results=None,
            top_k=10
        )

        state["rrf_results"] = fused_results
        logger.success(f"[RRFFusionWithTavily] Fusion completed: {len(fused_results)} results")

    except Exception as e:
        logger.error(f"[RRFFusionWithTavily] Fusion failed: {e}")
        # Keep original results
        pass

    logger.info("=" * 80)
    logger.success("[RRFFusionWithTavily] Node completed")
    logger.info("=" * 80)

    return state
