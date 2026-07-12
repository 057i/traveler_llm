"""
Hybrid Recommendation Service
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
import json

from app.models.schemas import QueryRequest, RecommendationResult
from app.services.base_service import BaseRecommendService


class HybridRecommendService(BaseRecommendService):
    """Hybrid recommendation using multiple search strategies"""

    def __init__(self):
        """Initialize hybrid recommendation service"""
        super().__init__()
        logger.info("Hybrid recommendation service initialized")

    async def search(self, query: QueryRequest) -> List[RecommendationResult]:
        """Search using hybrid approach"""
        logger.info(f"[Hybrid] Starting search for: {query.query}")

        # Collect results from multiple sources
        results_dict = {}

        # 1. Vector search (Milvus)
        try:
            vector_results = await self._vector_search(query.query)
            if vector_results:
                results_dict["vector"] = vector_results
                logger.info(f"[Hybrid] Vector search: {len(vector_results)} results")
        except Exception as e:
            logger.error(f"[Hybrid] Vector search failed: {e}")

        # 2. Graph search (Neo4j)
        try:
            graph_results = await self._graph_search(query.query)
            if graph_results:
                results_dict["graph"] = graph_results
                logger.info(f"[Hybrid] Graph search: {len(graph_results)} results")
        except Exception as e:
            logger.error(f"[Hybrid] Graph search failed: {e}")

        # 3. Fuse results using RRF
        fused_results = self.rrf_engine.fuse_results(
            results_dict,
            weights={"vector": 0.6, "graph": 0.4}
        )

        # 4. Apply filters
        if query.budget_min or query.budget_max or query.days or query.season:
            logger.info(f"[Hybrid] Applying filters: budget={query.budget_min}-{query.budget_max}, days={query.days}, season={query.season}")
            fused_results = self.apply_filters(
                fused_results,
                budget_min=query.budget_min,
                budget_max=query.budget_max,
                days=query.days,
                season=query.season
            )

        # 5. Rerank top results
        if len(fused_results) > 3:
            logger.info(f"[Hybrid] Reranking top results")
            fused_results = self.rerank_client.rerank(
                query.query,
                fused_results[:10],
                top_n=query.top_k or 5
            )

        logger.success(f"[Hybrid] Completed: {len(fused_results)} results")
        return fused_results[:query.top_k or 5]

    async def stream_search(self, query: QueryRequest) -> AsyncGenerator[str, None]:
        """Stream search results"""
        yield json.dumps({"type": "status", "message": "Starting hybrid search..."}) + "\n"

        results = await self.search(query)

        for result in results:
            yield json.dumps({
                "type": "result",
                "data": result.dict()
            }) + "\n"

        yield json.dumps({"type": "done", "count": len(results)}) + "\n"

    async def _vector_search(self, query: str) -> List[RecommendationResult]:
        """Perform vector search"""
        # Implementation depends on your RAG engine
        # This is a placeholder
        return []

    async def _graph_search(self, query: str) -> List[RecommendationResult]:
        """Perform graph search"""
        # Implementation depends on your graph RAG engine
        # This is a placeholder
        return []


_hybrid_service = None


def get_hybrid_recommend_service() -> HybridRecommendService:
    """Get singleton hybrid recommendation service instance"""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridRecommendService()
    return _hybrid_service
