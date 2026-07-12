"""
AI Recommendation Workflow - Node: Query Rewriter

Rewrites user query and extracts entities for better search
"""
from loguru import logger
from dashscope import Generation
import json

from config.settings import settings
from ..state import AIRecommendState


async def query_rewriter_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Query rewriter and entity extraction

    Tasks:
    1. Rewrite user query for better search
    2. Extract entities (destinations, activities, etc.)
    3. Identify intent
    """
    logger.info("=" * 80)
    logger.info("[QueryRewriter] Starting query rewrite")
    logger.info("=" * 80)

    user_query = state.get("query", "")
    session_id = state.get("session_id")

    logger.info(f"[QueryRewriter] Original query: {user_query}")
    logger.info(f"[QueryRewriter] Session ID: {session_id}")

    try:
        # Build prompt for query rewriting
        prompt = f"""You are a travel query optimization expert. Analyze the user's query and provide:
1. A rewritten, more searchable version of the query
2. Extracted entities (destinations, activities, interests)
3. Query intent

User Query: {user_query}

Respond in JSON format:
{{
    "rewritten_query": "optimized search query",
    "entities": ["entity1", "entity2"],
    "intent": "travel_guide/attraction/route/food/hotel"
}}
"""

        # Call LLM
        response = Generation.call(
            model=settings.QWEN_MODEL,
            prompt=prompt,
            api_key=settings.DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            result_text = response.output.text.strip()

            # Try to parse JSON
            try:
                result = json.loads(result_text)
                state["rewritten_query"] = result.get("rewritten_query", user_query)
                state["entities"] = result.get("entities", [])

                logger.success(f"[QueryRewriter] Rewritten: {state['rewritten_query']}")
                logger.info(f"[QueryRewriter] Entities: {state['entities']}")

            except json.JSONDecodeError:
                # Fallback to original query
                logger.warning("[QueryRewriter] JSON parse failed, using original query")
                state["rewritten_query"] = user_query
                state["entities"] = []
        else:
            # Fallback
            logger.error(f"[QueryRewriter] LLM call failed: {response.status_code}")
            state["rewritten_query"] = user_query
            state["entities"] = []

    except Exception as e:
        logger.error(f"[QueryRewriter] Error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to original query
        state["rewritten_query"] = user_query
        state["entities"] = []

    logger.info("=" * 80)
    logger.success("[QueryRewriter] Node completed")
    logger.info("=" * 80)

    return state
