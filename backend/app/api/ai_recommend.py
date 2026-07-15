"""
AI推荐API

使用SSE流式传输实现实时AI推荐
集成LangGraph工作流实现智能旅行建议
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import json
import asyncio
import time

from app.services.ai_recommend_service import get_ai_recommend_service
from app.services.progress_tracker import get_progress_tracker
from app.core.redis_client import get_redis_client
from config.settings import settings

router = APIRouter(prefix="/api/ai-recommend", tags=["AI推荐"])


class RecommendRequest(BaseModel):
    """推荐请求模型"""
    query: str  # 用户查询内容
    session_id: str  # 会话ID
    budget: Optional[str] = None  # 预算范围
    season: Optional[str] = None  # 旅行季节
    travel_type: Optional[str] = None  # 旅行类型
    duration: Optional[str] = None  # 旅行时长
    interests: Optional[List[str]] = None  # 兴趣标签


@router.post("/query")
async def create_recommendation_query(request: RecommendRequest):
    """
    创建AI推荐查询（异步处理）

    功能：
        - 接收用户查询，立即返回task_id
        - 后台异步执行工作流
        - 通过SSE推送进度和结果到 /events/{session_id}

    参数：
        request: 推荐请求对象

    返回：
        {"task_id": "...", "session_id": "...", "message": "推荐任务已创建"}
    """
    session_id = request.session_id
    query = request.query

    logger.info(f"[API] 收到推荐查询 - 会话: {session_id}, 查询: {query[:50]}...")

    # 生成task_id
    task_id = f"task_{int(time.time() * 1000)}_{session_id.split('_')[-1]}"

    # 保存task_id到Redis（供SSE事件过滤使用）
    redis_client = get_redis_client()
    task_key = f"ai:recommend:current_task:{session_id}"
    redis_client.set(task_key, task_id, ex=300)  # 5分钟过期

    # 清空该session的旧事件（避免SSE推送历史事件）
    events_key = f"ai:recommend:events:{session_id}"
    redis_client.delete(events_key)
    logger.info(f"[API] 已清空旧事件: {events_key}")

    logger.info(f"[API] 生成task_id: {task_id}")

    # 准备用户偏好参数
    preferences = {}
    if request.budget:
        preferences['budget'] = request.budget
    if request.season:
        preferences['season'] = request.season
    if request.travel_type:
        preferences['travel_type'] = request.travel_type
    if request.duration:
        preferences['duration'] = request.duration
    if request.interests:
        preferences['interests'] = request.interests

    # 启动后台异步任务
    ai_service = get_ai_recommend_service()
    asyncio.create_task(ai_service.process_query_async(query, session_id))

    return {
        "task_id": task_id,
        "session_id": session_id,
        "message": "推荐任务已创建，请通过SSE监听进度"
    }


@router.get("/events/{session_id}")
async def stream_recommendation_events(session_id: str):
    """
    SSE事件流端点

    功能：
        - 订阅Redis Pub/Sub频道
        - 实时推送工作流执行事件
        - 支持node_start、node_end、result、complete等事件

    参数：
        session_id: 会话ID

    返回：
        StreamingResponse: SSE事件流
    """
    logger.info(f"[API] SSE连接建立 - 会话: {session_id}")

    async def event_generator():
        """SSE事件生成器"""
        redis_client = get_redis_client()
        events_key = f"ai:recommend:events:{session_id}"

        try:
            # 发送连接成功事件
            yield f"event: connected\ndata: {json.dumps({'message': 'SSE连接已建立'}, ensure_ascii=False)}\n\n"

            # 轮询Redis列表获取事件
            last_index = 0
            timeout_count = 0
            max_timeout = 60  # 最多等待60秒无事件

            while timeout_count < max_timeout:
                # 从Redis列表读取新事件
                events = redis_client.lrange(events_key, last_index, -1)

                if events:
                    for event_data in events:
                        try:
                            if isinstance(event_data, bytes):
                                event_data = event_data.decode('utf-8')

                            event_obj = json.loads(event_data)
                            event_type = event_obj.get('event_type', 'message')

                            # 推送事件
                            yield f"event: {event_type}\ndata: {event_data}\n\n"

                            last_index += 1
                            timeout_count = 0  # 重置超时计数

                            # 如果是complete事件，关闭连接
                            if event_type == 'complete':
                                logger.info(f"[API] SSE推送完成 - 会话: {session_id}")
                                return

                        except json.JSONDecodeError:
                            logger.warning(f"[API] 无法解析事件数据: {event_data}")
                            last_index += 1
                else:
                    # 没有新事件，等待一段时间
                    await asyncio.sleep(0.5)
                    timeout_count += 1

            logger.info(f"[API] SSE超时关闭 - 会话: {session_id}")
            yield f"event: timeout\ndata: {json.dumps({'message': '连接超时'}, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"[API] SSE连接被取消 - 会话: {session_id}")
        except Exception as e:
            logger.error(f"[API] SSE事件流错误: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/stream")
async def create_recommendation_stream(request: RecommendRequest):
    """
    创建AI推荐流式响应

    功能：
        - 接收用户查询和偏好参数
        - 使用LangGraph工作流生成推荐
        - 通过SSE实时推送进度和结果

    参数：
        request: 推荐请求对象，包含查询和用户偏好

    返回：
        StreamingResponse: SSE流式响应

    异常：
        HTTPException: 当推荐服务失败时抛出500错误
    """
    session_id = request.session_id
    query = request.query

    logger.info(f"[API] 收到推荐请求 - 会话: {session_id}, 查询: {query[:50]}...")

    async def event_generator():
        """
        SSE事件生成器

        功能：
            - 生成SSE格式的事件流
            - 实时推送进度更新
            - 推送最终推荐结果
        """
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始处理推荐请求...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            # 获取AI推荐服务
            ai_service = get_ai_recommend_service()

            # 准备用户偏好参数
            preferences = {}
            if request.budget:
                preferences['budget'] = request.budget
            if request.season:
                preferences['season'] = request.season
            if request.travel_type:
                preferences['travel_type'] = request.travel_type
            if request.duration:
                preferences['duration'] = request.duration
            if request.interests:
                preferences['interests'] = request.interests

            logger.info(f"[API] 用户偏好: {preferences}")

            # 定义进度回调函数
            async def progress_callback(event):
                """
                进度回调函数

                功能：
                    - 接收工作流的进度事件
                    - 转换为SSE格式推送给客户端

                参数：
                    event: 进度事件字典
                """
                try:
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"[API] 进度回调错误: {e}")

            # 执行AI推荐
            result = await ai_service.recommend(
                query=query,
                session_id=session_id,
                preferences=preferences,
                progress_callback=progress_callback
            )

            # 推送最终结果
            if result.get('status') == 'success':
                final_event = {
                    'type': 'complete',
                    'data': result,
                    'message': '推荐完成'
                }
                yield f"data: {json.dumps(final_event, ensure_ascii=False)}\n\n"
                logger.success(f"[API] 推荐完成 - 会话: {session_id}")
            else:
                error_event = {
                    'type': 'error',
                    'message': result.get('message', '推荐失败'),
                    'error': result.get('error', 'Unknown error')
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                logger.error(f"[API] 推荐失败 - 会话: {session_id}, 错误: {result.get('error')}")

            # 发送结束事件
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[API] 推荐流处理异常: {e}", exc_info=True)
            error_event = {
                'type': 'error',
                'message': '推荐服务异常',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/progress/{session_id}")
async def get_recommendation_progress(session_id: str):
    """
    获取推荐进度

    功能：
        - 查询指定会话的推荐进度
        - 返回当前进度百分比和状态

    参数：
        session_id: 会话ID

    返回：
        dict: 包含进度信息的字典
            - session_id: 会话ID
            - progress: 进度百分比(0-100)
            - status: 当前状态
            - message: 状态消息

    异常：
        HTTPException: 当获取进度失败时抛出500错误
    """
    try:
        logger.info(f"[API] 获取推荐进度 - 会话: {session_id}")

        progress_tracker = get_progress_tracker()
        progress = progress_tracker.get_progress(session_id)

        if progress:
            return {
                "session_id": session_id,
                "progress": progress.get('progress', 0),
                "status": progress.get('status', 'unknown'),
                "message": progress.get('message', ''),
                "timestamp": progress.get('timestamp')
            }
        else:
            return {
                "session_id": session_id,
                "progress": 0,
                "status": "not_found",
                "message": "未找到该会话的进度信息"
            }

    except Exception as e:
        logger.error(f"[API] 获取进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_recommendation_history(session_id: str):
    """
    获取推荐历史

    功能：
        - 查询指定会话的历史推荐记录
        - 包含对话历史和推荐结果

    参数：
        session_id: 会话ID

    返回：
        dict: 包含历史记录的字典
            - session_id: 会话ID
            - history: 对话历史列表
            - last_result: 最后一次推荐结果

    异常：
        HTTPException: 当获取历史失败时抛出500错误
    """
    try:
        logger.info(f"[API] 获取推荐历史 - 会话: {session_id}")

        redis_client = get_redis_client()
        history_key = f"ai_recommend:history:{session_id}"

        # 从Redis List获取历史记录（使用lrange而不是get）
        history_items = redis_client.lrange(history_key, 0, -1)

        if history_items:
            # 解析每条历史记录
            history = []
            for item in history_items:
                try:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8')
                    history.append(json.loads(item))
                except json.JSONDecodeError as e:
                    logger.warning(f"[API] 解析历史记录失败: {e}")
                    continue

            return {
                "session_id": session_id,
                "history": history,
                "count": len(history),
                "message": f"成功加载{len(history)}条历史记录"
            }
        else:
            return {
                "session_id": session_id,
                "history": [],
                "count": 0,
                "message": "该会话暂无历史记录"
            }

    except Exception as e:
        logger.error(f"[API] 获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.delete("/history/{session_id}")
async def delete_recommendation_history(session_id: str):
    """
    删除推荐历史

    功能：
        - 删除指定会话的所有历史记录
        - 清理Redis中的相关键值

    参数：
        session_id: 会话ID

    返回：
        dict: 删除结果
            - success: 是否成功
            - session_id: 会话ID
            - deleted_keys: 删除的键数量
            - message: 结果消息

    异常：
        HTTPException: 当删除失败时抛出500错误
    """
    try:
        logger.info(f"[API] 删除推荐历史 - 会话: {session_id}")

        redis_client = get_redis_client()
        deleted_count = 0

        # 删除各类历史键（直接删除，不检查存在性）
        history_key = f"ai_recommend:history:{session_id}"
        events_key = f"ai_recommend:events:{session_id}"
        progress_key = f"ai_recommend:progress:{session_id}"
        task_key = f"ai:recommend:current_task:{session_id}"

        # Redis的delete命令可以接受多个键，不存在的键会被忽略
        deleted_count = redis_client.delete(history_key, events_key, progress_key, task_key)

        logger.success(f"[历史] 已删除 {deleted_count} 个键 - 会话: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "deleted_keys": deleted_count,
            "message": f"成功删除会话 {session_id} 的历史记录"
        }

    except Exception as e:
        logger.error(f"[历史] 删除历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除历史失败: {str(e)}")
