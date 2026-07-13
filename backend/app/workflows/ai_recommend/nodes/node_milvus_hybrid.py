"""
AI Recommendation Workflow - Node: Milvus Hybrid Search

Milvus混合检索节点：稠密+稀疏+精确匹配，内部RRF融合
"""
import asyncio
from loguru import logger
from typing import List, Dict, Any

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end
from config.settings import settings

FLOW_TYPE = "ai_recommend"


async def milvus_hybrid_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Milvus混合检索

    执行三路并行检索：
    1. 稠密向量检索（bge-base-zh-v1.5，语义相似）
    2. 稀疏向量检索（TF-IDF，关键词匹配）
    3. 实体精确匹配（景点名完全匹配）

    然后进行归一化+RRF融合，计算置信度
    """
    session_id = state.get("session_id")
    query = state.get("expanded_query") or state.get("rewritten_query", state["query"])
    entities = state.get("entities", [])

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[MilvusHybrid] Starting Milvus hybrid search")
    logger.info(f"[MilvusHybrid] Session: {session_id}")
    logger.info(f"[MilvusHybrid] Query: {query}")
    logger.info(f"[MilvusHybrid] Entities: {entities}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="milvus_hybrid",
            step_name="混合检索",
            progress=30,
            message="正在进行混合检索..."
        )

    # ========== 节点处理 ==========
    try:
        # 1. 并行三路检索
        logger.info("[MilvusHybrid] Parallel retrieving: dense + sparse + exact")

        dense_results, sparse_results, exact_results = await asyncio.gather(
            _search_dense(query),
            _search_sparse(query),
            _search_exact_match(entities)
        )

        logger.info(f"[MilvusHybrid] Dense: {len(dense_results)} results")
        logger.info(f"[MilvusHybrid] Sparse: {len(sparse_results)} results")
        logger.info(f"[MilvusHybrid] Exact: {len(exact_results)} results")

        # ========== 方案B：分路质量过滤 ==========
        if settings.QUALITY_FILTER_ENABLED:
            logger.info("[MilvusHybrid] Applying quality filter (Plan B: per-path filtering)")

            # 过滤稠密检索结果（score > 0.7）
            dense_filtered = [r for r in dense_results if r.get("score", 0) >= settings.DENSE_SCORE_THRESHOLD]
            logger.info(f"[MilvusHybrid] Dense filter: {len(dense_results)} → {len(dense_filtered)} (threshold={settings.DENSE_SCORE_THRESHOLD})")

            # 过滤稀疏检索结果（score > 0.35）
            sparse_filtered = [r for r in sparse_results if r.get("score", 0) >= settings.SPARSE_SCORE_THRESHOLD]
            logger.info(f"[MilvusHybrid] Sparse filter: {len(sparse_results)} → {len(sparse_filtered)} (threshold={settings.SPARSE_SCORE_THRESHOLD})")

            # 精确匹配全部保留
            exact_filtered = exact_results
            logger.info(f"[MilvusHybrid] Exact: {len(exact_results)} (keep all)")

            # 使用过滤后的结果
            dense_results = dense_filtered
            sparse_results = sparse_filtered
            exact_results = exact_filtered
        else:
            logger.info("[MilvusHybrid] Quality filter disabled")

        # ========== 打印原始分值详情 ==========
        logger.info("[MilvusHybrid] " + "=" * 60)
        logger.info("[MilvusHybrid] Original retrieval results:")
        logger.info("[MilvusHybrid] " + "=" * 60)

        # 打印稠密检索Top 5
        if dense_results:
            logger.info("[MilvusHybrid] Dense Search Top 5:")
            for i, r in enumerate(dense_results[:5], start=1):
                logger.info(
                    f"  #{i}: {r.get('name', 'N/A')[:20]:20s} | "
                    f"Score={r.get('score', 0):.4f} | "
                    f"Source={r.get('source', 'N/A')}"
                )

        # 打印稀疏检索Top 5
        if sparse_results:
            logger.info("[MilvusHybrid] Sparse Search Top 5:")
            for i, r in enumerate(sparse_results[:5], start=1):
                logger.info(
                    f"  #{i}: {r.get('name', 'N/A')[:20]:20s} | "
                    f"Score={r.get('score', 0):.4f} | "
                    f"Source={r.get('source', 'N/A')}"
                )

        # 打印精确匹配
        if exact_results:
            logger.info("[MilvusHybrid] Exact Match Results:")
            for i, r in enumerate(exact_results, start=1):
                logger.info(
                    f"  #{i}: {r.get('name', 'N/A')[:20]:20s} | "
                    f"Score={r.get('score', 0):.4f} (exact match) | "
                    f"Source={r.get('source', 'N/A')}"
                )

        logger.info("[MilvusHybrid] " + "=" * 60)

        # 2. 归一化+RRF融合
        logger.info("[MilvusHybrid] Normalizing and fusing with RRF...")

        from app.core.rrf_client import get_rrf_engine
        rrf_engine = get_rrf_engine()

        # 使用多路RRF融合
        fused_results = await rrf_engine.fuse_multi_path(
            results=[dense_results, sparse_results, exact_results],
            weights=[0.4, 0.3, 0.3],  # 稠密、稀疏、精确匹配权重
            top_k=settings.MILVUS_HYBRID_TOP_K
        )

        logger.success(f"[MilvusHybrid] Fused {len(fused_results)} results")

        # ========== 打印融合后的分值详情 ==========
        logger.info("[MilvusHybrid] " + "=" * 60)
        logger.info("[MilvusHybrid] RRF Fusion Results Top 20:")
        logger.info("[MilvusHybrid] " + "=" * 60)

        for i, r in enumerate(fused_results[:min(20, len(fused_results))], start=1):
            # 获取路径信息
            path1_rank = r.get("path_1_rank", "N/A")
            path2_rank = r.get("path_2_rank", "N/A")
            path3_rank = r.get("path_3_rank", "N/A")

            logger.info(
                f"  #{i}: {r.get('name', 'N/A')[:20]:20s} | "
                f"RRF={r.get('rrf_score', 0):.6f} | "
                f"OrigScore={r.get('score', 0):.4f} | "
                f"Ranks[Dense={path1_rank}, Sparse={path2_rank}, Exact={path3_rank}]"
            )

        logger.info("[MilvusHybrid] " + "=" * 60)


        logger.info("[MilvusHybrid] " + "=" * 60)

        # 3. 计算置信度（简化版本）
        confidence = _calculate_confidence(fused_results, entities)

        state["milvus_hybrid_results"] = fused_results
        state["milvus_confidence"] = confidence

        logger.success(f"[MilvusHybrid] Final confidence: {confidence:.3f}")

        # 打印Top 3简要信息
        if fused_results:
            logger.info("[MilvusHybrid] Final Top 3:")
            for i, r in enumerate(fused_results[:3], start=1):
                logger.info(
                    f"  #{i}: {r.get('name', 'N/A')} | "
                    f"RRF={r.get('rrf_score', 0):.4f} | "
                    f"Source={r.get('source', 'N/A')}"
                )
        else:
            logger.warning("[MilvusHybrid] No results after fusion")

    except Exception as e:
        logger.error(f"[MilvusHybrid] Search failed: {e}")
        import traceback
        traceback.print_exc()

        state["milvus_hybrid_results"] = []
        state["milvus_confidence"] = 0.0

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[MilvusHybrid] Milvus hybrid node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="milvus_hybrid",
            step_name="混合检索",
            progress=30,
            message=f"混合检索完成: {len(state['milvus_hybrid_results'])}条结果"
        )

    return state


async def _search_dense(query: str) -> List[Dict[str, Any]]:
    """稠密向量检索（HNSW索引）"""
    try:
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client
        from app.core.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()
        milvus_client = get_milvus_hybrid_client()

        # 生成稠密向量
        dense_vector = embedding_service.encode(query, normalize_embeddings=True)

        # 稠密检索
        results = await milvus_client._search_dense(
            dense_vector,
            top_k=settings.MILVUS_DENSE_TOP_K
        )

        return results

    except Exception as e:
        logger.error(f"[MilvusHybrid] Dense search failed: {e}")
        return []


async def _search_sparse(query: str) -> List[Dict[str, Any]]:
    """稀疏向量检索（TF-IDF）"""
    try:
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client

        milvus_client = get_milvus_hybrid_client()

        # 稀疏检索
        results = await milvus_client._search_sparse(
            query,
            top_k=settings.MILVUS_SPARSE_TOP_K
        )

        return results

    except Exception as e:
        logger.error(f"[MilvusHybrid] Sparse search failed: {e}")
        return []


async def _search_exact_match(entities: List[str]) -> List[Dict[str, Any]]:
    """实体精确匹配检索"""
    if not entities:
        logger.info("[MilvusHybrid] No entities for exact match")
        return []

    # 临时禁用：Milvus query()当前无法返回结果
    # 等query修复后再启用
    logger.warning("[MilvusHybrid] Exact match temporarily disabled due to Milvus query issue")
    logger.info(f"[MilvusHybrid] Would search for entities: {entities}")
    return []


def _calculate_confidence(results: List[Dict[str, Any]], entities: List[str]) -> float:
    """
    计算置信度分数（简化版）

    基于3个因素：
    1. 精确匹配（50%权重）
    2. 结果数量（30%权重）
    3. 来源多样性（20%权重）
    """
    if not results:
        return 0.0

    confidence = 0.0

    # ========== 1. 精确匹配检查（权重最高）==========
    has_exact_match = False
    exact_match_rank = None

    for i, r in enumerate(results, start=1):
        # 检查source字段或者查看实体名是否完全匹配
        if r.get("source") == "exact_match":
            has_exact_match = True
            exact_match_rank = i
            break
        # 也检查实体名是否在结果中
        if entities:
            result_name = r.get("name", "")
            if any(entity == result_name for entity in entities):
                has_exact_match = True
                exact_match_rank = i
                break

    if has_exact_match:
        if exact_match_rank == 1:
            confidence += 0.5  # Top1精确匹配，满分
        elif exact_match_rank <= 3:
            confidence += 0.4  # Top3精确匹配
        else:
            confidence += 0.3  # 有精确匹配但排名靠后
    else:
        confidence += 0.1  # 无精确匹配

    # ========== 2. 结果数量 ==========
    result_count = len(results)

    if result_count >= 10:
        confidence += 0.3  # 结果充足
    elif result_count >= 5:
        confidence += 0.2  # 结果中等
    elif result_count >= 3:
        confidence += 0.15  # 结果较少
    else:
        confidence += 0.1  # 结果很少

    # ========== 3. 来源多样性 ==========
    sources = set(r.get("source", "") for r in results[:10])
    diversity = len(sources)

    if diversity >= 3:
        confidence += 0.2  # 三种来源（最佳）
    elif diversity == 2:
        confidence += 0.15  # 两种来源
    else:
        confidence += 0.1  # 单一来源

    # 归一化到[0, 1]
    confidence = max(0.0, min(1.0, confidence))

    logger.info(f"[MilvusHybrid] Confidence calculation: exact_match={has_exact_match}(rank={exact_match_rank}), result_count={result_count}, diversity={diversity} -> {confidence:.3f}")

    return confidence
