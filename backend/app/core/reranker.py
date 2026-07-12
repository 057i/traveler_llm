"""Reranker using cross-encoder model"""
from typing import List, Dict, Any
from loguru import logger
from sentence_transformers import CrossEncoder

from app.models.schemas import RecommendationResult


class Reranker:
    """Rerank search results using cross-encoder"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize reranker with model"""
        try:
            self.model = CrossEncoder(model_name)
            logger.success(f"Reranker initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            self.model = None

    def rerank(
        self,
        query: str,
        results: List[RecommendationResult],
        top_k: int = None
    ) -> List[RecommendationResult]:
        """Rerank results using cross-encoder"""
        if not self.model or not results:
            return results

        top_k = top_k or len(results)

        # Prepare pairs for cross-encoder
        pairs = []
        for result in results:
            text = f"{result.destination.name} {result.destination.description}"
            pairs.append([query, text])

        # Get scores from cross-encoder
        scores = self.model.predict(pairs)

        # Update scores and sort
        for i, result in enumerate(results):
            result.score = float(scores[i])
            result.source = "reranker"

        # Sort by score and return top k
        reranked = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

        logger.info(f"Reranked {len(results)} results to top {len(reranked)}")
        return reranked


_reranker_instance = None


def get_reranker() -> Reranker:
    """Get singleton reranker instance"""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance
