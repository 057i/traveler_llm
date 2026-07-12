"""Integrated Search Client using RRF"""
from typing import List, Dict, Any
from collections import defaultdict
from loguru import logger

from app.models.schemas import RecommendationResult
from config.settings import settings


class RRFEngine:
    """Reciprocal Rank Fusion Engine"""

    def __init__(self, k: int = None):
        self.k = k or settings.RRF_K
        logger.info(f"RRF Engine initialized with k={self.k}")

    def fuse_results(
        self,
        results_dict: Dict[str, List[RecommendationResult]],
        weights: Dict[str, float] = None
    ) -> List[RecommendationResult]:
        """Fuse multiple search results using RRF algorithm"""
        if not results_dict:
            return []

        if weights is None:
            weights = {source: 1.0 for source in results_dict.keys()}

        rrf_scores = defaultdict(float)
        destination_map = {}

        for source, results in results_dict.items():
            weight = weights.get(source, 1.0)

            for rank, result in enumerate(results, start=1):
                dest_id = result.destination.name
                rrf_score = weight / (self.k + rank)
                rrf_scores[dest_id] += rrf_score

                if dest_id not in destination_map:
                    destination_map[dest_id] = result

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused_results = []
        for dest_id in sorted_ids:
            result = destination_map[dest_id]
            result.score = rrf_scores[dest_id]
            result.source = "rrf_fusion"
            fused_results.append(result)

        logger.success(f"RRF fusion completed: {len(fused_results)} results")
        return fused_results

    def calculate_diversity(self, results: List[RecommendationResult]) -> float:
        """Calculate diversity score of results"""
        if len(results) < 2:
            return 0.0

        tags_sets = [set(r.destination.tags) for r in results]
        diversity_sum = 0.0
        count = 0

        for i in range(len(tags_sets)):
            for j in range(i + 1, len(tags_sets)):
                intersection = len(tags_sets[i] & tags_sets[j])
                union = len(tags_sets[i] | tags_sets[j])

                if union > 0:
                    diversity = 1.0 - (intersection / union)
                    diversity_sum += diversity
                    count += 1

        return diversity_sum / count if count > 0 else 0.0

    def diversify_results(
        self,
        results: List[RecommendationResult],
        alpha: float = 0.7,
        top_k: int = None
    ) -> List[RecommendationResult]:
        """Diversify results using MMR-like algorithm"""
        if not results:
            return []

        top_k = top_k or len(results)
        selected = []
        remaining = results.copy()

        selected.append(remaining.pop(0))

        while remaining and len(selected) < top_k:
            best_score = -float('inf')
            best_idx = 0

            for idx, candidate in enumerate(remaining):
                relevance = candidate.score
                diversity = 0.0

                if selected:
                    candidate_tags = set(candidate.destination.tags)

                    for sel in selected:
                        sel_tags = set(sel.destination.tags)
                        intersection = len(candidate_tags & sel_tags)
                        union = len(candidate_tags | sel_tags)

                        if union > 0:
                            diversity += 1.0 - (intersection / union)

                    diversity /= len(selected)

                combined = alpha * relevance + (1 - alpha) * diversity

                if combined > best_score:
                    best_score = combined
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        logger.info(f"Diversified {len(results)} results to {len(selected)}")
        return selected


_rrf_engine_instance = None


def get_rrf_engine() -> RRFEngine:
    """Get singleton RRF engine instance"""
    global _rrf_engine_instance
    if _rrf_engine_instance is None:
        _rrf_engine_instance = RRFEngine()
    return _rrf_engine_instance
