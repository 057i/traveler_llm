"""
AI Recommendation Workflow - Node: Tavily Search

Optional web search when confidence is low
"""
from loguru import logger

from ..state import AIRecommendState


async def tavily_search_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Tavily web search

    Performs web search if confidence is low
    """
    if not state.get("needs_web_search", False):
        logger.info("[TavilySearch] Skipping - confidence sufficient")
        state["tavily_results"] = None
        return state

    logger.info("=" * 80)
    logger.info("[TavilySearch] Starting web search")
    logger.info("=" * 80)

    rewritten_query = state.get("rewritten_query", state["query"])
    logger.info(f"[TavilySearch] Query: {rewritten_query}")

    try:
        from app.core.tavily_client import get_tavily_client

        tavily_client = get_tavily_client()
        results = tavily_client.search(rewritten_query, max_results=5)

        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result.get('content', ''),
                'title': result.get('title', 'No title'),
                'similarity': 0.7,
                'metadata': {'url': result.get('url', '')},
                'source': 'tavily'
            })

        state["tavily_results"] = formatted_results
        logger.success(f"[TavilySearch] Web search completed: {len(formatted_results)} results")

    except Exception as e:
        logger.error(f"[TavilySearch] Web search failed: {e}")
        state["tavily_results"] = []

    logger.info("=" * 80)
    logger.success("[TavilySearch] Node completed")
    logger.info("=" * 80)

    return state
