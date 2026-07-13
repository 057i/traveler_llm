"""
Node: Finalize

Complete the workflow and update statistics
"""
from loguru import logger
from ..state import DocumentProcessingState
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_calculate_statistics(destinations: list) -> dict:
    """
    Step 1: 计算统计信息

    Args:
        destinations: 景点列表

    Returns:
        统计信息字典
    """
    provinces = set()
    cities = set()
    first_province = None
    first_city = None

    for dest in destinations:
        if dest.get('province'):
            provinces.add(dest['province'])
            if not first_province:
                first_province = dest['province']
        if dest.get('city'):
            cities.add(dest['city'])
            if not first_city:
                first_city = dest['city']

    stats = {
        'destinations_count': len(destinations),
        'provinces_count': len(provinces),
        'cities_count': len(cities),
        'first_province': first_province or '-',
        'first_city': first_city or '-',
        'provinces_list': list(provinces),
        'cities_list': list(cities)
    }

    logger.info(f"[Finalize] Statistics:")
    logger.info(f"  - Destinations: {stats['destinations_count']}")
    logger.info(f"  - Provinces: {stats['provinces_count']}")
    logger.info(f"  - Cities: {stats['cities_count']}")

    return stats


def step2_update_redis(task_id: str, stats: dict, pages_count: int, minio_directory: str):
    """
    Step 2: 更新Redis中的任务信息

    Args:
        task_id: 任务ID
        stats: 统计信息
        pages_count: 页数
        minio_directory: MinIO目录名
    """
    from app.core.redis_client import get_redis_client
    import json

    redis_client = get_redis_client()
    task_key = f"document:task:{task_id}"
    task_data = redis_client.get(task_key)

    if task_data:
        task_info = json.loads(task_data)
        task_info['destinations_count'] = stats['destinations_count']
        task_info['province'] = stats['first_province']
        task_info['city'] = stats['first_city']
        task_info['pages_count'] = pages_count
        task_info['status'] = 'completed'
        task_info['minio_directory'] = minio_directory

        redis_client.set(task_key, json.dumps(task_info), ex=86400)  # 24小时
        logger.success(
            f"[Finalize] Updated Redis: {stats['destinations_count']} destinations, "
            f"{pages_count} pages"
        )


def step3_save_markdown_to_minio(minio_directory: str, parsed_text: str):
    """
    Step 3: 保存Markdown文档到MinIO

    Args:
        minio_directory: MinIO目录名
        parsed_text: Markdown文本内容
    """
    from app.core.minio_client import get_minio_client
    import os

    minio = get_minio_client()

    # Markdown文件名
    md_object_name = f"{minio_directory}/{minio_directory}.md"

    # 创建临时文件
    temp_dir = "./data/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_md_path = os.path.join(temp_dir, f"{minio_directory}.md")

    # 写入markdown内容
    with open(temp_md_path, 'w', encoding='utf-8') as f:
        f.write(parsed_text)

    # 上传到MinIO
    minio.save_file(temp_md_path, md_object_name)

    # 删除临时文件
    os.remove(temp_md_path)

    logger.success(f"[Finalize] Markdown saved to MinIO: {md_object_name}")


# ==================== 主节点函数 ====================

async def finalize(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 完成处理并更新统计

    流程:
        1. 计算统计信息（景点数、省份数、城市数等）
        2. 更新Redis中的任务信息
        3. 保存Markdown文档到MinIO

    Args:
        state: 工作流状态

    Returns:
        更新后的状态
    """
    task_id = state.get('task_id')

    # 发送node_start事件
    if task_id:
        await send_node_start(
            task_id=task_id,
            flow_type=FLOW_TYPE,
            step_id="finalize",
            step_name="完成",
            progress=100,
            message="正在完成处理..."
        )

    logger.info("[Finalize] === Finalizing workflow ===")

    try:
        destinations = state.get('destinations', [])
        chunks_count = len(state.get('chunks', []))

        # Step 1: 计算统计信息
        stats = step1_calculate_statistics(destinations)

        # Step 2: 更新Redis
        if task_id:
            try:
                step2_update_redis(
                    task_id,
                    stats,
                    state.get('pages_count', 0),
                    state.get('minio_directory', '')
                )

                # Step 3: 保存Markdown到MinIO
                minio_directory = state.get('minio_directory')
                parsed_text = state.get('parsed_text', '')

                if minio_directory and parsed_text:
                    try:
                        step3_save_markdown_to_minio(minio_directory, parsed_text)
                    except Exception as md_err:
                        logger.warning(f"[Finalize] Failed to save markdown: {md_err}")

            except Exception as e:
                logger.warning(f"[Finalize] Failed to update Redis: {e}")

        # 保存统计信息到state
        state['finalize_success'] = True
        state['statistics'] = stats

        logger.success(
            f"[Finalize] === Workflow completed: {stats['destinations_count']} destinations ==="
        )

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="finalize",
                step_name="完成",
                progress=100,
                message=f"处理完成 ({stats['destinations_count']} 个景点)"
            )

    except Exception as e:
        logger.error(f"[Finalize] Finalization failed: {e}")
        import traceback
        traceback.print_exc()
        state['finalize_success'] = False

    return state
