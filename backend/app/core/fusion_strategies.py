"""
Fusion Strategies Module

Provides various score fusion strategies for combining multiple ranking results.
"""
from typing import List, Tuple, Dict
from loguru import logger
import math


class FusionStrategy:
    """
    融合策略基类

    提供多种结果融合算法：
    1. RRF融合（Reciprocal Rank Fusion）
    2. 加权融合（Weighted Fusion）
    3. MAX融合（取最大分数）

    适用场景：
    - 多模型检索结果融合
    - 多数据源结果合并
    - 提升检索准确率
    """

    @staticmethod
    def normalize_scores(scores: Dict[int, float]) -> Dict[int, float]:
        """
        分数归一化（Min-Max归一化）

        将分数缩放到[0, 1]区间，消除不同模型分数尺度差异

        公式：normalized = (score - min) / (max - min)

        Args:
            scores: 文档ID到分数的映射 {doc_id: score}

        Returns:
            归一化后的分数字典 {doc_id: normalized_score}
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
        RRF融合（Reciprocal Rank Fusion）

        核心思想：基于排名而非绝对分数
        - 不受不同模型分数尺度影响
        - 排名靠前的结果权重更高
        - 在多个榜单中都出现的结果权重累加

        公式：RRF_score(d) = Σ (1 / (k + rank(d)))

        Args:
            rankings: 多个排序列表 [[(doc_id, score), ...], ...]
            k: 平滑参数（默认60，避免首位优势过大）

        Returns:
            融合后的排序结果 [(doc_id, rrf_score), ...]
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
