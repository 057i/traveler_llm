"""
Base Service for recommendation services
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
import json

from app.models.schemas import QueryRequest, RecommendationResult
from app.core.milvus_client import get_milvus_client
from app.core.neo4j_client import get_neo4j_client
from app.core.integrated_search_client import get_rrf_engine
from app.core.rerank_client import get_rerank_client


class BaseRecommendService:
    """Base class for recommendation services"""

    def __init__(self):
        """Initialize base service"""
        self.milvus_client = get_milvus_client()
        self.neo4j_client = get_neo4j_client()
        self.rrf_engine = get_rrf_engine()
        self.rerank_client = get_rerank_client()
        logger.info("Base recommendation service initialized")

    async def search(self, query: QueryRequest) -> List[RecommendationResult]:
        """Search for recommendations - to be overridden"""
        raise NotImplementedError("Subclass must implement search method")

    async def stream_search(self, query: QueryRequest) -> AsyncGenerator[str, None]:
        """Stream search results - to be overridden"""
        raise NotImplementedError("Subclass must implement stream_search method")

    def filter_by_budget(
        self,
        results: List[RecommendationResult],
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None
    ) -> List[RecommendationResult]:
        """Filter results by budget range"""
        if not budget_min and not budget_max:
            return results

        filtered = []
        for result in results:
            budget = result.destination.budget
            if budget is None:
                continue

            if budget_min and budget < budget_min:
                continue
            if budget_max and budget > budget_max:
                continue

            filtered.append(result)

        logger.info(f"Filtered {len(results)} to {len(filtered)} by budget")
        return filtered

    def filter_by_season(
        self,
        results: List[RecommendationResult],
        season: Optional[str] = None
    ) -> List[RecommendationResult]:
        """Filter results by season"""
        if not season:
            return results

        filtered = []
        for result in results:
            if season in result.destination.best_seasons:
                filtered.append(result)

        logger.info(f"Filtered {len(results)} to {len(filtered)} by season: {season}")
        return filtered

    def filter_by_days(
        self,
        results: List[RecommendationResult],
        days: Optional[int] = None
    ) -> List[RecommendationResult]:
        """Filter results by trip duration"""
        if not days:
            return results

        filtered = []
        for result in results:
            rec_days = result.destination.recommended_days
            if rec_days is None:
                continue

            # Allow +/- 1 day flexibility
            if abs(rec_days - days) <= 1:
                filtered.append(result)

        logger.info(f"Filtered {len(results)} to {len(filtered)} by days: {days}")
        return filtered

    def apply_filters(
        self,
        results: List[RecommendationResult],
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        days: Optional[int] = None,
        season: Optional[str] = None
    ) -> List[RecommendationResult]:
        """Apply all filters"""
        filtered = results

        if budget_min or budget_max:
            filtered = self.filter_by_budget(filtered, budget_min, budget_max)

        if days:
            filtered = self.filter_by_days(filtered, days)

        if season:
            filtered = self.filter_by_season(filtered, season)

        return filtered
