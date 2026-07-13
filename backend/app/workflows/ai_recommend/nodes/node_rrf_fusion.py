"""
AI Recommendation Workflow - Node: RRF Fusion

加权RRF融合节点：融合Milvus+Tavily结果（可配置权重）
注意：Neo4j结果不参与融合，保留作为附近信息
"""
from loguru import logger

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end
from config.settings import settings

FLOW_TYPE = "ai_recommend"


async def rrf_fusion_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: 加权RRF融合

    融合Milvus和Tavily结果，使用可配置权重
    Neo4j结果不参与融合，保留作为附近信息补充
    """
    session_id = state.get("session_id")

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[RRFFusion] 🚀 Starting weighted RRF fusion")
    logger.info(f"[RRFFusion] Session: {session_id}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="fusion",
            step_name="结果融合",
            progress=70,
            message="正在融合检索结果..."
        )

    # ========== 节点处理 ==========
    milvus_results = state.get("milvus_hybrid_results", [])
    tavily_results = state.get("tavily_results", [])
    neo4j_results = state.get("neo4j_results", [])

    logger.info(f"[RRFFusion] Input:")
    logger.info(f"  - Milvus: {len(milvus_results)} results")
    logger.info(f"  - Tavily: {len(tavily_results)} results")
    logger.info(f"  - Neo4j: {len(neo4j_results)} results (not fused)")
    logger.info(f"[RRFFusion] Weights: Milvus={settings.RRF_MILVUS_WEIGHT}, "
                f"Tavily={settings.RRF_TAVILY_WEIGHT}")

    try:
        # 如果没有Tavily结果，直接使用Milvus结果
        if not tavily_results:
            logger.info("[RRFFusion] ⏭️  No Tavily results, using Milvus results directly")
            state["rrf_results"] = milvus_results[:10]

            logger.success(f"[RRFFusion] ✅ Using {len(state['rrf_results'])} Milvus results")

        else:
            # 使用加权RRF融合
            logger.info("[RRFFusion] 🔀 Fusing Milvus + Tavily with weighted RRF...")

            from app.core.rrf_client import get_rrf_engine
            rrf_engine = get_rrf_engine()

            fused_results = await rrf_engine.fuse_weighted(
                results_a=milvus_results,
                results_b=tavily_results,
                weight_a=settings.RRF_MILVUS_WEIGHT,
                weight_b=settings.RRF_TAVILY_WEIGHT,
                top_k=10
            )

            state["rrf_results"] = fused_results

            logger.success(f"[RRFFusion] ✅ Fused {len(fused_results)} results")

            # 打印Top 3
            if fused_results:
                logger.info("[RRFFusion] Top 3 results:")
                for i, r in enumerate(fused_results[:3], start=1):
                    logger.info(
                        f"  #{i}: {r.get('name', 'N/A')} | "
                        f"RRF={r.get('rrf_score', 0):.4f} | "
                        f"A_rank={r.get('source_a_rank', 'N/A')}, "
                        f"B_rank={r.get('source_b_rank', 'N/A')}"
                    )

    except Exception as e:
        logger.error(f"[RRFFusion] ❌ Fusion failed: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: 使用Milvus结果
        state["rrf_results"] = milvus_results[:10]

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[RRFFusion] ✅ RRF fusion node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="fusion",
            step_name="结果融合",
            progress=70,
            message=f"融合完成: {len(state['rrf_results'])}条结果"
        )

    return state
