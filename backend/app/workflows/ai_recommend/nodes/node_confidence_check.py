"""
AI Recommendation Workflow - Node: Confidence Check

Check confidence of retrieval results to decide if web search is needed
"""
from loguru import logger

from ..state import AIRecommendState


async def confidence_check_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Confidence check

    Evaluates retrieval quality and decides if Tavily search is needed
    """
    logger.info("=" * 80)
    logger.info("[ConfidenceCheck] Starting confidence check")
    logger.info("=" * 80)

    rrf_results = state.get("rrf_results", [])

    if rrf_results:
        scores = []
        for r in rrf_results:
            if hasattr(r, 'score'):
                scores.append(r.score)
            elif isinstance(r, dict):
                scores.append(r.get("score", 0) or r.get("similarity", 0))
            else:
                scores.append(0)

        max_score = max(scores) if scores else 0.0
    else:
        max_score = 0.0

    state["confidence_score"] = max_score

    confidence_threshold = 0.7
    needs_web_search = max_score < confidence_threshold

    state["needs_web_search"] = needs_web_search

    logger.info(f"[ConfidenceCheck] Max score: {max_score:.3f}")
    logger.info(f"[ConfidenceCheck] Threshold: {confidence_threshold}")

    if needs_web_search:
        logger.warning(f"[ConfidenceCheck] Low confidence ({max_score:.3f} < {confidence_threshold}), will use Tavily")
    else:
        logger.success(f"[ConfidenceCheck] Sufficient confidence ({max_score:.3f} >= {confidence_threshold}), skipping web search")

    logger.info("=" * 80)
    logger.success("[ConfidenceCheck] Node completed")
    logger.info("=" * 80)

    return state
