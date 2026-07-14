"""
Query处理工具

1. 获取历史聊天记录
2. 判断是否为旅游问题
"""
from typing import List, Optional
from loguru import logger
import json

try:
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available, using fallback decorator")
    LANGCHAIN_AVAILABLE = False

    def tool(func):
        func.name = func.__name__
        func.description = func.__doc__
        async def ainvoke(args):
            if isinstance(args, dict):
                return await func(**args)
            else:
                return await func(args)
        func.ainvoke = ainvoke
        return func


@tool
async def get_chat_history(session_id: str, limit: int = 5) -> str:
    """
    获取用户历史聊天记录

    Args:
        session_id: 会话ID
        limit: 获取最近N条记录，默认5条

    Returns:
        JSON字符串，包含历史对话
    """
    logger.info(f"[Tool] get_chat_history called: session_id={session_id}, limit={limit}")

    try:
        from app.services.redis_chat_history import get_redis_chat_history

        redis_history = get_redis_chat_history()

        # 获取历史记录
        response = await redis_history.get_chat_history(session_id, limit)

        if not response or not response.get('messages'):
            return json.dumps({
                "success": True,
                "count": 0,
                "messages": [],
                "summary": "没有历史记录"
            }, ensure_ascii=False)

        # 格式化历史记录
        messages = response.get('messages', [])
        formatted = []

        for msg in messages[-limit:]:  # 只取最近N条
            formatted.append({
                "role": msg.get('type', 'user'),  # user or assistant
                "content": msg.get('content', '')[:200],  # 限制长度
                "timestamp": msg.get('timestamp', '')
            })

        result = {
            "success": True,
            "count": len(formatted),
            "messages": formatted,
            "summary": f"最近{len(formatted)}条对话"
        }

        logger.success(f"[Tool] get_chat_history: found {len(formatted)} messages")

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] get_chat_history failed: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": str(e),
            "count": 0,
            "messages": []
        }, ensure_ascii=False)


@tool
async def is_travel_query(query: str) -> str:
    """
    判断是否为旅游相关问题

    Args:
        query: 用户查询

    Returns:
        JSON字符串，包含判断结果
    """
    logger.info(f"[Tool] is_travel_query called: query='{query}'")

    try:
        # 旅游相关关键词
        travel_keywords = [
            '景点', '旅游', '攻略', '游玩', '推荐', '路线', '行程',
            '酒店', '住宿', '门票', '美食', '特产', '交通', '怎么去',
            '好玩', '值得', '附近', '周边', '几天', '预算', '费用',
            '山', '寺', '湖', '岛', '古镇', '公园', '博物馆', '风景',
            '玩', '逛', '看', '去', '爬', '游', '观光', '旅行'
        ]

        # 闲聊关键词
        chitchat_keywords = [
            '你好', 'hello', 'hi', '天气', '笑话', '故事', '新闻',
            '聊天', '陪我', '你是谁', '你叫什么', '你会什么',
            '唱歌', '跳舞', '做饭', '游戏', '电影', '音乐',
            '再见', '拜拜', '谢谢', '不客气'
        ]

        query_lower = query.lower()

        # 检查旅游关键词
        travel_score = sum(1 for kw in travel_keywords if kw in query_lower)

        # 检查闲聊关键词
        chitchat_score = sum(1 for kw in chitchat_keywords if kw in query_lower)

        # 判断逻辑：
        # 1. 如果有旅游关键词，判定为旅游问题
        # 2. 如果有闲聊关键词且无旅游关键词，判定为闲聊
        # 3. 其他情况默认为旅游问题（宽松策略）
        is_travel = travel_score > 0 or (travel_score == 0 and chitchat_score == 0)

        result = {
            "success": True,
            "is_travel_related": is_travel,
            "travel_score": travel_score,
            "chitchat_score": chitchat_score,
            "confidence": 0.9 if travel_score > 0 else (0.2 if chitchat_score > 0 else 0.6),
            "reason": f"旅游关键词匹配: {travel_score}, 闲聊关键词匹配: {chitchat_score}"
        }

        logger.info(f"[Tool] is_travel_query: {result}")

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] is_travel_query failed: {e}")
        return json.dumps({
            "success": False,
            "is_travel_related": True,  # 出错时假设是旅游问题
            "error": str(e)
        }, ensure_ascii=False)
