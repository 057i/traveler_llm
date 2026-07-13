"""
AI Recommendation Workflow - Node: Query Rewriter

查询重写节点：
1. 判断是否旅游相关问题
2. 提取实体
3. 查询重写
4. 查询扩展（LLM生成相关词）
"""
from loguru import logger
from dashscope import Generation
import json

from config.settings import settings
from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "ai_recommend"


async def query_rewriter_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Query rewriter with intent recognition

    Tasks:
    1. 判断是否旅游相关问题（非旅游问题优雅拒绝）
    2. 提取实体
    3. 重写查询
    4. 查询扩展（生成相关关键词）
    5. 判断是否需要附近检索
    """
    session_id = state.get("session_id")
    user_query = state.get("query", "")

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[QueryRewriter] 🚀 Starting query rewriter node")
    logger.info(f"[QueryRewriter] Session: {session_id}")
    logger.info(f"[QueryRewriter] Original query: {user_query}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="rewrite",
            step_name="查询分析",
            progress=10,
            message="正在分析查询..."
        )

    # ========== 节点处理 ==========
    try:
        # Step 1: 判断是否旅游相关 + 提取信息
        prompt = f"""你是旅游领域的智能助手。请分析用户的查询并返回JSON格式的结果。

用户查询: {user_query}

请分析以下内容：
1. is_travel_related: 判断是否是旅游相关问题（景点、路线、住宿、美食、攻略等）
2. rewritten_query: 将查询重写为更适合检索的形式
3. entities: 提取地名、景点名等实体
4. needs_nearby_search: 是否需要附近推荐（包含"附近"、"周边"、"周围"、"附近酒店"、"附近美食"、"周边景点"等关键词）
5. nearby_type: 如果needs_nearby_search=true，判断类型：景点(attraction)/酒店(hotel)/美食(food)/全部(all)
6. expanded_keywords: 生成3-5个相关搜索关键词（同义词、相关词）

返回JSON格式：
{{
    "is_travel_related": true/false,
    "rewritten_query": "优化后的查询",
    "entities": ["实体1", "实体2"],
    "needs_nearby_search": true/false,
    "nearby_type": "attraction/hotel/food/all",
    "expanded_keywords": "关键词1 关键词2 关键词3"
}}

示例：
- 输入: "三清山附近有什么景点"
  输出: {{"is_travel_related": true, "rewritten_query": "三清山 周边 景点 推荐", "entities": ["三清山"], "needs_nearby_search": true, "nearby_type": "attraction", "expanded_keywords": "三清山景区 道教名山 上饶旅游"}}

- 输入: "推荐三清山附近的酒店"
  输出: {{"is_travel_related": true, "rewritten_query": "三清山 附近 酒店", "entities": ["三清山"], "needs_nearby_search": true, "nearby_type": "hotel", "expanded_keywords": "三清山住宿 三清山酒店 三清山客栈"}}

- 输入: "三清山周边有什么好吃的"
  输出: {{"is_travel_related": true, "rewritten_query": "三清山 周边 美食", "entities": ["三清山"], "needs_nearby_search": true, "nearby_type": "food", "expanded_keywords": "三清山美食 三清山餐厅 上饶美食"}}

- 输入: "推荐江西的旅游景点"
  输出: {{"is_travel_related": true, "rewritten_query": "江西 旅游 景点 推荐", "entities": ["江西"], "needs_nearby_search": false, "nearby_type": "all", "expanded_keywords": "江西景点 江西旅游 江西名胜"}}

- 输入: "今天天气怎么样"
  输出: {{"is_travel_related": false, "rewritten_query": "", "entities": [], "needs_nearby_search": false, "nearby_type": "all", "expanded_keywords": ""}}

- 输入: "帮我写一段代码"
  输出: {{"is_travel_related": false, "rewritten_query": "", "entities": [], "needs_nearby_search": false, "nearby_type": "all", "expanded_keywords": ""}}

