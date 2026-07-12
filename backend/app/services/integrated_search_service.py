"""
Integrated Search Service using RRF fusion
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
import json

from app.models.schemas import QueryRequest, RecommendationResult
from app.services.base_service import BaseRecommendService
from app.services.destination_extractor import get_destination_extractor


class IntegratedSearchService(BaseRecommendService):
    """Integrated search service using RRF fusion"""

    def __init__(self):
        """Initialize integrated search service"""
        super().__init__()
        self.extractor = get_destination_extractor()
        logger.info("Integrated search service initialized")

    async def search(self, query: QueryRequest) -> List[RecommendationResult]:
        """Search using RRF fusion"""
        logger.info(f"[IntegratedSearch] Query: {query.query}")

        # Extract core entities for better search
        core_query = await self.extractor.extract_core_entities(query.query)
        logger.info(f"[IntegratedSearch] Core query: {core_query}")

        # Collect results from multiple sources
        results_dict = {}

        # 1. Vector search
        try:
            vector_results = await self._vector_search(core_query, query.top_k or 10)
            if vector_results:
                results_dict["vector"] = vector_results
                logger.info(f"[IntegratedSearch] Vector: {len(vector_results)} results")
        except Exception as e:
            logger.error(f"[IntegratedSearch] Vector search failed: {e}")

        # 2. Graph search
        try:
            graph_results = await self._graph_search(core_query, query.top_k or 10)
            if graph_results:
                results_dict["graph"] = graph_results
                logger.info(f"[IntegratedSearch] Graph: {len(graph_results)} results")
        except Exception as e:
            logger.error(f"[IntegratedSearch] Graph search failed: {e}")

        if not results_dict:
            logger.warning("[IntegratedSearch] No results from any source")
            return []

        # 3. RRF fusion
        fused_results = self.rrf_engine.fuse_results(
            results_dict,
            weights={"vector": 0.6, "graph": 0.4}
        )

        logger.info(f"[IntegratedSearch] Fused: {len(fused_results)} results")

        # 4. Apply filters
        if query.budget_min or query.budget_max or query.days or query.season:
            fused_results = self.apply_filters(
                fused_results,
                budget_min=query.budget_min,
                budget_max=query.budget_max,
                days=query.days,
                season=query.season
            )
            logger.info(f"[IntegratedSearch] After filters: {len(fused_results)} results")

        # 5. Diversify results
        if len(fused_results) > query.top_k:
            fused_results = self.rrf_engine.diversify_results(
                fused_results,
                alpha=0.7,
                top_k=query.top_k
            )

        logger.success(f"[IntegratedSearch] Final: {len(fused_results)} results")
        return fused_results

    async def stream_search(self, query: QueryRequest) -> AsyncGenerator[str, None]:
        """Stream search results"""
        yield json.dumps({"type": "status", "message": "Starting search..."}) + "\n"

        results = await self.search(query)

        for i, result in enumerate(results):
            yield json.dumps({
                "type": "result",
                "index": i,
                "data": result.dict()
            }) + "\n"

        yield json.dumps({"type": "done", "total": len(results)}) + "\n"

    async def _vector_search(self, query: str, top_k: int) -> List[RecommendationResult]:
        """Perform vector search"""
        # Placeholder - implement with your Milvus client
        return []

    async def _graph_search(self, query: str, top_k: int) -> List[RecommendationResult]:
        """Perform graph search"""
        # Placeholder - implement with your Neo4j client
        return []


_integrated_search_service = None


def get_integrated_search_service() -> IntegratedSearchService:
    """Get singleton integrated search service instance"""
    global _integrated_search_service
    if _integrated_search_service is None:
        _integrated_search_service = IntegratedSearchService()
    return _integrated_search_service
