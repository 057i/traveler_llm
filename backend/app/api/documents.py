"""
文档管理 API

提供文档上传、列表、删除、下载和处理进度查询功能
支持PDF文档的流式上传和异步处理
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
from loguru import logger
import os
import uuid
from datetime import datetime

from app.services.document_task import DocumentTaskService
from app.core.redis_client import get_redis_client
from app.workflows.document_processing.workflow_service import get_document_workflow
import asyncio

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

# 初始化服务
document_task_service = DocumentTaskService()

# 允许的文件类型
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/x-pdf',
}

ALLOWED_EXTENSIONS = {'.pdf'}

# 文件大小限制（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档

    支持流式上传，避免内存溢出
    返回任务ID用于查询处理进度
    """
    try:
        # 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file.content_type not in ALLOWED_MIME_TYPES and file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。仅支持PDF文件"
            )

        # MIME类型宽松检查
        if file.content_type not in ALLOWED_MIME_TYPES:
            if file_ext in ALLOWED_EXTENSIONS:
                logger.warning(f"MIME类型 {file.content_type} 不在白名单，但扩展名正确，允许通过")
            else:
                raise HTTPException(status_code=400, detail="文件类型不匹配")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建临时文件路径
        upload_dir = "./data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        temp_file_path = os.path.join(upload_dir, f"{task_id}.pdf")

        # 流式保存文件
        file_size = 0
        with open(temp_file_path, "wb") as f:
            while chunk := await file.read(8192):  # 8KB chunks
                file_size += len(chunk)

                # 检查文件大小
                if file_size > MAX_FILE_SIZE:
                    os.remove(temp_file_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件大小超过限制（最大100MB）"
                    )

                f.write(chunk)

        logger.info(f"文件上传完成: {file.filename}, 大小: {file_size} bytes, 任务ID: {task_id}")

        # 创建处理任务
        await document_task_service.create_task(
            task_id=task_id,
            filename=file.filename,
            file_path=temp_file_path,
            file_size=file_size
        )

        # 启动后台处理任务
        asyncio.create_task(
            process_document_background(task_id, file.filename, temp_file_path)
        )

        return {
            "task_id": task_id,
            "filename": file.filename,
            "file_size": file_size,
            "status": "processing",
            "message": "文档上传成功，正在处理中"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(task_id: str, filename: str, file_path: str):
    """
    后台处理文档

    异步执行文档处理workflow，更新进度到Redis
    """
    try:
        logger.info(f"[Background] Starting document processing for task: {task_id}")

        # 获取workflow服务
        workflow = get_document_workflow()

        # 执行处理
        result = await workflow.process_document(
            task_id=task_id,
            filename=filename,
            file_path=file_path
        )

        logger.success(f"[Background] Document processing completed for task: {task_id}")

        # 更新任务状态
        await document_task_service.update_progress(
            task_id=task_id,
            progress=100,
            status="completed" if result.get("success") else "failed",
            message=f"Processing completed: {result.get('destinations_count', 0)} destinations"
        )

    except Exception as e:
        logger.error(f"[Background] Document processing failed for task {task_id}: {e}")
        import traceback
        traceback.print_exc()

        # 更新失败状态
        await document_task_service.update_progress(
            task_id=task_id,
            progress=0,
            status="failed",
            message=f"Processing failed: {str(e)}"
        )


@router.get("/progress/{task_id}")
async def get_processing_progress(task_id: str):
    """
    获取文档处理进度（SSE流式）

    使用Server-Sent Events实时推送处理进度
    """
    try:
        redis_client = get_redis_client()

        async def event_generator():
            """SSE事件生成器"""
            import asyncio
            import json

            last_event = None
            last_progress = -1
            timeout_count = 0
            max_timeout = 300  # 5分钟超时

            logger.info(f"[SSE] Client connected for task: {task_id}")

            while timeout_count < max_timeout:
                try:
                    # 获取进度数据
                    progress_key = f"document:progress:{task_id}"
                    progress_data = redis_client.get(progress_key)

                    if progress_data:
                        data = json.loads(progress_data)

                        # 检查是否是新的进度更新
                        current_progress = data.get('progress', 0)

                        if current_progress != last_progress or data != last_event:
                            last_progress = current_progress
                            last_event = data

                            # 根据状态发送不同事件
                            step = data.get('step')
                            status = data.get('status')

                            if status == 'processing':
                                # 发送 progress 事件
                                yield f"event: progress\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

                            elif status == 'completed':
                                # 发送 step_complete 事件
                                yield f"event: step_complete\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

                            logger.info(f"[SSE] Sent {status} event for step: {step}")

                    # 检查是否有完成或错误事件
                    event_key = f"document:event:{task_id}"
                    event_data = redis_client.get(event_key)

                    if event_data:
                        event = json.loads(event_data)
                        event_type = event.get('type')

                        if event_type == 'start':
                            yield f"event: start\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                            logger.info(f"[SSE] Sent start event")

                        elif event_type == 'complete':
                            yield f"event: complete\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                            logger.success(f"[SSE] Processing completed for task: {task_id}")
                            break

                        elif event_type == 'error':
                            yield f"event: error\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                            logger.error(f"[SSE] Processing failed for task: {task_id}")
                            break

                        # 清除已处理的事件
                        redis_client.delete(event_key)

                    await asyncio.sleep(0.5)
                    timeout_count += 1

                except Exception as e:
                    logger.error(f"[SSE] Error in event loop: {e}")
                    yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
                    break

            # 超时
            if timeout_count >= max_timeout:
                logger.warning(f"[SSE] Timeout for task: {task_id}")
                yield f"event: error\ndata: {json.dumps({'message': '处理超时'}, ensure_ascii=False)}\n\n"

            logger.info(f"[SSE] Connection closed for task: {task_id}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        logger.error(f"获取处理进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    获取文档列表

    支持分页查询
    """
    try:
        documents = await document_task_service.list_documents(skip=skip, limit=limit)
        total = await document_task_service.count_documents()

        return {
            "documents": documents,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    删除文档

    删除文档记录和相关文件
    """
    try:
        success = await document_task_service.delete_document(doc_id)

        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")

        return {"message": "文档删除成功", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/download")
async def download_document(doc_id: str):
    """
    下载文档

    返回原始PDF文件
    """
    try:
        doc_info = await document_task_service.get_document(doc_id)

        if not doc_info:
            raise HTTPException(status_code=404, detail="文档不存在")

        file_path = doc_info.get('file_path')
        filename = doc_info.get('filename', 'document.pdf')

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            file_path,
            filename=filename,
            media_type='application/pdf'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    获取统计信息

    返回文档总数、处理中的数量等
    """
    try:
        total = await document_task_service.count_documents()
        processing = await document_task_service.count_processing()

        return {
            "total": total,
            "processing": processing,
            "completed": total - processing
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
