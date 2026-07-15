"""
AI团队推荐 WebSocket API - 增强版

功能：
- 实时AI团队推荐，支持详细的进度追踪
- 多智能体协作（预算专家、行程规划师、美食助手、交通助手、RAG助手）
- WebSocket双向通信，实时推送每个智能体的工作状态
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import json

router = APIRouter(prefix="/api/team-recommend-ws", tags=["AI团队推荐"])


@router.websocket("/stream")
async def team_recommend_websocket(websocket: WebSocket):
    """
    AI团队推荐WebSocket端点（增强进度追踪）

    功能：
        - 接收客户端的查询请求
        - 实时推送多个AI智能体的工作进度
        - 流式返回最终推荐结果
        - 支持会话管理和历史记录

    推送的智能体进度：
        - 查询重写助手：分析和优化用户查询
        - RAG助手：检索相关旅游信息
        - 图RAG助手：检索景点关系信息
        - 预算专家：分析预算和费用
        - 行程规划师：规划详细行程
        - 美食助手：推荐当地美食
        - 交通助手：规划交通路线

    消息格式：
        客户端发送：
            {
                "query": "用户查询内容",
                "session_id": "会话ID"
            }

        服务端推送：
            进度更新：
                {
                    "type": "progress",
                    "agent": "智能体名称",
                    "status": "working|completed|error",
                    "message": "状态消息",
                    "progress": 进度百分比,
                    "detail": "详细信息"
                }

            最终答案：
                {
                    "type": "answer",
                    "answer": "推荐内容",
                    "sources": ["来源列表"],
                    "metadata": {},
                    "agent_logs": []
                }

            完成：
                {
                    "type": "complete",
                    "message": "AI团队推荐完成",
                    "progress": 100
                }

            错误：
                {
                    "type": "error",
                    "message": "错误消息",
                    "error": "错误详情"
                }

    异常处理：
        - WebSocketDisconnect: 客户端断开连接
        - Exception: 其他异常，发送错误消息
    """
    await websocket.accept()
    logger.info("[团队推荐WS] 客户端已连接")

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get('query', '')
            session_id = message.get('session_id')

            logger.info(f"[团队推荐WS] 收到查询: {query[:50]}...")

            # 发送初始化消息
            await websocket.send_json({
                "type": "start",
                "message": "AI团队正在分析您的需求",
                "timestamp": None
            })

            # 调用团队推荐服务
            try:
                from app.services.team_recommend_service import get_team_recommend_service

                service = get_team_recommend_service()

                # 流式返回结果
                async for progress_update in service.recommend_stream(
                    query=query,
                    session_id=session_id
                ):
                    # 增强的进度消息格式化
                    if progress_update.get('type') == 'progress':
                        # 智能体进度更新
                        agent_name = progress_update.get('agent', '未知智能体')
                        status = progress_update.get('status', 'working')
                        message_text = progress_update.get('message', '')
                        progress_value = progress_update.get('progress', 0)

                        # 映射状态到用户友好的消息
                        status_messages = {
                            'started': f'{agent_name} 开始分析',
                            'working': f'{agent_name}: {message_text}',
                            'completed': f'{agent_name} 已完成',
                            'error': f'{agent_name} 遇到问题'
                        }

                        await websocket.send_json({
                            "type": "progress",
                            "agent": agent_name,
                            "status": status,
                            "message": status_messages.get(status, message_text),
                            "progress": progress_value,
                            "detail": message_text
                        })

                    elif progress_update.get('type') == 'answer':
                        # 收到最终答案
                        await websocket.send_json({
                            "type": "answer",
                            "answer": progress_update.get('answer', ''),
                            "sources": progress_update.get('sources', []),
                            "metadata": progress_update.get('metadata', {}),
                            "agent_logs": progress_update.get('agent_logs', [])
                        })

                    elif progress_update.get('type') == 'complete':
                        # 完成消息
                        await websocket.send_json({
                            "type": "complete",
                            "message": "AI团队推荐完成",
                            "progress": 100
                        })

                    elif progress_update.get('type') == 'error':
                        # 错误消息
                        await websocket.send_json({
                            "type": "error",
                            "message": progress_update.get('message', '发生错误'),
                            "error": progress_update.get('error', '')
                        })

            except Exception as e:
                logger.error(f"[团队推荐WS] 服务错误: {e}")
                import traceback
                traceback.print_exc()

                await websocket.send_json({
                    "type": "error",
                    "message": "处理推荐失败",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        logger.info("[团队推荐WS] 客户端已断开连接")
    except Exception as e:
        logger.error(f"[团队推荐WS] 连接错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "WebSocket连接错误",
                "error": str(e)
            })
        except:
            pass


@router.get("/health")
async def health():
    """
    健康检查接口

    功能：
        - 检查团队推荐WebSocket服务是否正常运行
        - 返回服务状态和版本信息

    返回：
        dict: 健康状态
            - status: 状态 'ok'
            - service: 服务名称
            - version: 版本号
    """
    return {
        "status": "ok",
        "service": "team_recommend_ws",
        "version": "1.0.0"
    }


@router.get("/history/{session_id}")
async def get_team_recommend_history(session_id: str):
    """
    获取AI团队推荐历史记录

    功能：
        - 查询指定会话的历史记录
        - 返回用户查询和AI回复的消息列表

    参数：
        session_id: 会话ID

    返回：
        dict: 包含历史记录的字典
            - session_id: 会话ID
            - messages: 消息列表
            - count: 消息数量
    """
    try:
        from app.core.redis_client import get_redis_client

        logger.info(f"[团队推荐] 获取历史记录 - 会话: {session_id}")

        redis_client = get_redis_client()
        history_key = f"team_recommend:history:{session_id}"

        # 从Redis List获取历史记录
        history_items = redis_client.lrange(history_key, 0, -1)

        if history_items:
            # 解析每条历史记录
            messages = []
            for item in history_items:
                try:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8')
                    messages.append(json.loads(item))
                except json.JSONDecodeError as e:
                    logger.warning(f"[团队推荐] 解析历史记录失败: {e}")
                    continue

            return {
                "session_id": session_id,
                "messages": messages,
                "count": len(messages),
                "message": f"成功加载{len(messages)}条历史记录"
            }
        else:
            return {
                "session_id": session_id,
                "messages": [],
                "count": 0,
                "message": "该会话暂无历史记录"
            }

    except Exception as e:
        logger.error(f"[团队推荐] 获取历史失败: {e}")
        return {
            "session_id": session_id,
            "messages": [],
            "count": 0,
            "message": f"获取历史失败: {str(e)}"
        }


@router.delete("/history/{session_id}")
async def delete_team_recommend_history(session_id: str):
    """
    删除AI团队推荐历史记录

    功能：
        - 删除指定会话的所有历史记录

    参数：
        session_id: 会话ID

    返回：
        dict: 删除结果
    """
    try:
        from app.core.redis_client import get_redis_client

        logger.info(f"[团队推荐] 删除历史记录 - 会话: {session_id}")

        redis_client = get_redis_client()
        history_key = f"team_recommend:history:{session_id}"

        deleted_count = redis_client.delete(history_key)

        logger.success(f"[团队推荐] 已删除 {deleted_count} 个键 - 会话: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "deleted_keys": deleted_count,
            "message": f"成功删除会话 {session_id} 的历史记录"
        }

    except Exception as e:
        logger.error(f"[团队推荐] 删除历史失败: {e}")
        return {
            "success": False,
            "session_id": session_id,
            "message": f"删除历史失败: {str(e)}"
        }
