"""
Fusion Strategies Module

Provides various score fusion strategies for combining multiple ranking results.
"""
from typing import List, Tuple, Dict
from loguru import logger
import math


class FusionStrategy:
    """Base fusion strategy class"""

    @staticmethod
    def normalize_scores(scores: Dict[int, float]) -> Dict[int, float]:
        """
        Normalize scores to [0, 1] using Min-Max normalization

        Args:
            scores: Dictionary mapping doc_id to score

        Returns:
            Normalized scores dictionary
        """
        if not scores:
            return {}

        values = list(scores.values())
        min_score = min(values)
        max_score = max(values)

        if max_score == min_score:
            return {doc_id: 1.0 for doc_id in scores}

        return {
            doc_id: (score - min_score) / (max_score - min_score)
            for doc_id, score in scores.items()
        }

    @staticmethod
    def rrf_fusion(
        rankings: List[List[Tuple[int, float]]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Reciprocal Rank Fusion (RRF)

        Args:
            rankings: List of ranking results, each is [(doc_id, score), ...]
            k: RRF parameter, default 60

        Returns:
            Fused ranking results
        """
        rrf_scores = {}

        for ranking in rankings:
            for rank, (doc_id, _) in enumerate(ranking, 1):
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0
                rrf_scores[doc_id] += 1 / (k + rank)

        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    @staticmethod
    def weighted_fusion(
        rankings: List[List[Tuple[int, float]]],
        weights: List[float]
    ) -> List[Tuple[int, float]]:
        """
        Weighted score fusion

        Args:
            rankings: List of ranking results
            weights: Weights for each ranking

        Returns:
            Fused ranking results
        """
        if len(rankings) != len(weights):
            logger.error("Number of rankings and weights must match")
            return []

        weighted_scores = {}

        for ranking, weight in zip(rankings, weights):
            scores_dict = {doc_id: score for doc_id, score in ranking}
            normalized = FusionStrategy.normalize_scores(scores_dict)

            for doc_id, score in normalized.items():
                if doc_id not in weighted_scores:
                    weighted_scores[doc_id] = 0
                weighted_scores[doc_id] += score * weight

        sorted_results = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    @staticmethod
    def max_fusion(
        rankings: List[List[Tuple[int, float]]]
    ) -> List[Tuple[int, float]]:
        """
        MAX fusion - take maximum score for each document

        Args:
            rankings: List of ranking results

        Returns:
            Fused ranking results
        """
        max_scores = {}

        for ranking in rankings:
            for doc_id, score in ranking:
                if doc_id not in max_scores:
                    max_scores[doc_id] = score
                else:
                    max_scores[doc_id] = max(max_scores[doc_id], score)

        sorted_results = sorted(
            max_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results
