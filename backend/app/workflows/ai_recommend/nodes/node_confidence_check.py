"""
AI Recommendation Workflow - Node: Confidence Check

置信度检查节点：判断Milvus结果质量，决定是否需要Tavily
"""
from loguru import logger

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end
from config.settings import settings

FLOW_TYPE = "ai_recommend"


async def confidence_check_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: 置信度检查

    检查Milvus结果的置信度，决定是否需要Tavily网络搜索
    """
    session_id = state.get("session_id")

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[ConfidenceCheck] 🚀 Starting confidence check")
    logger.info(f"[ConfidenceCheck] Session: {session_id}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="confidence",
            step_name="置信度检查",
            progress=50,
            message="正在检查置信度..."
        )

    # ========== 节点处理 ==========
    # 从Milvus节点获取置信度
    confidence = state.get("milvus_confidence", 0.0)
    threshold = settings.CONFIDENCE_THRESHOLD

    logger.info(f"[ConfidenceCheck] 📊 Milvus confidence: {confidence:.3f}")
    logger.info(f"[ConfidenceCheck] 📏 Threshold: {threshold:.3f}")

    # 判断是否需要网络搜索
    needs_web_search = confidence < threshold
    state["needs_web_search"] = needs_web_search
    state["confidence_score"] = confidence

    if needs_web_search:
        logger.warning(
            f"[ConfidenceCheck] ⚠️  Low confidence ({confidence:.3f} < {threshold:.3f}), "
            f"will trigger Tavily search"
        )
    else:
        logger.success(
            f"[ConfidenceCheck] ✅ Sufficient confidence ({confidence:.3f} >= {threshold:.3f}), "
            f"skipping Tavily"
        )

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[ConfidenceCheck] ✅ Confidence check node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="confidence",
            step_name="置信度检查",
            progress=50,
            message=f"置信度: {confidence:.2f}, {'需要' if needs_web_search else '无需'}网络搜索"
        )

    return state
