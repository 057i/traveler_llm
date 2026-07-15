"""
RRF (Reciprocal Rank Fusion) Client - 结果融合引擎

支持多源检索结果的融合，包括归一化和RRF算法
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import numpy as np


class RRFEngine:
    """
    RRF融合引擎 - Reciprocal Rank Fusion

    功能：
    - 多源检索结果融合（稠密向量 + 稀疏向量 + 图谱）
    - 分数归一化（Min-Max）
    - RRF算法融合（基于排名的倒数加权）
    - 加权融合（支持不同来源权重）
    - 多路融合（3+路）

    算法原理：
    RRF Score = Σ (weight / (k + rank))
    - k: 平滑参数（默认60）
    - rank: 结果在该来源中的排名（1-based）
    - weight: 来源权重

    优势：
    - 不依赖绝对分数（不同模型分数尺度不同）
    - 基于排名更鲁棒
    - 自然融合多源结果
    """

    def __init__(self, k: int = 60):
        """
        初始化RRF引擎

        Args:
            k: RRF平滑参数（默认60，越大越平滑）
        """
        self.k = k
        logger.info(f"[RRF] Initialized with k={k}")

    def normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        归一化分数到[0, 1]区间

        Args:
            results: 检索结果列表，每项包含score字段

        Returns:
            归一化后的结果列表
        """
        if not results:
            return []

        # 提取所有分数
        scores = [r.get("score", 0.0) for r in results]

        # 处理边界情况
        if len(scores) == 0:
            return results

        min_score = min(scores)
        max_score = max(scores)

        # 如果所有分数相同
        if max_score == min_score:
            for r in results:
                r["normalized_score"] = 1.0
            return results

        # Min-Max归一化
        for r in results:
            original_score = r.get("score", 0.0)
            normalized = (original_score - min_score) / (max_score - min_score)
            r["normalized_score"] = normalized

        logger.debug(f"[RRF] Normalized {len(results)} scores: [{min_score:.4f}, {max_score:.4f}] -> [0.0, 1.0]")
        return results

    def calculate_rrf_score(self, rank: int) -> float:
        """
        计算RRF分数

        RRF公式: score = 1 / (k + rank)
        rank从1开始

        Args:
            rank: 排名位置（1-based）

        Returns:
            RRF分数
        """
        return 1.0 / (self.k + rank)

    async def fuse(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        融合多源检索结果

        重要：
        1. 稠密和稀疏向量结果需要先归一化再RRF融合
        2. Neo4j图检索结果不参与融合，作为附加信息返回

        Args:
            vector_results: 向量检索结果（可能包含稠密+稀疏）
            graph_results: 图检索结果（可选，不参与融合）
            top_k: 返回Top K结果

        Returns:
            融合后的结果列表
        """
        logger.info(f"[RRF] Fusing results: vector={len(vector_results)}, graph={len(graph_results) if graph_results else 0}")

        if not vector_results:
            logger.warning("[RRF] No vector results to fuse")
            return []

        # 1. 归一化向量结果的分数
        normalized_results = self.normalize_scores(vector_results)

        # 2. 按归一化分数排序
        sorted_results = sorted(
            normalized_results,
            key=lambda x: x.get("normalized_score", 0.0),
            reverse=True
        )

        # 3. 计算RRF分数
        fused_results = {}
        for rank, result in enumerate(sorted_results, start=1):
            item_id = result.get("destination_id") or result.get("id") or result.get("name")

            if not item_id:
                continue

            rrf_score = self.calculate_rrf_score(rank)

            if item_id not in fused_results:
                fused_results[item_id] = {
                    **result,
                    "rrf_score": rrf_score,
                    "rrf_rank": rank,
                    "original_score": result.get("score", 0.0),
                    "normalized_score": result.get("normalized_score", 0.0)
                }
            else:
                # 如果同一个item出现多次，累加RRF分数
                fused_results[item_id]["rrf_score"] += rrf_score

        # 4. 按RRF分数排序
        final_results = sorted(
            fused_results.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:top_k]

        logger.success(f"[RRF] Fusion completed: {len(final_results)} results")

        # 5. 添加Neo4j图结果作为附加信息（不参与融合）
        for result in final_results:
            result["nearby_info"] = []  # 预留附近信息字段

        if graph_results:
            # 将图结果标记为附加信息
            for gr in graph_results:
                gr["is_nearby"] = True
                gr["source"] = "neo4j_nearby"

            logger.info(f"[RRF] Added {len(graph_results)} graph results as nearby info")

        return final_results

    async def fuse_dense_sparse(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        融合稠密和稀疏检索结果（专用方法）

        工作流程：
        1. 分别归一化稠密和稀疏结果的分数（Min-Max归一化到[0,1]）
        2. 按归一化分数排序，计算每个来源的RRF分数
        3. 同一item在多个来源出现，累加RRF分数
        4. 按最终RRF分数排序

        为什么要归一化？
        - 稠密向量分数（余弦相似度）范围：[-1, 1]
        - 稀疏向量分数（TF-IDF内积）范围：[0, +∞)
        - 归一化后统一到[0, 1]，便于比较

        Args:
            dense_results: 稠密向量检索结果（语义相似度）
            sparse_results: 稀疏向量检索结果（关键词匹配）
            top_k: 返回Top K结果

        Returns:
            融合后的结果列表，每项包含：
            - rrf_score: RRF融合分数
            - dense_rank: 在稠密结果中的排名
            - sparse_rank: 在稀疏结果中的排名
            - dense_score: 归一化后的稠密分数
            - sparse_score: 归一化后的稀疏分数
        """
        logger.info(f"[RRF] Fusing dense-sparse: dense={len(dense_results)}, sparse={len(sparse_results)}")

        # 1. 归一化稠密结果
        if dense_results:
            dense_normalized = self.normalize_scores(dense_results)
            logger.info(f"[RRF] Normalized {len(dense_normalized)} dense results")
        else:
            dense_normalized = []

        # 2. 归一化稀疏结果
        if sparse_results:
            sparse_normalized = self.normalize_scores(sparse_results)
            logger.info(f"[RRF] Normalized {len(sparse_normalized)} sparse results")
        else:
            sparse_normalized = []

        # 3. 计算每个来源的RRF分数
        rrf_scores = {}

        # 处理稠密结果
        for rank, result in enumerate(sorted(dense_normalized, key=lambda x: x.get("normalized_score", 0), reverse=True), start=1):
            item_id = result.get("destination_id") or result.get("id") or result.get("name")
            if not item_id:
                continue

            rrf_score = self.calculate_rrf_score(rank)

            if item_id not in rrf_scores:
                rrf_scores[item_id] = {
                    **result,
                    "rrf_score": rrf_score,
                    "dense_rank": rank,
                    "sparse_rank": None,
                    "dense_score": result.get("normalized_score", 0.0),
                    "sparse_score": None
                }
            else:
                rrf_scores[item_id]["rrf_score"] += rrf_score
                rrf_scores[item_id]["dense_rank"] = rank
                rrf_scores[item_id]["dense_score"] = result.get("normalized_score", 0.0)

        # 处理稀疏结果
        for rank, result in enumerate(sorted(sparse_normalized, key=lambda x: x.get("normalized_score", 0), reverse=True), start=1):
            item_id = result.get("destination_id") or result.get("id") or result.get("name")
            if not item_id:
                continue

            rrf_score = self.calculate_rrf_score(rank)

            if item_id not in rrf_scores:
                rrf_scores[item_id] = {
                    **result,
                    "rrf_score": rrf_score,
                    "dense_rank": None,
                    "sparse_rank": rank,
                    "dense_score": None,
                    "sparse_score": result.get("normalized_score", 0.0)
                }
            else:
                rrf_scores[item_id]["rrf_score"] += rrf_score
                rrf_scores[item_id]["sparse_rank"] = rank
                rrf_scores[item_id]["sparse_score"] = result.get("normalized_score", 0.0)

        # 4. 按RRF分数排序
        final_results = sorted(
            rrf_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:top_k]

        logger.success(f"[RRF] Dense-Sparse fusion completed: {len(final_results)} results")

        # 打印Top 3结果的详细信息
        for i, result in enumerate(final_results[:3], start=1):
            logger.debug(
                f"[RRF] #{i}: {result.get('name', 'N/A')} | "
                f"RRF={result['rrf_score']:.4f} | "
                f"Dense(rank={result.get('dense_rank', 'N/A')}, score={result.get('dense_score', 0):.4f}) | "
                f"Sparse(rank={result.get('sparse_rank', 'N/A')}, score={result.get('sparse_score', 0):.4f})"
            )

        return final_results


    async def fuse_weighted(
        self,
        results_a: List[Dict[str, Any]],
        results_b: List[Dict[str, Any]],
        weight_a: float = 0.7,
        weight_b: float = 0.3,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        加权RRF融合（两路）

        Args:
            results_a: 结果集A（如Milvus）
            results_b: 结果集B（如Tavily）
            weight_a: A的权重
            weight_b: B的权重
            top_k: 返回Top K结果

        Returns:
            融合后的结果列表
        """
        logger.info(f"[RRF] Weighted fusion: A={len(results_a)}, B={len(results_b)}")
        logger.info(f"[RRF] Weights: A={weight_a:.2f}, B={weight_b:.2f}")

        # 归一化权重
        total_weight = weight_a + weight_b
        weight_a = weight_a / total_weight
        weight_b = weight_b / total_weight

        # 归一化结果分数
        results_a_norm = self.normalize_scores(results_a) if results_a else []
        results_b_norm = self.normalize_scores(results_b) if results_b else []

        # 计算加权RRF分数
        rrf_scores = {}

        # 处理结果集A
        for rank, result in enumerate(sorted(results_a_norm,
                                            key=lambda x: x.get("normalized_score", 0),
                                            reverse=True), start=1):
            item_id = result.get("destination_id") or result.get("id") or result.get("name")
            if not item_id:
                continue

            rrf_score = self.calculate_rrf_score(rank) * weight_a

            rrf_scores[item_id] = {
                **result,
                "rrf_score": rrf_score,
                "source_a_rank": rank,
                "source_b_rank": None
            }

        # 处理结果集B
        for rank, result in enumerate(sorted(results_b_norm,
                                            key=lambda x: x.get("normalized_score", 0),
                                            reverse=True), start=1):
            item_id = result.get("destination_id") or result.get("id") or result.get("title") or result.get("name")
            if not item_id:
                continue

            rrf_score = self.calculate_rrf_score(rank) * weight_b

            if item_id in rrf_scores:
                rrf_scores[item_id]["rrf_score"] += rrf_score
                rrf_scores[item_id]["source_b_rank"] = rank
            else:
                rrf_scores[item_id] = {
                    **result,
                    "rrf_score": rrf_score,
                    "source_a_rank": None,
                    "source_b_rank": rank
                }

        # 排序返回
        final_results = sorted(
            rrf_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:top_k]

        logger.success(f"[RRF] Weighted fusion completed: {len(final_results)} results")
        return final_results


    async def fuse_multi_path(
        self,
        results: List[List[Dict[str, Any]]],
        weights: List[float],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        多路RRF融合（支持3+路）

        Args:
            results: 多个结果集列表 [[path1_results], [path2_results], ...]
            weights: 每路的权重 [w1, w2, w3, ...]
            top_k: 返回Top K结果

        Returns:
            融合后的结果列表
        """
        logger.info(f"[RRF] Multi-path fusion: {len(results)} paths")
        logger.info(f"[RRF] Weights: {weights}")

        # 归一化权重
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # 归一化每路结果
        normalized_results = []
        for i, path_results in enumerate(results):
            if path_results:
                norm_results = self.normalize_scores(path_results)
                normalized_results.append(norm_results)
                logger.info(f"[RRF] Path {i+1}: {len(path_results)} results")
            else:
                normalized_results.append([])
                logger.info(f"[RRF] Path {i+1}: 0 results")

        # 计算多路加权RRF分数
        rrf_scores = {}

        for path_idx, path_results in enumerate(normalized_results):
            weight = normalized_weights[path_idx]

            for rank, result in enumerate(sorted(path_results,
                                                key=lambda x: x.get("normalized_score", 0),
                                                reverse=True), start=1):
                item_id = result.get("destination_id") or result.get("id") or result.get("name")
                if not item_id:
                    continue

                rrf_score = self.calculate_rrf_score(rank) * weight

                if item_id in rrf_scores:
                    rrf_scores[item_id]["rrf_score"] += rrf_score
                    rrf_scores[item_id][f"path_{path_idx+1}_rank"] = rank
                else:
                    rrf_scores[item_id] = {
                        **result,
                        "rrf_score": rrf_score,
                        f"path_{path_idx+1}_rank": rank
                    }

        # 排序返回
        final_results = sorted(
            rrf_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:top_k]

        logger.success(f"[RRF] Multi-path fusion completed: {len(final_results)} results")
        return final_results


# 单例
_rrf_engine = None


def get_rrf_engine(k: int = 60) -> RRFEngine:
    """获取RRF引擎单例"""
    global _rrf_engine

    if _rrf_engine is None:
        from config.settings import settings
        _rrf_engine = RRFEngine(k=settings.RRF_K)

    return _rrf_engine
