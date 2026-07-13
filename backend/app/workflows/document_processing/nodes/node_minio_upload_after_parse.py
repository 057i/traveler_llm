"""
Node: Upload to MinIO (After PDF Parsing)

在PDF解析完成后，上传所有文件到MinIO
"""
from loguru import logger
from pathlib import Path
from ..state import DocumentProcessingState
from app.utils.sse_utils import send_node_start, send_node_end
from app.core.minio_client import get_minio_client
from app.utils.temp_file_manager import get_temp_file_manager
from config.settings import settings

FLOW_TYPE = "document"


async def upload_to_minio_after_parse(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 解析后上传到MinIO

    上传内容：
    1. 原始PDF文件
    2. 解析后的Markdown文件
    3. 提取的图片文件夹

    MinIO路径：travel-documents/{doc_name}/
    """
    task_id = state.get('task_id')
    doc_id = state.get('doc_id')
    filename = state.get('filename')

    # 发送node_start事件
    if task_id:
        await send_node_start(
            task_id=task_id,
            flow_type=FLOW_TYPE,
            step_id="upload_minio",
            step_name="上传MinIO",
            progress=35,
            message="正在上传文件到对象存储..."
        )

    logger.info("[UploadMinIO] === Starting MinIO upload after parsing ===")

    try:
        minio_client = get_minio_client()
        temp_manager = get_temp_file_manager()

        # 获取临时目录
        temp_dir = temp_manager.get_temp_dir(doc_id)
        if not temp_dir:
            raise Exception(f"Temp directory not found for {doc_id}")

        # MinIO路径：travel-documents/{filename}/
        bucket = settings.MINIO_BUCKET
        folder = f"{filename}/"

        uploaded_files = []

        # 1. 上传原始PDF
        pdf_path = temp_dir / state.get('original_filename', f"{filename}.pdf")
        if pdf_path.exists():
            minio_path = f"{folder}{filename}_origin.pdf"
            minio_client.save_file(str(pdf_path), minio_path)
            uploaded_files.append(minio_path)
            logger.success(f"[UploadMinIO] ✅ Uploaded PDF: {minio_path}")

        # 2. 上传Markdown文件
        mineru_output = temp_dir / "mineru_output"
        if mineru_output.exists():
            # 查找markdown文件
            md_files = list(mineru_output.glob("*.md"))
            if md_files:
                md_path = md_files[0]
                minio_path = f"{folder}{filename}.md"
                minio_client.save_file(str(md_path), minio_path)
                uploaded_files.append(minio_path)
                logger.success(f"[UploadMinIO] ✅ Uploaded Markdown: {minio_path}")

            # 3. 上传图片文件夹
            images_dir = mineru_output / "images"
            if images_dir.exists() and images_dir.is_dir():
                image_files = list(images_dir.glob("*"))
                for img_file in image_files:
                    if img_file.is_file():
                        minio_path = f"{folder}images/{img_file.name}"
                        minio_client.save_file(str(img_file), minio_path)
                        uploaded_files.append(minio_path)

                logger.success(f"[UploadMinIO] ✅ Uploaded {len(image_files)} images")

        # 更新state
        state['minio_upload_success'] = True
        state['minio_bucket'] = bucket
        state['minio_folder'] = folder
        state['minio_uploaded_files'] = uploaded_files

        logger.success(f"[UploadMinIO] === MinIO upload completed: {len(uploaded_files)} files ===")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="upload_minio",
                step_name="上传MinIO",
                progress=35,
                message=f"已上传 {len(uploaded_files)} 个文件"
            )

        return state

    except Exception as e:
        logger.error(f"[UploadMinIO] MinIO upload failed: {e}")
        import traceback
        traceback.print_exc()

        state['minio_upload_success'] = False
        state['errors'] = state.get('errors', []) + [f"MinIO upload error: {str(e)}"]

        return state


async def minio_upload_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: MinIO上传失败，继续处理但记录错误
    """
    logger.warning("[UploadMinIO] Using fallback - continuing without MinIO upload")
    state['minio_upload_success'] = False
    return state