只返回JSON，不要其他内容：
"""

        logger.info("[QueryRewriter] 📤 Calling LLM for query analysis...")

        # 调用LLM
        response = Generation.call(
            model=settings.QWEN_MODEL,
            prompt=prompt,
            api_key=settings.DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            result_text = response.output.text.strip()
            logger.info(f"[QueryRewriter] 📥 LLM response received")

            # 解析JSON
            try:
                result = json.loads(result_text)

                is_travel_related = result.get("is_travel_related", True)

                # ========== 判断：是否旅游相关 ==========
                if not is_travel_related:
                    logger.warning(f"[QueryRewriter] ⚠️  Non-travel query detected: {user_query}")

                    # 优雅拒绝
                    state["is_travel_related"] = False
                    state["should_skip_retrieval"] = True
                    state["final_answer"] = """非常抱歉，我是专注于旅游领域的智能助手，目前只能回答与旅游、景点、行程规划相关的问题。

如果您有以下方面的需求，我很乐意为您提供帮助：
🗺️  景点推荐和介绍
🚌 旅游路线规划
🏨 住宿和美食建议
📅 最佳旅游时间咨询
💡 当地特色和文化体验

欢迎向我提出任何旅游相关的问题！"""

                    state["sources"] = []
                    state["rewritten_query"] = ""
                    state["expanded_query"] = ""
                    state["entities"] = []
                    state["needs_nearby_search"] = False

                    logger.info("[QueryRewriter] 🚫 Non-travel query, returning rejection message")

                    # 发送node_end事件
                    if session_id:
                        await send_node_end(
                            task_id=session_id,
                            flow_type=FLOW_TYPE,
                            step_id="rewrite",
                            step_name="查询分析",
                            progress=10,
                            message="非旅游问题，已拒绝"
                        )

                    logger.info("=" * 80)
                    logger.success("[QueryRewriter] ✅ Node completed (rejected)")
                    logger.info("=" * 80)

                    return state

                # ========== 旅游相关问题：提取信息 ==========
                state["is_travel_related"] = True
                state["should_skip_retrieval"] = False
                state["rewritten_query"] = result.get("rewritten_query", user_query)
                state["entities"] = result.get("entities", [])
                state["needs_nearby_search"] = result.get("needs_nearby_search", False)
                state["nearby_type"] = result.get("nearby_type", "all")  # 新增：附近推荐类型

                # 查询扩展
                expanded_keywords = result.get("expanded_keywords", "")
                state["expanded_query"] = f"{state['rewritten_query']} {expanded_keywords}".strip()

                logger.success(f"[QueryRewriter] ✅ Travel query confirmed")
                logger.info(f"[QueryRewriter] 📝 Rewritten: {state['rewritten_query']}")
                logger.info(f"[QueryRewriter] 🏷️  Entities: {state['entities']}")
                logger.info(f"[QueryRewriter] 📍 Needs nearby: {state['needs_nearby_search']}")
                logger.info(f"[QueryRewriter] 🏷️  Nearby type: {state['nearby_type']}")
                logger.info(f"[QueryRewriter] 🔍 Expanded: {state['expanded_query']}")

            except json.JSONDecodeError:
                # JSON解析失败，降级处理
                logger.warning("[QueryRewriter] ⚠️  JSON parse failed, using fallback")
                state["is_travel_related"] = True
                state["should_skip_retrieval"] = False
                state["rewritten_query"] = user_query
                state["expanded_query"] = user_query
                state["entities"] = []
                state["needs_nearby_search"] = False
        else:
            # LLM调用失败
            logger.error(f"[QueryRewriter] ❌ LLM call failed: {response.status_code}")
            state["is_travel_related"] = True
            state["should_skip_retrieval"] = False
            state["rewritten_query"] = user_query
            state["expanded_query"] = user_query
            state["entities"] = []
            state["needs_nearby_search"] = False

    except Exception as e:
        logger.error(f"[QueryRewriter] ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        # 降级处理
        state["is_travel_related"] = True
        state["should_skip_retrieval"] = False
        state["rewritten_query"] = user_query
        state["expanded_query"] = user_query
        state["entities"] = []
        state["needs_nearby_search"] = False

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[QueryRewriter] ✅ Query rewriter node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="rewrite",
            step_name="查询分析",
            progress=10,
            message=f"查询分析完成: {state['rewritten_query']}"
        )

    return state
