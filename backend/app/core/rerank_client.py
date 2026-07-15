"""Rerank Client using local BGE Reranker model"""
from typing import List, Dict, Any, Optional
from loguru import logger
from sentence_transformers import CrossEncoder

from config.settings import settings


class RerankClient:
    """
    重排序客户端 - 基于BGE Reranker模型

    功能：
    - 使用CrossEncoder模型对检索结果重排序
    - 计算query与候选文档的相关性分数
    - 基于阈值过滤低质量结果
    - 智能控制返回结果数量

    模型：bge-reranker-base（本地部署）

    使用场景：
    - 提升检索精度（在召回后精排）
    - 过滤不相关结果
    - 多路检索结果的最终排序
    """

    def __init__(self):
        """Initialize rerank client with local model"""
        try:
            model_path = settings.RERANK_MODEL_PATH
            logger.info(f"[Rerank] Loading model from: {model_path}")

            self.model = CrossEncoder(model_path)

            logger.success(f"[Rerank] ✅ Local reranker initialized: {model_path}")
        except Exception as e:
            logger.error(f"[Rerank] ❌ Failed to initialize reranker: {e}")
            self.model = None

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 10,
        threshold: float = 0.5,
        min_results: int = 3,
        max_results: int = 7
    ) -> List[Dict[str, Any]]:
        """
        重排序候选结果（带智能过滤）

        工作流程：
        1. 构建query-candidate对
        2. 使用CrossEncoder计算相关性分数
        3. 按分数降序排序
        4. 应用阈值过滤（>= threshold的保留）
        5. 控制返回数量（min_results ~ max_results）

        Args:
            query: 用户查询
            candidates: 候选结果列表（每项包含name, description, tags等）
            top_n: 最多对多少个候选重排序（性能优化）
            threshold: 最低分数阈值（默认0.5，低于此分数的过滤掉）
            min_results: 最少返回结果数（如果过滤后不足，返回空列表触发知识缺口）
            max_results: 最多返回结果数

        Returns:
            重排序并过滤后的结果列表，每项新增 rerank_score 字段

        示例：
            >>> results = await rerank_client.rerank(
            ...     query="北京有什么好玩的",
            ...     candidates=[{"name": "故宫", "description": "..."}, ...],
            ...     threshold=0.6
            ... )
        """
        if not self.model or not candidates:
            logger.warning("[Rerank] No model or no candidates, returning original")
            return candidates[:min_results]

        try:
            logger.info(f"[Rerank] Reranking {len(candidates)} candidates...")
            logger.info(f"[Rerank] 🎯 Config: top_n={top_n}, threshold={threshold}, min={min_results}, max={max_results}")

            # Prepare query-candidate pairs
            pairs = []
            for candidate in candidates:
                # 构建候选文本
                name = candidate.get('name', '')
                description = candidate.get('description', '')
                tags = ' '.join(candidate.get('tags', []))

                # 组合文本（限制长度）
                candidate_text = f"{name} {description[:200]} {tags}"
                pairs.append([query, candidate_text])

            # 使用CrossEncoder计算分数
            scores = self.model.predict(pairs)

            # 更新候选结果的分数
            for i, candidate in enumerate(candidates):
                candidate['rerank_score'] = float(scores[i])

            # 按rerank_score降序排序
            reranked = sorted(candidates, key=lambda x: x.get('rerank_score', 0), reverse=True)

            # ========== 智能过滤策略 ==========
            # 1. 先取Top N
            top_candidates = reranked[:top_n]

            # 2. 过滤：保留 >= threshold 的结果
            filtered = [r for r in top_candidates if r.get('rerank_score', 0) >= threshold]

            # 3. 如果过滤后结果为空，返回空列表（不触发保底逻辑）
            if len(filtered) == 0:
                logger.warning(
                    f"[Rerank] ⚠️ No results >= {threshold}, returning empty list "
                    f"(will trigger knowledge gap message)"
                )
                final_results = []
            # 4. 如果过滤后 < min_results 但 > 0，保持原样（不强制补齐）
            elif len(filtered) < min_results:
                logger.info(
                    f"[Rerank] ✓ Only {len(filtered)} results >= {threshold}, "
                    f"returning as-is (no padding)"
                )
                final_results = filtered
            # 5. 如果过滤后 > max_results，限制：只返回Top max_results
            elif len(filtered) > max_results:
                logger.info(f"[Rerank] ✂️ Limiting {len(filtered)} results to {max_results}")
                final_results = filtered[:max_results]
            # 6. 否则，返回所有过滤后的结果
            else:
                final_results = filtered

            logger.success(
                f"[Rerank] ✅ Final: {len(final_results)} results "
                f"(filtered: {len(filtered)}/{len(top_candidates)} >= {threshold})"
            )
            # ==================================

            # 打印结果
            for i, r in enumerate(final_results, 1):
                rerank_score = r.get('rerank_score', 0)
                marker = "🔥" if rerank_score >= 0.7 else "✓" if rerank_score >= threshold else "⚠"
                logger.info(
                    f"[Rerank]   #{i}: {r.get('name', 'N/A')[:20]} | "
                    f"Rerank={rerank_score:.4f} {marker}"
                )

            return final_results

        except Exception as e:
            logger.error(f"[Rerank] ❌ Reranking failed: {e}")
            import traceback
            traceback.print_exc()

            # Fallback: 返回原始结果的前min_results条
            return candidates[:min_results]


_rerank_client = None


def get_rerank_client() -> RerankClient:
    """Get singleton rerank client instance"""
    global _rerank_client
    if _rerank_client is None:
        _rerank_client = RerankClient()
    return _rerank_client
