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

        # 获取PDF页数
        pages_count = 0
        try:
            import PyPDF2
            with open(temp_file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pages_count = len(pdf_reader.pages)
                logger.info(f"[Upload] PDF页数: {pages_count}")
        except Exception as e:
            logger.warning(f"[Upload] 无法获取页数: {e}")

        # 创建处理任务
        await document_task_service.create_task(
            task_id=task_id,
            filename=file.filename,
            file_path=temp_file_path,
            file_size=file_size,
            pages_count=pages_count  # 传递页数
        )

        # 启动后台处理任务
        asyncio.create_task(
            process_document_background(task_id, file.filename, temp_file_path)
        )

        # 返回响应（包含document_id以便前端关联）
        return {
            "task_id": task_id,
            "document_id": task_id,  # 使用task_id作为document_id
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

        # 获取任务信息（包含pages_count）
        task_info = await document_task_service.get_document(task_id)
        pages_count = task_info.get('pages_count', 0) if task_info else 0

        # 获取workflow服务
        workflow = get_document_workflow()

        # 执行处理
        result = await workflow.process_document(
            task_id=task_id,
            filename=filename,
            file_path=file_path,
            pages_count=pages_count  # 传递页数
        )

        logger.success(f"[Background] Document processing completed for task: {task_id}")

        # 注意：不再调用update_progress，因为：
        # 1. workflow_service已经通过_send_sse_event发送了complete事件
        # 2. 所有节点的进度已通过_send_step_event更新到progress key
        # 3. 额外的update_progress会覆盖progress key，导致event_type丢失

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
            """SSE事件生成器 - 使用Redis Pub/Sub实时推送"""
            import asyncio
            import json

            sent_event_ids = set()  # 追踪已发送的事件，避免重复

            logger.info(f"[SSE] Client connected for task: {task_id}")

            # 1. 立即发送所有历史事件
            events_key = f"document:events:{task_id}"
            historical_events = redis_client.lrange(events_key, 0, -1)

            if historical_events:
                logger.info(f"[SSE] Sending {len(historical_events)} historical events")
                for i, event_json in enumerate(historical_events, 1):
                    try:
                        event = json.loads(event_json)
                        event_type = event.get('event_type', 'progress')
                        step = event.get('step', 'N/A')

                        # 创建事件唯一ID
                        event_id = f"{event_type}:{step}"

                        # 跳过已发送的事件
                        if event_id in sent_event_ids:
                            continue

                        sent_event_ids.add(event_id)

                        logger.debug(f"[SSE] Sending historical event {i}/{len(historical_events)}: {event_type} - {step}")

                        # 根据event_type发送对应的SSE事件
                        if event_type == 'node_start':
                            yield f"event: node_start\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        elif event_type == 'node_end':
                            yield f"event: node_end\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                        else:
                            yield f"event: progress\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

                        await asyncio.sleep(0.001)
                    except Exception as e:
                        logger.warning(f"[SSE] Failed to send historical event {i}: {e}")

                logger.info(f"[SSE] Finished sending {len(historical_events)} historical events")
            else:
                logger.info(f"[SSE] No historical events found")

            # 2. 订阅Redis Pub/Sub频道，接收实时事件
            channel = f"document:events:{task_id}"

            # 创建独立的Redis连接用于订阅（不能与查询共用）
            import redis as redis_lib
            from config.settings import settings

            try:
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

                # 监听Pub/Sub消息
                timeout_count = 0
                max_timeout = 3000  # 5分钟 (以0.1秒为单位)

                while timeout_count < max_timeout:
                    try:
                        # 非阻塞方式获取消息
                        message = pubsub.get_message(timeout=0.1)

                        if message and message['type'] == 'message':
                            # 收到Pub/Sub消息
                            try:
                                data = json.loads(message['data'])
                                event_type = data.get('type')  # 注意：Pub/Sub消息使用'type'字段

                                # 转换为标准格式（添加event_type字段）
                                if 'event_type' not in data:
                                    data['event_type'] = event_type

                                step = data.get('step')
                                event_id = f"{event_type}:{step}" if step else f"{event_type}:_"

                                # 跳过已发送的事件
                                if event_id in sent_event_ids:
                                    logger.debug(f"[SSE] Skipping duplicate event: {event_id}")
                                    continue

                                sent_event_ids.add(event_id)

                                # 根据事件类型发送
                                if event_type == 'node_start':
                                    yield f"event: node_start\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    logger.info(f"[SSE] Sent node_start event for step: {step}")
                                elif event_type == 'node_end':
                                    yield f"event: node_end\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    logger.info(f"[SSE] Sent node_end event for step: {step}")
                                elif event_type == 'complete':
                                    yield f"event: complete\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    logger.success(f"[SSE] Processing completed for task: {task_id}")
                                    break
                                elif event_type == 'error':
                                    yield f"event: error\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    logger.error(f"[SSE] Processing failed for task: {task_id}")
                                    break
                                else:
                                    # 其他事件类型
                                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    logger.info(f"[SSE] Sent {event_type} event")

                                timeout_count = 0  # 收到消息后重置超时计数

                            except json.JSONDecodeError as e:
                                logger.warning(f"[SSE] Failed to parse message: {e}")

                        else:
                            # 没有消息，增加超时计数
                            timeout_count += 1
                            await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.error(f"[SSE] Error in Pub/Sub loop: {e}")
                        import traceback
                        traceback.print_exc()
                        break

                # 超时或完成
                if timeout_count >= max_timeout:
                    logger.warning(f"[SSE] Timeout for task: {task_id}")
                    yield f"event: error\ndata: {json.dumps({'message': '处理超时'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"[SSE] Pub/Sub error: {e}")
                import traceback
                traceback.print_exc()
                yield f"event: error\ndata: {json.dumps({'message': f'连接错误: {str(e)}'}, ensure_ascii=False)}\n\n"

            finally:
                # 清理订阅
                try:
                    pubsub.unsubscribe()
                    pubsub.close()
                    pubsub_client.close()
                    logger.info(f"[SSE] Unsubscribed and closed connection for task: {task_id}")
                except:
                    pass

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


@router.get("/debug/{task_id}")
async def debug_task(task_id: str):
    """
    调试接口：查看Redis中的任务详细信息
    """
    try:
        from app.core.redis_client import get_redis_client
        import json

        redis_client = get_redis_client()
        task_key = f"document:task:{task_id}"
        task_data = redis_client.get(task_key)

        if task_data:
            task_info = json.loads(task_data)
            return {
                "success": True,
                "task_info": task_info
            }
        else:
            return {
                "success": False,
                "message": "Task not found in Redis"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/list")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    获取文档列表

    支持分页查询
    """
    try:
        # 将page和page_size转换为skip和limit
        skip = (page - 1) * page_size
        limit = page_size

        documents = await document_task_service.list_documents(skip=skip, limit=limit)
        total = await document_task_service.count_documents()

        # Redis中的数据已经包含province, city, destinations_count, pages_count
        # 如果缺少，设置默认值
        for doc in documents:
            if 'province' not in doc:
                doc['province'] = '-'
            if 'city' not in doc:
                doc['city'] = '-'
            if 'destinations_count' not in doc:
                doc['destinations_count'] = 0
            if 'pages_count' not in doc:
                doc['pages_count'] = 0

        return {
            "documents": documents,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    删除文档

    清理范围：MinIO、本地文件、Redis、Neo4j、Milvus
    """
    try:
        logger.info(f"[Delete] 开始删除文档: {doc_id}")

        # 1. 获取文档信息
        doc_info = await document_task_service.get_document(doc_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="文档不存在")

        filename = doc_info.get('filename', '')
        minio_directory = doc_info.get('minio_directory', '')

        # 2. 删除MinIO文件夹
        if minio_directory:
            try:
                from app.core.minio_client import get_minio_client
                minio = get_minio_client()

                files = minio.list_files(prefix=f"{minio_directory}/")
                logger.info(f"[Delete] 删除MinIO: {minio_directory}/ ({len(files)}个文件)")

                for file_name in files:
                    minio.delete_file(file_name)

                logger.success(f"[Delete] MinIO已清理")
            except Exception as e:
                logger.warning(f"[Delete] MinIO清理失败: {e}")

        # 3. 删除本地文件
        file_path = doc_info.get('file_path', '')
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[Delete] 本地文件已删除")

        # 4. 删除Neo4j节点
        if filename:
            try:
                from app.core.neo4j_client import get_neo4j_client
                neo4j = get_neo4j_client()
                result = neo4j.query(
                    "MATCH (n:Destination {filename: $filename}) DETACH DELETE n RETURN count(n) as deleted_count",
                    {"filename": filename}
                )
                deleted_count = result[0]['deleted_count'] if result else 0
                logger.info(f"[Delete] Neo4j已删除: {deleted_count}个节点")
            except Exception as e:
                logger.warning(f"[Delete] Neo4j清理失败: {e}")

        # 5. 删除Milvus向量
        if filename:
            try:
                from app.core.milvus_hybrid_client import get_milvus_hybrid_client
                milvus = get_milvus_hybrid_client()
                milvus.collection.delete(f'filename == "{filename}"')
                logger.info(f"[Delete] Milvus向量已删除")
            except Exception as e:
                logger.warning(f"[Delete] Milvus清理失败: {e}")

        # 6. 删除Redis记录
        success = await document_task_service.delete_document(doc_id)
        if success:
            logger.success(f"[Delete] 文档删除完成: {doc_id}")

        return {"message": "文档删除成功", "doc_id": doc_id, "filename": filename}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Delete] 删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

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

    返回文档总数、省份数、城市数、景点数等
    """
    try:
        # 文档统计
        total_docs = await document_task_service.count_documents()
        processing = await document_task_service.count_processing()

        # 从Milvus获取景点统计
        total_destinations = 0
        total_provinces = 0
        total_cities = 0

        try:
            from app.core.milvus_hybrid_client import get_milvus_hybrid_client
            milvus = get_milvus_hybrid_client()

            # 获取Milvus中的向量总数
            milvus.collection.flush()  # 确保数据已刷新
            total_destinations = milvus.collection.num_entities

            logger.info(f"[Statistics] Milvus count: {total_destinations}")

        except Exception as e:
            logger.error(f"[Statistics] 获取Milvus统计失败: {e}")
            import traceback
            traceback.print_exc()
            total_destinations = 0
            total_provinces = 0
            total_cities = 0

        # 从Neo4j获取图谱统计
        graph_destinations = 0
        try:
            from app.core.neo4j_client import get_neo4j_client
            neo4j = get_neo4j_client()

            # 统计省份数（从Destination节点中去重）
            result = neo4j.query("""
                MATCH (n:Destination)
                WHERE n.province IS NOT NULL AND n.province <> ''
                RETURN count(DISTINCT n.province) as count
            """)
            if result and len(result) > 0:
                total_provinces = result[0].get('count', 0)

            # 统计城市数（从Destination节点中去重）
            result = neo4j.query("""
                MATCH (n:Destination)
                WHERE n.city IS NOT NULL AND n.city <> ''
                RETURN count(DISTINCT n.city) as count
            """)
            if result and len(result) > 0:
                total_cities = result[0].get('count', 0)

            # 统计景点数
            result = neo4j.query("MATCH (n:Destination) RETURN count(n) as count")
            if result and len(result) > 0:
                graph_destinations = result[0].get('count', 0)

        except Exception as e:
            logger.error(f"[Statistics] 获取Neo4j统计失败: {e}")
            import traceback
            traceback.print_exc()
            graph_destinations = 0

        return {
            "totalDocs": total_docs,
            "processing": processing,
            "completed": total_docs - processing,
            "totalProvinces": total_provinces,
            "totalCities": total_cities,
            "totalDestinations": total_destinations,
            "textRAG": total_destinations,
            "graphRAG": graph_destinations
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
