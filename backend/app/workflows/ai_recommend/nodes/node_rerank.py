"""
AI Recommendation Workflow - Node: Rerank

智能重排节点：使用BGE Reranker深度语义重排
"""
from loguru import logger

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end
from config.settings import settings

FLOW_TYPE = "ai_recommend"


async def rerank_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: 智能重排

    使用bge-reranker-v2-m3进行深度语义重排
    """
    session_id = state.get("session_id")

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[Rerank] 🚀 Starting reranking")
    logger.info(f"[Rerank] Session: {session_id}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="rerank",
            step_name="智能重排",
            progress=85,
            message="正在重排序结果..."
        )

    # ========== 节点处理 ==========
    rrf_results = state.get("rrf_results", [])
    query = state.get("query", "")

    logger.info(f"[Rerank] 📊 Input: {len(rrf_results)} results")
    logger.info(f"[Rerank] 🔍 Query: {query}")

    if not rrf_results:
        logger.warning("[Rerank] ⚠️  No results to rerank")
        state["reranked_results"] = []

        if session_id:
            await send_node_end(
                task_id=session_id,
                flow_type=FLOW_TYPE,
                step_id="rerank",
                step_name="智能重排",
                progress=85,
                message="无结果需要重排"
            )

        logger.info("=" * 80)
        logger.success("[Rerank] ✅ Node completed (no results)")
        logger.info("=" * 80)

        return state

    try:
        from app.core.rerank_client import get_rerank_client

        rerank_client = get_rerank_client()

        # 执行重排
        logger.info("[Rerank] 🔄 Performing rerank...")
        reranked = await rerank_client.rerank(
            query=query,
            candidates=rrf_results,
            top_n=settings.RERANK_TOP_N,
            threshold=settings.RERANK_THRESHOLD,
            min_results=settings.RERANK_MIN_RESULTS,
            max_results=settings.RERANK_MAX_RESULTS
        )

        state["reranked_results"] = reranked
        logger.success(f"[Rerank] ✅ Reranking completed: {len(reranked)} results")

        # 打印结果统计
        if reranked:
            high_quality = len([r for r in reranked if r.get('rerank_score', 0) >= 0.7])
            medium_quality = len([r for r in reranked if 0.5 <= r.get('rerank_score', 0) < 0.7])
            low_quality = len([r for r in reranked if r.get('rerank_score', 0) < 0.5])

            logger.info(f"[Rerank] 📊 Quality: High(>=0.7)={high_quality}, Medium(>=0.5)={medium_quality}, Low(<0.5)={low_quality}")

    except Exception as e:
        logger.error(f"[Rerank] ❌ Reranking failed: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: 使用RRF结果
        state["reranked_results"] = rrf_results

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[Rerank] ✅ Rerank node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="rerank",
            step_name="智能重排",
            progress=85,
            message=f"重排序完成: {len(state['reranked_results'])}条"
        )

    return state
