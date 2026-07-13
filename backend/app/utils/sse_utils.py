"""
Common SSE Event Utilities

统一的SSE事件发送工具，支持所有workflow类型
"""
from loguru import logger
import json
import time


async def send_node_event(
    task_id: str,
    flow_type: str,
    event_type: str,
    step_id: str,
    step_name: str,
    progress: int,
    message: str
):
    """
    发送节点事件到Redis

    Args:
        task_id: 任务ID (document: 文档task_id, ai_recommend: session_id)
        flow_type: 工作流类型 ("document" 或 "ai_recommend")
        event_type: 事件类型 ("node_start" 或 "node_end")
        step_id: 步骤ID
        step_name: 步骤名称
        progress: 进度百分比 (0-100)
        message: 消息内容
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

    # 根据flow_type构建Redis key
    if flow_type == "document":
        events_key = f"document:events:{task_id}"
        progress_key = f"document:progress:{task_id}"
    elif flow_type == "ai_recommend":
        events_key = f"ai:recommend:events:{task_id}"
        progress_key = f"ai:recommend:progress:{task_id}"
    else:
        raise ValueError(f"Unknown flow_type: {flow_type}")

    # ========== 获取当前task_id（如果存在） ==========
    # 使用已经创建的redis_client（第46行）
    task_key = f"ai:recommend:current_task:{task_id}"
    current_task_id = redis_client.get(task_key)
    if current_task_id:
        current_task_id = current_task_id.decode('utf-8') if isinstance(current_task_id, bytes) else current_task_id
        event_data['task_id'] = current_task_id  # 添加task_id到事件数据
        logger.info(f"[SSE] [{flow_type}] 📌 Added task_id: {current_task_id}")
    # ================================================

    # 记录发送时间
    send_time = time.time()
    logger.info(f"[SSE] [{flow_type}] ⏱️ SEND at {send_time:.3f} | {event_type} - {step_name}")

    # 1. 保存事件到列表 (历史记录)
    redis_client.rpush(events_key, json.dumps(event_data, ensure_ascii=False))
    redis_client.expire(events_key, 3600)

    # 2. 保存到progress key (最新进度)
    redis_client.set(progress_key, json.dumps(event_data, ensure_ascii=False), ex=3600)

    # 3. 发布到Redis Pub/Sub (实时推送)
    redis_client.publish(events_key, json.dumps(event_data, ensure_ascii=False))

    logger.info(f"[SSE] [{flow_type}] ✅ PUBLISHED | {event_type} - {step_name}")


async def send_node_start(
    task_id: str,
    flow_type: str,
    step_id: str,
    step_name: str,
    progress: int,
    message: str
):
    """发送node_start事件"""
    await send_node_event(
        task_id=task_id,
        flow_type=flow_type,
        event_type="node_start",
        step_id=step_id,
        step_name=step_name,
        progress=progress,
        message=message
    )


async def send_node_end(
    task_id: str,
    flow_type: str,
    step_id: str,
    step_name: str,
    progress: int,
    message: str
):
    """发送node_end事件"""
    await send_node_event(
        task_id=task_id,
        flow_type=flow_type,
        event_type="node_end",
        step_id=step_id,
        step_name=step_name,
        progress=progress,
        message=message
    )


async def send_complete_event(
    task_id: str,
    flow_type: str,
    message: str,
    answer: str = None,
    sources: list = None
):
    """发送完成事件，可选包含答案和来源"""
    from app.core.redis_client import get_redis_client

    # 添加详细调试日志
    logger.info(f"[SSE] send_complete_event called")
    logger.info(f"[SSE]   task_id: {task_id}")
    logger.info(f"[SSE]   answer: {repr(answer)}")
    logger.info(f"[SSE]   answer type: {type(answer)}")
    logger.info(f"[SSE]   answer length: {len(answer) if answer else 0}")
    logger.info(f"[SSE]   sources count: {len(sources) if sources else 0}")

    event_data = {
        "event_type": "complete",
        "message": message,
        "timestamp": time.time()
    }

    # 如果有答案和来源，添加到事件中
    if answer is not None:
        logger.info(f"[SSE] ✅ Adding answer to event_data (length: {len(answer)})")
        event_data["answer"] = answer
    else:
        logger.warning(f"[SSE] ⚠️ answer is None, not adding to event_data")

    if sources is not None:
        logger.info(f"[SSE] ✅ Adding sources to event_data (count: {len(sources)})")
        event_data["sources"] = sources
    else:
        logger.warning(f"[SSE] ⚠️ sources is None, not adding to event_data")

    logger.info(f"[SSE] Final event_data keys: {list(event_data.keys())}")
    logger.info(f"[SSE] Final event_data: {json.dumps(event_data, ensure_ascii=False)[:200]}...")

    redis_client = get_redis_client()

    if flow_type == "document":
        events_key = f"document:events:{task_id}"
    elif flow_type == "ai_recommend":
        events_key = f"ai:recommend:events:{task_id}"
    else:
        raise ValueError(f"Unknown flow_type: {flow_type}")

    redis_client.rpush(events_key, json.dumps(event_data, ensure_ascii=False))
    redis_client.publish(events_key, json.dumps(event_data, ensure_ascii=False))

    logger.success(f"[SSE] [{flow_type}] complete" + (f" with answer ({len(answer)} chars)" if answer else ""))


async def send_error_event(
    task_id: str,
    flow_type: str,
    error_message: str
):
    """发送错误事件"""
    from app.core.redis_client import get_redis_client

    event_data = {
        "event_type": "error",
        "message": error_message,
        "timestamp": time.time()
    }

    redis_client = get_redis_client()

    if flow_type == "document":
        events_key = f"document:events:{task_id}"
    elif flow_type == "ai_recommend":
        events_key = f"ai:recommend:events:{task_id}"
    else:
        raise ValueError(f"Unknown flow_type: {flow_type}")

    redis_client.rpush(events_key, json.dumps(event_data, ensure_ascii=False))
    redis_client.publish(events_key, json.dumps(event_data, ensure_ascii=False))

    logger.error(f"[SSE] [{flow_type}] error")
