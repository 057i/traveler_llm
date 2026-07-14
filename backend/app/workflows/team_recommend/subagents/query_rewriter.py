"""
Query Rewriter Assistant - 查询重写助手

负责：
1. 获取历史聊天记录
2. 理解用户意图
3. 重写优化查询
4. 判断是否为旅游问题
"""
from .langchain_base import LangChainAgent
from .query_tools import get_chat_history, is_travel_query
from loguru import logger
from typing import Dict, Any


class QueryRewriter(LangChainAgent):
    """查询重写助手 - 理解意图并重写问题"""

    def __init__(self):
        tools = [
            get_chat_history,
            is_travel_query
        ]

        system_prompt = """你是一个查询重写专家，负责理解用户意图并优化查询。

**你的工具：**
1. get_chat_history(session_id, limit) - 获取用户历史聊天记录
2. is_travel_query(query) - 判断是否为旅游相关问题

**工作流程：**

第一步：获取上下文
- 调用 get_chat_history 获取最近3-5条历史记录
- 分析用户的对话历史

第二步：理解意图
- 如果用户说"那里"、"它"、"附近"等代词，结合历史找到指代对象
- 识别用户真正想问什么

第三步：判断问题类型
- 调用 is_travel_query 判断是否为旅游问题
- 旅游问题包括：景点推荐、行程规划、交通、美食、住宿等
- 非旅游问题：闲聊、天气、新闻、笑话等

第四步：重写查询
- 如果是旅游问题：补充上下文，优化为完整清晰的问题
  例如："那里怎么去？" → "从出发地到三清山怎么去？"

- 如果是闲聊：标记为非旅游问题，准备礼貌回复

**返回格式（JSON）：**
{
  "is_travel_related": true,
  "rewritten_query": "重写后的完整问题",
  "original_intent": "用户意图描述",
  "should_continue": true,
  "friendly_response": "如果是闲聊，这里放回复内容"
}

**注意事项：**
- 保持用户原意，不要过度解读
- 如果历史记录中有明确的地点/景点，优先使用
- 闲聊时要友好礼貌，引导用户提旅游问题
"""

        super().__init__(
            name="查询重写助手",
            system_prompt=system_prompt,
            tools=tools
        )

        logger.info("[Query Rewriter] Initialized with history + intent tools")

    async def rewrite(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """
        重写用户查询

        Args:
            query: 用户原始查询
            session_id: 会话ID

        Returns:
            {
                "is_travel_related": bool,
                "rewritten_query": str,
                "should_continue": bool,
                "friendly_response": str (optional)
            }
        """
        try:
            # 如果没有LangChain，使用简化逻辑
            if not self.agent_executor:
                logger.warning("[Query Rewriter] Using fallback mode")
                return await self._fallback_rewrite(query, session_id)

            # 调用LangChain Agent执行重写
            task = f"""请分析并重写以下查询：

用户查询: {query}
会话ID: {session_id or 'unknown'}

请按照以下步骤：
1. 获取历史记录（如果有session_id）
2. 判断是否为旅游问题
3. 重写查询或准备友好回复

返回JSON格式。"""

            result_text = await self.execute(task)

            # 解析结果
            import json
            import re

            # 尝试从结果中提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 回退：解析失败
                logger.warning("[Query Rewriter] Failed to parse JSON, using fallback")
                return await self._fallback_rewrite(query, session_id)

            logger.info(f"[Query Rewriter] Result: {result}")
            return result

        except Exception as e:
            logger.error(f"[Query Rewriter] Failed: {e}")
            import traceback
            traceback.print_exc()

            # 回退
            return await self._fallback_rewrite(query, session_id)

    async def _fallback_rewrite(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """
        回退模式：简单的重写逻辑

        Args:
            query: 用户查询
            session_id: 会话ID

        Returns:
            重写结果
        """
        try:
            # 调用is_travel_query工具判断
            result_json = await is_travel_query.ainvoke(query)
            import json
            travel_check = json.loads(result_json)

            is_travel = travel_check.get('is_travel_related', True)

            if is_travel:
                # 是旅游问题，进行意图分类
                intent_type = self._classify_intent(query)

                return {
                    "is_travel_related": True,
                    "rewritten_query": query,
                    "original_intent": "旅游咨询",
                    "should_continue": True,
                    "intent_type": intent_type  # 添加意图类型
                }
            else:
                # 是闲聊，返回友好回复
                return {
                    "is_travel_related": False,
                    "rewritten_query": query,
                    "original_intent": "闲聊",
                    "should_continue": False,
                    "friendly_response": "您好！我是旅游推荐助手，专注于帮您规划旅行。如果您有旅游相关的问题，欢迎随时提问！😊",
                    "intent_type": "chitchat"
                }

        except Exception as e:
            logger.error(f"[Query Rewriter] Fallback failed: {e}")
            # 最后的回退：假设是旅游问题
            return {
                "is_travel_related": True,
                "rewritten_query": query,
                "should_continue": True,
                "intent_type": "comprehensive_guide"  # 默认全面攻略
            }

    def _classify_intent(self, query: str) -> str:
        """
        分类用户意图

        Returns:
            - "spot_recommendation": 景点推荐（只要结果列表）
            - "itinerary_planning": 行程规划（需要详细安排）
            - "comprehensive_guide": 全面攻略（需要所有信息）
            - "specific_query:transport": 交通咨询
            - "specific_query:food": 美食咨询
            - "specific_query:budget": 预算咨询
        """
        query_lower = query.lower()

        # 景点推荐关键词
        spot_keywords = ['推荐', '有什么', '哪些景点', '好玩的', '值得去', '介绍', '景点']

        # 行程规划关键词
        itinerary_keywords = ['天', '行程', '安排', '路线', '怎么玩', '游玩顺序']

        # 全面攻略关键词
        comprehensive_keywords = ['攻略', '旅游指南', '完整', '全部', '详细']

        # 特定咨询关键词
        transport_keywords = ['怎么去', '交通', '车', '飞机', '高铁', '到达']
        food_keywords = ['吃', '美食', '餐厅', '特色菜', '小吃']
        budget_keywords = ['预算', '费用', '多少钱', '价格', '花费']

        # 判断逻辑（按优先级）
        if any(kw in query_lower for kw in comprehensive_keywords):
            return "comprehensive_guide"

        if any(kw in query_lower for kw in transport_keywords):
            return "specific_query:transport"

        if any(kw in query_lower for kw in food_keywords):
            return "specific_query:food"

        if any(kw in query_lower for kw in budget_keywords):
            return "specific_query:budget"

        if any(kw in query_lower for kw in itinerary_keywords):
            return "itinerary_planning"

        if any(kw in query_lower for kw in spot_keywords):
            return "spot_recommendation"

        # 默认：如果不确定，归为全面攻略
        return "comprehensive_guide"
