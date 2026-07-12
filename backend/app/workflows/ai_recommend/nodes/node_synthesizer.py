"""
AI Recommendation Workflow - Node: Synthesizer

Generate final answer using LLM
"""
from loguru import logger
from dashscope import Generation

from config.settings import settings
from ..state import AIRecommendState


async def synthesizer_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: LLM synthesizer

    Generates natural language answer from reranked results
    """
    logger.info("=" * 80)
    logger.info("[Synthesizer] Starting answer generation")
    logger.info("=" * 80)

    query = state.get("query", "")
    reranked_results = state.get("reranked_results", [])

    logger.info(f"[Synthesizer] Query: {query}")
    logger.info(f"[Synthesizer] Results to synthesize: {len(reranked_results)}")

    if not reranked_results:
        logger.warning("[Synthesizer] No results to synthesize")
        state["final_answer"] = "Sorry, no relevant information found for your query."
        state["sources"] = []
        logger.info("=" * 80)
        logger.success("[Synthesizer] Node completed")
        logger.info("=" * 80)
        return state

    try:
        # Build context from top results
        context_parts = []
        for i, r in enumerate(reranked_results[:5]):
            if hasattr(r, 'name'):
                title = r.name
                content = r.destination.description if hasattr(r, 'destination') else ''
            elif isinstance(r, dict):
                title = r.get('title', f'Result {i+1}')
                content = r.get('content', '')
            else:
                continue

            context_parts.append(
                f"Source {i+1}: {title}\nContent: {content[:500]}"
            )

        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = f"""As a professional travel consultant, generate a comprehensive and helpful answer based on the following context.

User Query: {query}

Context:
{context}

Generate a detailed, well-structured answer in Chinese that:
1. Directly addresses the user's question
2. Includes specific information from the sources
3. Provides practical recommendations
4. Is engaging and easy to read

Answer:"""

        # Call LLM
        response = Generation.call(
            model=settings.QWEN_MODEL,
            prompt=prompt,
            api_key=settings.DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            final_answer = response.output.text.strip()
            state["final_answer"] = final_answer
            logger.success(f"[Synthesizer] Generated answer: {len(final_answer)} characters")
        else:
            logger.error(f"[Synthesizer] LLM call failed: {response.status_code}")
            state["final_answer"] = "Failed to generate answer. Please try again."

    except Exception as e:
        logger.error(f"[Synthesizer] Generation failed: {e}")
        import traceback
        traceback.print_exc()

        state["final_answer"] = f"Error generating answer: {str(e)}"

    logger.info("=" * 80)
    logger.success("[Synthesizer] Node completed")
    logger.info("=" * 80)

    return state
