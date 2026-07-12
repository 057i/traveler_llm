"""
Node: Finalize

Complete the workflow and update statistics
"""
from loguru import logger
from ..state import DocumentProcessingState


async def finalize(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 7: Finalize workflow

    Updates statistics and completes processing
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="finalize",
            step_name="完成",
            progress=100,
            message="正在完成处理..."
        )

    logger.info("[Finalize] Completing workflow")

    destinations_count = len(state.get('destinations', []))
    chunks_count = len(state.get('chunks', []))

    # Extract statistics
    provinces = set()
    cities = set()
    first_province = None
    first_city = None

    for dest in state.get('destinations', []):
        if dest.get('province'):
            provinces.add(dest['province'])
            if not first_province:
                first_province = dest['province']
        if dest.get('city'):
            cities.add(dest['city'])
            if not first_city:
                first_city = dest['city']

    logger.info(f"[Finalize] Statistics:")
    logger.info(f"  - Destinations: {destinations_count}")
    logger.info(f"  - Provinces: {len(provinces)}")
    logger.info(f"  - Cities: {len(cities)}")
    logger.info(f"  - Chunks: {chunks_count}")

    # Store statistics in state for API response
    state['statistics'] = {
        'destinations_count': destinations_count,
        'provinces_count': len(provinces),
        'cities_count': len(cities),
        'chunks_count': chunks_count,
        'provinces': list(provinces),
        'cities': list(cities),
        'first_province': first_province or '-',
        'first_city': first_city or '-'
    }

    # Update Redis task info with statistics
    task_id = state.get('task_id')
    if task_id:
        try:
            from app.core.redis_client import get_redis_client
            import json

            redis_client = get_redis_client()
            task_key = f"document:task:{task_id}"
            task_data = redis_client.get(task_key)

            if task_data:
                task_info = json.loads(task_data)
                task_info['destinations_count'] = destinations_count
                task_info['province'] = first_province or '-'
                task_info['city'] = first_city or '-'
                task_info['pages_count'] = state.get('pages_count', 0)
                task_info['status'] = 'completed'
                task_info['minio_directory'] = state.get('minio_directory', '')  # 保存MinIO目录名

                redis_client.set(task_key, json.dumps(task_info), ex=86400)  # 24小时
                logger.success(f"[Finalize] Updated task info in Redis: {destinations_count} destinations, {task_info['pages_count']} pages")
        except Exception as e:
            logger.warning(f"[Finalize] Failed to update Redis: {e}")

    state['finalize_success'] = True

    logger.success(f"[Workflow] Completed: {destinations_count} destinations processed")

    # 发送 node_end 事件
    if task_id:
        from ..utils import send_node_end
        await send_node_end(
            task_id=task_id,
            step_id="finalize",
            step_name="完成",
            progress=100,
            message=f"处理完成 ({destinations_count} 个景点)"
        )

    return state
