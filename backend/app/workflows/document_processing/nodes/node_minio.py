"""
Node: MinIO Storage

上传文件到MinIO，包括原始PDF和MinerU解析后的文件
"""
from loguru import logger
from ..state import DocumentProcessingState
import os
from pathlib import Path


async def save_to_minio(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 1: Save file to MinIO storage

    逻辑：
    1. 创建同名目录（基于原文件名）
    2. 上传原始PDF（重命名为xx_origin.pdf）
    3. 如果有MinerU解析结果，下载并上传到同目录
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="minio",
            step_name="MinIO存储",
            progress=15,
            message="正在保存文件到MinIO存储..."
        )

    logger.info("[MinIO] Saving file to storage")

    try:
        from app.core.minio_client import get_minio_client

        file_path = state.get('file_path')
        filename = state.get('filename')

        if not file_path or not filename:
            raise ValueError("file_path and filename are required")

        # 获取MinIO客户端
        minio = get_minio_client()

        # 1. 解析文件名，创建目录结构
        # 例如：三清山攻略.pdf -> 三清山攻略/
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1]  # .pdf

        # 2. 重命名原始文件
        # 三清山攻略.pdf -> 三清山攻略_origin.pdf
        origin_filename = f"{name_without_ext}_origin{file_ext}"
        origin_object_name = f"{name_without_ext}/{origin_filename}"

        # 3. 上传原始PDF
        logger.info(f"[MinIO] Uploading original PDF: {origin_object_name}")
        minio.save_file(file_path, origin_object_name)
        logger.success(f"[MinIO] Original PDF uploaded: {origin_object_name}")

        # 2. 上传MinerU完整输出包
        mineru_output_dir = state.get('mineru_output_dir')
        mineru_has_package = state.get('mineru_has_package', False)

        logger.info(f"[MinIO] mineru_output_dir: {mineru_output_dir}")
        logger.info(f"[MinIO] mineru_has_package: {mineru_has_package}")

        if mineru_output_dir and os.path.exists(mineru_output_dir):
            logger.info(f"[MinIO] 开始上传MinerU输出包...")

            # 遍历输出目录，上传所有文件
            file_count = 0
            for root, dirs, files in os.walk(mineru_output_dir):
                for filename in files:
                    local_file = os.path.join(root, filename)

                    # 计算相对路径
                    rel_path = os.path.relpath(local_file, mineru_output_dir)

                    # MinIO对象名称
                    object_name = f"{name_without_ext}/mineru/{rel_path.replace(os.sep, '/')}"

                    # 上传文件
                    try:
                        minio.save_file(local_file, object_name)
                        file_count += 1
                        logger.debug(f"[MinIO] 已上传: {object_name}")
                    except Exception as e:
                        logger.warning(f"[MinIO] 上传失败 {object_name}: {e}")

            logger.success(f"[MinIO] MinerU输出包上传完成（{file_count}个文件）")

            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(mineru_output_dir)
                logger.info(f"[MinIO] 已清理临时目录: {mineru_output_dir}")
            except Exception as e:
                logger.warning(f"[MinIO] 清理临时目录失败: {e}")
        else:
            if not mineru_output_dir:
                logger.info(f"[MinIO] state中没有mineru_output_dir字段")
            elif not os.path.exists(mineru_output_dir):
                logger.warning(f"[MinIO] 输出目录不存在: {mineru_output_dir}")
            else:
                logger.info(f"[MinIO] MinerU没有返回完整输出包，只上传Markdown")

        # 3. 单独上传Markdown文本（方便访问）
        markdown_text = state.get('parsed_text')
        if markdown_text:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as f:
                f.write(markdown_text)
                temp_md_path = f.name

            md_object_name = f"{name_without_ext}/{name_without_ext}.md"
            logger.info(f"[MinIO] 上传Markdown文件: {md_object_name}")
            minio.save_file(temp_md_path, md_object_name)
            os.remove(temp_md_path)
            logger.success(f"[MinIO] Markdown已上传: {md_object_name}")

        # 5. 保存MinIO路径信息到state
        state['minio_success'] = True
        state['minio_path'] = origin_object_name
        state['minio_directory'] = name_without_ext

        logger.success(f"[MinIO] All files saved to directory: {name_without_ext}/")

        # 发送 node_end 事件
        if task_id:
            from ..utils import send_node_end
            await send_node_end(
                task_id=task_id,
                step_id="minio",
                step_name="MinIO存储",
                progress=15,
                message="文件保存成功"
            )

    except Exception as e:
        logger.error(f"[MinIO] Save failed: {e}")
        import traceback
        traceback.print_exc()
        state["minio_success"] = False

    return state


async def minio_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip MinIO storage and use original file path
    """
    logger.warning("[MinIO] Using fallback - using original file path")

    file_path = state.get('file_path')
    state["minio_success"] = True
    state["minio_path"] = file_path

    return state
