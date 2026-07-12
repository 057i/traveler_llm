"""
Workflow 工具函数

用于在节点内部发送SSE事件
"""

from loguru import logger
import json
import time


async def send_node_event(
    task_id: str,
    step_id: str,
    step_name: str,
    progress: int,
    message: str,
    event_type: str = "node_start"  # node_start 或 node_end
):
    """
    发送节点事件（node_start 或 node_end）

    Args:
        task_id: 任务ID
        step_id: 步骤ID (minio, parse, chunk, extract, vectorize_traditional, vectorize_graph, finalize)
        step_name: 步骤名称（中文）
        progress: 进度百分比
        message: 消息
        event_type: 事件类型 ("node_start" 或 "node_end")
    """
    from app.core.redis_client import get_redis_client

    status = "processing" if event_type == "node_start" else "completed"

    event_data = {
        "event_type": event_type,
        "step": step_id,
        "step_name": step_name,
        "status": status,
        "message": message,
        "progress": progress,
        "timestamp": time.time()
    }

    redis_client = get_redis_client()

    # 1. 保存到事件列表（历史）
    events_key = f"document:events:{task_id}"
    redis_client.rpush(events_key, json.dumps(event_data, ensure_ascii=False))
    redis_client.expire(events_key, 3600)

    # 2. 保存到progress key（最新进度）
    progress_key = f"document:progress:{task_id}"
    redis_client.set(progress_key, json.dumps(event_data, ensure_ascii=False), ex=3600)

    # 3. 发布到Redis Pub/Sub（实时推送）
    channel = f"document:events:{task_id}"
    try:
        if redis_client.client:
            event_with_type = {"type": event_type, **event_data}
            redis_client.client.publish(
                channel,
                json.dumps(event_with_type, ensure_ascii=False)
            )
            logger.info(f"[Pub/Sub] Published {event_type} for {step_id}")
    except Exception as e:
        logger.warning(f"[Pub/Sub] Failed to publish: {e}")

    logger.info(f"[{event_type.upper()}] {step_name} ({step_id}): {message} ({progress}%)")

    # 添加微小延迟确保Pub/Sub消息顺序
    import asyncio
    await asyncio.sleep(0.001)


async def send_node_start(task_id: str, step_id: str, step_name: str, progress: int, message: str):
    """发送 node_start 事件"""
    await send_node_event(task_id, step_id, step_name, progress, message, "node_start")


async def send_node_end(task_id: str, step_id: str, step_name: str, progress: int, message: str):
    """发送 node_end 事件"""
    await send_node_event(task_id, step_id, step_name, progress, message, "node_end")
