"""
AI Recommendation API

Real-time AI recommendation using SSE streaming
Integrates with LangGraph workflow for intelligent travel suggestions
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import json
import asyncio

from app.services.ai_recommend_service import get_ai_recommend_service
from app.services.progress_tracker import get_progress_tracker
from app.core.redis_client import get_redis_client
from config.settings import settings

router = APIRouter(prefix="/api/ai-recommend", tags=["AI Recommendation"])


class RecommendRequest(BaseModel):
    """Recommendation request"""
    query: str
    session_id: str
    budget: Optional[str] = None
    season: Optional[str] = None
    travel_type: Optional[str] = None
    duration: Optional[str] = None
    interests: Optional[List[str]] = None


@router.get("/stream")
async def ai_recommend_stream_get(
    query: str,
    session_id: str,
    budget: Optional[str] = None,
    season: Optional[str] = None,
    travel_type: Optional[str] = None,
    duration: Optional[str] = None
):
    """
    AI Recommendation with SSE streaming (GET method for EventSource)

    Real-time progress updates through Server-Sent Events
    Shows detailed workflow execution steps
    """
    try:
        async def event_generator():
            """Generate SSE event stream"""
            try:
                # Initialize progress tracking
                tracker = get_progress_tracker()
                tracker.start_progress(session_id, "AI Recommendation")

                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting AI recommendation workflow'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                # Get AI recommendation service
                service = get_ai_recommend_service()

                # Track nodes for frontend display
                executed_nodes = []

                # Process with workflow
                async for event in service.process_stream(
                    user_query=query,
                    session_id=session_id
                ):
                    # Parse SSE data
                    if event.startswith('data: '):
                        data_str = event[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)

                                # Track node execution
                                if data.get('type') == 'progress' and data.get('node'):
                                    node_name = data.get('node')
                                    executed_nodes.append({
                                        'name': node_name,
                                        'message': data.get('message', ''),
                                        'status': 'success',
                                        'icon': 'Check',
                                        'color': '#67c23a'
                                    })

                                    # Send progress with nodes
                                    progress_event = {
                                        'type': 'progress',
                                        'node': node_name,
                                        'message': data.get('message', ''),
                                        'nodes': executed_nodes.copy()
                                    }
                                    yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

                                elif data.get('type') == 'complete':
                                    # Final result
                                    result = {
                                        'type': 'complete',
                                        'answer': data.get('answer', ''),
                                        'sources': data.get('sources', []),
                                        'nodes': executed_nodes,
                                        'message': 'AI recommendation completed'
                                    }
                                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

                                    # Save to Redis history
                                    try:
                                        redis_client = get_redis_client()
                                        history_key = f"ai_recommend:history:{session_id}"
                                        redis_client.lpush(history_key, json.dumps({
                                            'query': query,
                                            'answer': data.get('answer', ''),
                                            'sources': data.get('sources', []),
                                            'nodes': [{'name': n['name'], 'status': n['status']} for n in executed_nodes],
                                            'timestamp': asyncio.get_event_loop().time()
                                        }, ensure_ascii=False))
                                        redis_client.expire(history_key, 86400)
                                    except Exception as redis_error:
                                        logger.warning(f"Failed to save to Redis: {redis_error}")

                                elif data.get('type') == 'error':
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                            except json.JSONDecodeError:
                                pass

                    # Forward the event
                    yield event

                # Update progress
                tracker.complete_progress(session_id)

            except Exception as e:
                logger.error(f"AI recommendation streaming failed: {e}")
                import traceback
                traceback.print_exc()

                error_data = {
                    'type': 'error',
                    'error': str(e),
                    'message': 'AI recommendation failed'
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"AI recommendation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def ai_recommend_stream(request: RecommendRequest):
    """
    AI Recommendation with SSE streaming

    Real-time progress updates through Server-Sent Events
    Shows detailed workflow execution steps
    """
    try:
        async def event_generator():
            """Generate SSE event stream"""
            try:
                # Initialize progress tracking
                tracker = get_progress_tracker()
                tracker.start_progress(request.session_id, "AI Recommendation")

                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting AI recommendation workflow'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                # Get AI recommendation service
                service = get_ai_recommend_service()

                # Track nodes for frontend display
                executed_nodes = []

                # Process with workflow
                async for event in service.process_stream(
                    user_query=request.query,
                    session_id=request.session_id
                ):
                    # Parse SSE data
                    if event.startswith('data: '):
                        data_str = event[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)

                                # Track node execution
                                if data.get('type') == 'progress' and data.get('node'):
                                    node_name = data.get('node')
                                    executed_nodes.append({
                                        'name': node_name,
                                        'message': data.get('message', ''),
                                        'status': 'success',
                                        'icon': 'Check',
                                        'color': '#67c23a'
                                    })

                                    # Send progress with nodes
                                    progress_event = {
                                        'type': 'progress',
                                        'node': node_name,
                                        'message': data.get('message', ''),
                                        'nodes': executed_nodes.copy()
                                    }
                                    yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

                                elif data.get('type') == 'complete':
                                    # Final result
                                    result = {
                                        'type': 'complete',
                                        'answer': data.get('answer', ''),
                                        'sources': data.get('sources', []),
                                        'nodes': executed_nodes,
                                        'message': 'AI recommendation completed'
                                    }
                                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

                                    # Save to Redis history
                                    try:
                                        redis_client = get_redis_client()
                                        history_key = f"ai_recommend:history:{request.session_id}"
                                        redis_client.lpush(history_key, json.dumps({
                                            'query': request.query,
                                            'answer': data.get('answer', ''),
                                            'sources': data.get('sources', []),
                                            'nodes': [{'name': n['name'], 'status': n['status']} for n in executed_nodes],
                                            'timestamp': asyncio.get_event_loop().time()
                                        }, ensure_ascii=False))
                                        redis_client.expire(history_key, 86400)
                                    except Exception as redis_error:
                                        logger.warning(f"Failed to save to Redis: {redis_error}")

                                elif data.get('type') == 'error':
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                            except json.JSONDecodeError:
                                pass

                    # Forward the event
                    yield event

                # Update progress
                tracker.complete_progress(request.session_id)

            except Exception as e:
                logger.error(f"AI recommendation streaming failed: {e}")
                import traceback
                traceback.print_exc()

                error_data = {
                    'type': 'error',
                    'error': str(e),
                    'message': 'AI recommendation failed'
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"AI recommendation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def ai_recommend_query(request: RecommendRequest):
    """
    触发AI推荐工作流

    接收查询请求，触发LangGraph工作流，通过SSE实时推送进度
    """
    try:
        logger.info(f"[Query] Received request: query={request.query}, session={request.session_id}")

        # ========== 生成task_id ==========
        import time
        task_id = f"task_{int(time.time() * 1000)}_{request.session_id.split('_')[-1]}"
        logger.info(f"[Query] Generated task_id: {task_id}")

        # 保存task_id到Redis（供process_query_async使用）
        from app.core.redis_client import get_redis_client
        redis_client = get_redis_client()
        task_key = f"ai:recommend:current_task:{request.session_id}"
        redis_client.set(task_key, task_id, ex=300)  # 5分钟过期

        # ========== 清空旧的历史事件（避免旧task_id污染） ==========
        events_key = f"ai:recommend:events:{request.session_id}"
        old_count = redis_client.llen(events_key)
        if old_count > 0:
            redis_client.delete(events_key)
            logger.info(f"[Query] Cleared {old_count} old events from {events_key}")
        # ================================================================

        # =================================

        # 在后台启动工作流
        service = get_ai_recommend_service()

        # 异步执行工作流（不等待结果）
        import asyncio
        asyncio.create_task(service.process_query_async(
            query=request.query,
            session_id=request.session_id
        ))

        logger.info(f"[Query] Workflow started for session: {request.session_id}, task: {task_id}")

        return {
            "status": "started",
            "session_id": request.session_id,
            "task_id": task_id,  # 新增：返回task_id给前端
            "message": "AI推荐工作流已启动"
        }

    except Exception as e:
        logger.error(f"[Query] Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{session_id}")
async def ai_recommend_events(session_id: str):
    """
    AI推荐SSE事件流 - 使用Redis Pub/Sub

    类似document workflow的SSE实现
    支持node_start, node_end, complete, error事件
    """
    try:
        async def event_generator():
            """SSE事件生成器 - 使用Redis Pub/Sub"""
            import redis as redis_lib

            redis_client = get_redis_client()
            sent_event_ids = set()

            logger.info(f"[SSE] AI Recommend - Client connected for session: {session_id}")

            # 1. 先订阅Redis Pub/Sub（避免错过实时事件）
            channel = f"ai:recommend:events:{session_id}"

            pubsub_client = redis_lib.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
            pubsub = pubsub_client.pubsub()
            pubsub.subscribe(channel)

            logger.info(f"[SSE] Subscribed to Redis channel: {channel}")

            # 2. 发送历史事件（如果workflow已经执行完成）
            events_key = f"ai:recommend:events:{session_id}"
            historical_events = redis_client.lrange(events_key, 0, -1)

            if historical_events:
                logger.info(f"[SSE] Sending {len(historical_events)} historical events")
                for event_json in historical_events:
                    try:
                        event = json.loads(event_json)
                        event_type = event.get('event_type') or event.get('type')

                        # 调试：如果是complete事件，打印完整内容
                        if event_type == 'complete':
                            logger.info(f"[SSE] DEBUG: Complete event from Redis:")
                            logger.info(f"[SSE]   Keys: {list(event.keys())}")
                            logger.info(f"[SSE]   Has answer: {'answer' in event}")
                            logger.info(f"[SSE]   Answer length: {len(event.get('answer', ''))}")
                            logger.info(f"[SSE]   Event JSON (first 200 chars): {event_json[:200]}")

                        # 根据事件类型发送
                        if event_type == 'node_start':
                            yield f"event: node_start\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        elif event_type == 'node_end':
                            yield f"event: node_end\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        elif event_type == 'result':
                            yield f"event: result\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        elif event_type == 'complete':
                            yield f"event: complete\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        else:
                            yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

                        await asyncio.sleep(0.05)  # 添加延迟，模拟实时
                    except Exception as e:
                        logger.warning(f"[SSE] Failed to send historical event: {e}")

                logger.info(f"[SSE] Finished sending historical events")
            else:
                logger.info(f"[SSE] No historical events found, waiting for real-time events")

            # 3. 监听Pub/Sub消息（继续接收新事件）
            timeout_count = 0
            max_timeout = 3000  # 5分钟

            while timeout_count < max_timeout:
                try:
                    message = pubsub.get_message(timeout=0.1)

                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            event_type = data.get('event_type') or data.get('type')

                            # 跳过无效消息
                            if not event_type:
                                logger.warning(f"[SSE] Skipping message without event_type")
                                continue

                            if 'event_type' not in data:
                                data['event_type'] = event_type

                            step = data.get('step')
                            event_id = f"{event_type}:{step}" if step else f"{event_type}:_"

                            # 跳过重复事件
                            if event_id in sent_event_ids:
                                logger.debug(f"[SSE] Skipping duplicate event: {event_id}")
                                continue

                            sent_event_ids.add(event_id)

                            # 发送SSE事件
                            if event_type == 'node_start':
                                yield f"event: node_start\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.info(f"[SSE] Sent node_start event for step: {step}")
                            elif event_type == 'node_end':
                                yield f"event: node_end\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.info(f"[SSE] Sent node_end event for step: {step}")
                            elif event_type == 'result':
                                # 处理result事件（包含answer）
                                logger.info(f"[SSE] DEBUG: Result event from Pub/Sub:")
                                logger.info(f"[SSE]   Keys: {list(data.keys())}")
                                logger.info(f"[SSE]   Has answer: {'answer' in data}")
                                logger.info(f"[SSE]   Answer length: {len(data.get('answer', ''))}")

                                yield f"event: result\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.success(f"[SSE] Sent result event with answer ({len(data.get('answer', ''))} chars)")
                            elif event_type == 'complete':
                                # 调试：检查complete事件是否有answer
                                logger.info(f"[SSE] DEBUG: Complete event from Pub/Sub:")
                                logger.info(f"[SSE]   Keys: {list(data.keys())}")
                                logger.info(f"[SSE]   Has answer: {'answer' in data}")
                                logger.info(f"[SSE]   Answer length: {len(data.get('answer', ''))}")

                                yield f"event: complete\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.success(f"[SSE] Processing completed for session: {session_id}")
                                break
                            elif event_type == 'error':
                                yield f"event: error\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.error(f"[SSE] Processing failed for session: {session_id}")
                                break
                            else:
                                yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                logger.info(f"[SSE] Sent {event_type} event")

                            timeout_count = 0  # 收到消息后重置超时

                        except json.JSONDecodeError as e:
                            logger.warning(f"[SSE] Failed to parse message: {e}")

                    else:
                        # 没有消息，增加超时计数
                        timeout_count += 1
                        await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"[SSE] Error in event loop: {e}")
                    break

            # 清理
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
                pubsub_client.close()
                logger.info(f"[SSE] Unsubscribed and closed connection for session: {session_id}")
            except Exception as e:
                logger.warning(f"[SSE] Cleanup error: {e}")

            logger.info(f"[SSE] Connection closed for session: {session_id}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"AI recommend events API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "ai_recommend",
        "version": "1.0.0"
    }


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """
    获取会话历史记录

    Args:
        session_id: 会话ID
        limit: 返回的最大记录数

    Returns:
        历史记录列表
    """
    try:
        from app.core.redis_client import get_redis_client
        redis_client = get_redis_client()

        # 从Redis获取历史记录
        history_key = f"ai_recommend:history:{session_id}"

        # lrange获取列表（0到limit-1）
        history_data = redis_client.lrange(history_key, 0, limit - 1)

        if not history_data:
            logger.info(f"[History] No history found for session: {session_id}")
            return {
                "session_id": session_id,
                "history": [],
                "count": 0
            }

        # 解析JSON
        history = []
        for item in history_data:
            try:
                history.append(json.loads(item))
            except json.JSONDecodeError as e:
                logger.error(f"[History] Failed to parse history item: {e}")
                continue

        logger.info(f"[History] Retrieved {len(history)} records for session: {session_id}")

        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"[History] Get history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.delete("/history/{session_id}")
async def delete_history(session_id: str):
    """
    删除会话历史记录

    Args:
        session_id: 会话ID

    Returns:
        删除结果
    """
    try:
        redis_client = get_redis_client()

        # 历史记录key
        history_key = f"ai_recommend:history:{session_id}"

        # 事件key
        events_key = f"ai:recommend:events:{session_id}"

        # 进度key
        progress_key = f"ai:recommend:progress:{session_id}"

        # 删除所有相关key
        deleted_count = 0

        if redis_client.exists(history_key):
            redis_client.delete(history_key)
            deleted_count += 1
            logger.info(f"[History] Deleted history key: {history_key}")

        if redis_client.exists(events_key):
            redis_client.delete(events_key)
            deleted_count += 1
            logger.info(f"[History] Deleted events key: {events_key}")

        if redis_client.exists(progress_key):
            redis_client.delete(progress_key)
            deleted_count += 1
            logger.info(f"[History] Deleted progress key: {progress_key}")

        logger.success(f"[History] Deleted {deleted_count} keys for session: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "deleted_keys": deleted_count,
            "message": f"Successfully deleted history for session {session_id}"
        }

    except Exception as e:
        logger.error(f"[History] Delete history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")
