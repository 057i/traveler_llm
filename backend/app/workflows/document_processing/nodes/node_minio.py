"""
Node: MinIO Storage

上传文件到MinIO，包括原始PDF
"""
from loguru import logger
from ..state import DocumentProcessingState
import os
from pathlib import Path
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_prepare_paths(filename: str, file_path: str) -> dict:
    """
    Step 1: 准备文件路径和MinIO对象名称

    Args:
        filename: 原始文件名 (如: 三清山攻略.pdf)
        file_path: 本地文件路径

    Returns:
        包含目录名、对象名等信息的字典
    """
    name_without_ext = Path(filename).stem
    file_ext = Path(filename).suffix

    # MinIO目录结构: 三清山攻略/三清山攻略_origin.pdf
    directory = name_without_ext
    origin_filename = f"{name_without_ext}_origin{file_ext}"
    origin_object_name = f"{directory}/{origin_filename}"

    logger.info(f"[MinIO] Directory: {directory}")
    logger.info(f"[MinIO] Object name: {origin_object_name}")

    return {
        'directory': directory,
        'origin_object_name': origin_object_name,
        'file_path': file_path
    }


def step2_upload_original_pdf(minio, file_path: str, object_name: str):
    """
    Step 2: 上传原始PDF到MinIO

    Args:
        minio: MinIO客户端
        file_path: 本地PDF文件路径
        object_name: MinIO对象名称
    """
    logger.info(f"[MinIO] Uploading original PDF: {object_name}")
    minio.save_file(file_path, object_name)
    logger.success(f"[MinIO] Original PDF uploaded successfully")


# ==================== 主节点函数 ====================

async def save_to_minio(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 保存文件到MinIO存储

    流程:
        1. 准备文件路径和MinIO对象名
        2. 上传原始PDF（重命名为xx_origin.pdf）
        3. Markdown文档将在finalize节点保存

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
            step_id="minio",
            step_name="MinIO存储",
            progress=15,
            message="正在保存文件到MinIO存储..."
        )

    logger.info("[MinIO] === Starting MinIO upload ===")

    try:
        from app.core.minio_client import get_minio_client

        file_path = state.get('file_path')
        filename = state.get('filename')

        # 验证必需参数
        if not file_path or not filename:
            raise ValueError("file_path and filename are required")

        # 获取MinIO客户端
        minio = get_minio_client()

        # Step 1: 准备路径
        paths = step1_prepare_paths(filename, file_path)

        # Step 2: 上传原始PDF
        step2_upload_original_pdf(
            minio,
            paths['file_path'],
            paths['origin_object_name']
        )

        # 保存结果到state
        state['minio_success'] = True
        state['minio_path'] = paths['origin_object_name']
        state['minio_directory'] = paths['directory']

        logger.success(f"[MinIO] === Upload completed: {paths['directory']}/ ===")
        logger.info(f"[MinIO] Markdown将在finalize节点保存")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="minio",
                step_name="MinIO存储",
                progress=15,
                message="文件保存成功"
            )

    except Exception as e:
        logger.error(f"[MinIO] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        state["minio_success"] = False

    return state


async def minio_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: 跳过MinIO存储，直接使用原始文件路径
    """
    logger.warning("[MinIO] Using fallback - using original file path")

    file_path = state.get('file_path')
    state["minio_success"] = True
    state["minio_path"] = file_path

    return state
