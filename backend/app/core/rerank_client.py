"""Rerank Client using Dashscope API"""
from typing import List, Dict, Any, Optional
from loguru import logger
import dashscope
from dashscope import Generation

from config.settings import settings
from app.models.schemas import RecommendationResult


class RerankClient:
    """Client for reranking using Dashscope API"""

    def __init__(self):
        """Initialize rerank client"""
        self.api_key = settings.DASHSCOPE_API_KEY
        dashscope.api_key = self.api_key

    def rerank(
        self,
        query: str,
        candidates: List[RecommendationResult],
        top_n: int = 3
    ) -> List[RecommendationResult]:
        """Rerank candidates using LLM"""
        if not candidates:
            return []

        try:
            # Build prompt for reranking
            candidates_text = ""
            for i, candidate in enumerate(candidates):
                dest = candidate.destination
                candidates_text += f"{i+1}. {dest.name} - {dest.description[:100]}...\n"

            prompt = f"""Given the user query: "{query}"

Rank the following travel destinations from most relevant to least relevant:

{candidates_text}

Return only the ranking numbers separated by commas (e.g., "3,1,5,2,4").
"""

            response = Generation.call(
                model=settings.LLM_MODEL,
                prompt=prompt,
                max_tokens=100,
                temperature=0.1
            )

            if response.status_code == 200:
                ranking_text = response.output.text.strip()
                rankings = [int(x.strip()) - 1 for x in ranking_text.split(",") if x.strip().isdigit()]

                # Reorder candidates based on ranking
                reranked = []
                for rank in rankings[:top_n]:
                    if 0 <= rank < len(candidates):
                        candidate = candidates[rank]
                        candidate.source = "llm_rerank"
                        reranked.append(candidate)

                logger.success(f"Reranked {len(candidates)} to top {len(reranked)}")
                return reranked
            else:
                logger.error(f"Rerank API error: {response.message}")
                return candidates[:top_n]

        except Exception as e:
            logger.error(f"Rerank failed: {e}")
            return candidates[:top_n]


_rerank_client = None


def get_rerank_client() -> RerankClient:
    """Get singleton rerank client instance"""
    global _rerank_client
    if _rerank_client is None:
        _rerank_client = RerankClient()
    return _rerank_client
