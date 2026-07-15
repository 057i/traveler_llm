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

        # ==================== 自动设置MinIO访问策略 ====================
        try:
            logger.info(f"[UploadMinIO] 正在设置文件夹访问策略: {folder}")

            # 设置该文件夹为公共只读
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/{folder}*"]
                    }
                ]
            }

            import json
            from minio.commonconfig import ENABLED
            from minio.api import Minio

            # 获取MinIO客户端实例
            minio_instance = minio_client.client

            # 获取当前桶策略
            try:
                current_policy = minio_instance.get_bucket_policy(bucket)
                if current_policy:
                    current_policy_dict = json.loads(current_policy)
                else:
                    current_policy_dict = {"Version": "2012-10-17", "Statement": []}
            except Exception:
                # 如果没有策略，创建新的
                current_policy_dict = {"Version": "2012-10-17", "Statement": []}

            # 添加新的语句（如果不存在）
            folder_resource = f"arn:aws:s3:::{bucket}/{folder}*"
            already_exists = any(
                stmt.get("Resource") == [folder_resource]
                for stmt in current_policy_dict.get("Statement", [])
            )

            if not already_exists:
                current_policy_dict["Statement"].append(policy["Statement"][0])
                minio_instance.set_bucket_policy(bucket, json.dumps(current_policy_dict))
                logger.success(f"[UploadMinIO] ✅ 已设置文件夹 {folder} 为公共只读")
            else:
                logger.info(f"[UploadMinIO] 文件夹 {folder} 访问策略已存在")

        except Exception as policy_error:
            logger.warning(f"[UploadMinIO] 设置访问策略失败（不影响上传）: {policy_error}")
        # ================================================================

        # ==================== 保存MinIO查看URL到Redis ====================
        try:
            logger.info(f"[UploadMinIO] 正在保存文档查看URL到Redis...")

            from app.services.document_metadata_service import get_document_metadata_service

            # 获取文件名（不含扩展名）
            filename = state.get('filename', 'unknown')

            # 构建MinIO公共访问URL
            # 确保URL包含 http:// 前缀
            minio_endpoint = settings.MINIO_ENDPOINT
            if not minio_endpoint.startswith('http://') and not minio_endpoint.startswith('https://'):
                minio_public_url = f"http://{minio_endpoint}"
            else:
                minio_public_url = minio_endpoint

            logger.info(f"[UploadMinIO] 文档名: {filename}")
            logger.info(f"[UploadMinIO] MinIO公共URL: {minio_public_url}")
            logger.info(f"[UploadMinIO] 存储桶: {bucket}")
            logger.info(f"[UploadMinIO] 文件夹: {folder}")

            # 生成完整的view_url（minio_public_url已包含http://前缀）
            view_url = f"{minio_public_url}/{bucket}/{folder}{filename}_origin.pdf"

            logger.info(f"[UploadMinIO] 生成的查看URL: {view_url}")

            # 更新Redis元数据
            metadata_service = get_document_metadata_service()
            metadata_service._update_field(doc_id, 'view_url', view_url)
            metadata_service._update_field(doc_id, 'minio_public_url', view_url)

            logger.success(f"[UploadMinIO] ✅ 已保存查看URL到Redis: {view_url}")

        except Exception as url_error:
            logger.warning(f"[UploadMinIO] 保存查看URL失败（不影响上传）: {url_error}")
        # ================================================================

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
