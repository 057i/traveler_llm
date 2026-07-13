"""
AI Recommendation Workflow - Node: Tavily Search

Tavily网络搜索节点：条件执行，补充外部信息
"""
from loguru import logger

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "ai_recommend"


async def tavily_search_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Tavily网络搜索

    条件执行：仅当 needs_web_search = True 时执行
    """
    session_id = state.get("session_id")
    needs_search = state.get("needs_web_search", False)

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[TavilySearch] 🚀 Starting Tavily web search")
    logger.info(f"[TavilySearch] Session: {session_id}")
    logger.info(f"[TavilySearch] Needs search: {needs_search}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="tavily",
            step_name="网络搜索",
            progress=60,
            message="正在搜索网络..."
        )

    # ========== 节点处理 ==========
    # 条件判断：是否需要网络搜索
    if not needs_search:
        logger.info("[TavilySearch] ⏭️  Skipping - confidence sufficient")
        state["tavily_results"] = []

        # 发送node_end事件
        if session_id:
            await send_node_end(
                task_id=session_id,
                flow_type=FLOW_TYPE,
                step_id="tavily",
                step_name="网络搜索",
                progress=60,
                message="无需网络搜索"
            )

        logger.info("=" * 80)
        logger.success("[TavilySearch] ✅ Node completed (skipped)")
        logger.info("=" * 80)

        return state

    # 执行Tavily搜索
    query = state.get("rewritten_query", state["query"])
    logger.info(f"[TavilySearch] 🔍 Query: {query}")

    try:
        from app.core.tavily_client import get_tavily_client

        tavily = get_tavily_client()
        results = tavily.search(query, max_results=5)  # 去掉await

        logger.success(f"[TavilySearch] ✅ Found {len(results)} web results")

        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result.get('content', ''),
                'title': result.get('title', 'No title'),
                'score': result.get('score', 0.7),
                'url': result.get('url', ''),
                'source': 'tavily'
            })

        state["tavily_results"] = formatted_results

        # 打印前3条
        if formatted_results:
            logger.info("[TavilySearch] Top 3 results:")
            for i, r in enumerate(formatted_results[:3], start=1):
                logger.info(f"  #{i}: {r['title'][:50]}")

    except Exception as e:
        logger.error(f"[TavilySearch] ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

        state["tavily_results"] = []

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[TavilySearch] ✅ Tavily search node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="tavily",
            step_name="网络搜索",
            progress=60,
            message=f"网络搜索完成: {len(state.get('tavily_results', []))}条结果"
        )

    return state
