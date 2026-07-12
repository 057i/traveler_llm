"""
AI Recommendation Workflow - Node: Parallel Retrieval

Parallel search from Milvus and Neo4j
"""
import asyncio
from loguru import logger

from ..state import AIRecommendState


async def parallel_retrieval_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Parallel retrieval from multiple sources

    Retrieves from:
    - Milvus: Dense + Sparse hybrid search
    - Neo4j: Graph-based related destinations
    """
    logger.info("=" * 80)
    logger.info("[ParallelRetrieval] Starting parallel retrieval")
    logger.info("=" * 80)

    rewritten_query = state.get("rewritten_query", state["query"])
    logger.info(f"[ParallelRetrieval] Query: {rewritten_query}")

    async def milvus_search():
        """Search from Milvus vector database"""
        try:
            logger.info("[ParallelRetrieval] Searching Milvus (hybrid search)")
            from app.core.chroma_client import get_chroma_client

            chroma = get_chroma_client()
            results = chroma.search(query_text=rewritten_query, n_results=10)

            milvus_results = []
            if results and 'documents' in results:
                for i, doc in enumerate(results['documents'][0]):
                    milvus_results.append({
                        'content': doc,
                        'score': 1.0 - (i * 0.05),
                        'source': 'milvus'
                    })

            logger.success(f"[ParallelRetrieval] Milvus: {len(milvus_results)} results")
            return milvus_results

        except Exception as e:
            logger.error(f"[ParallelRetrieval] Milvus search failed: {e}")
            return []

    async def neo4j_search():
        """Search from Neo4j graph database"""
        try:
            logger.info("[ParallelRetrieval] Searching Neo4j (graph search)")
            logger.warning("[ParallelRetrieval] Neo4j search placeholder")
            return []

        except Exception as e:
            logger.error(f"[ParallelRetrieval] Neo4j search failed: {e}")
            return []

    milvus_results, neo4j_results = await asyncio.gather(
        milvus_search(),
        neo4j_search()
    )

    state["milvus_results"] = milvus_results
    state["neo4j_results"] = neo4j_results

    logger.info("=" * 80)
    logger.success(f"[ParallelRetrieval] Completed: Milvus {len(milvus_results)}, Neo4j {len(neo4j_results)}")
    logger.info("=" * 80)

    return state
