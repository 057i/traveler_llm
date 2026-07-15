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
from asyncio import Semaphore
from concurrent.futures import ThreadPoolExecutor

from app.services.document_task import DocumentTaskService
from app.core.redis_client import get_redis_client
from app.services.document_processing_service import get_document_workflow
import asyncio

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

# 全局并发限制：最多2个文档同时处理
processing_semaphore = Semaphore(2)

# 全局线程池：用于CPU密集型操作（向量化）
vector_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="vector_worker")

# 列表查询缓存（2秒）
list_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 2  # 缓存2秒

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

        # 生成文档ID和任务ID
        doc_id = str(uuid.uuid4())
        task_id = doc_id

        # 标准化文件名（去除扩展名）
        filename = os.path.splitext(file.filename)[0]

        # 使用临时文件管理器保存上传的文件
        from app.utils.temp_file_manager import get_temp_file_manager
        temp_manager = get_temp_file_manager()

        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大100MB）"
            )

        # 保存到临时目录（快速操作）
        temp_file_path = temp_manager.save_uploaded_file(
            doc_id=doc_id,
            file_content=file_content,
            filename=file.filename
        )

        logger.info(f"文件上传完成: {file.filename}, 大小: {file_size} bytes, Doc ID: {doc_id}")

        # 快速获取PDF页数（可选，如果太慢可以移到后台）
        pages_count = 0
        try:
            import PyPDF2
            with open(temp_file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pages_count = len(pdf_reader.pages)
                logger.info(f"[Upload] PDF页数: {pages_count}")
        except Exception as e:
            logger.warning(f"[Upload] 无法获取PDF页数: {e}")
            pages_count = 0

        # 创建Redis元数据（快速操作）
        from app.services.document_metadata_service import get_document_metadata_service
        metadata_service = get_document_metadata_service()

        metadata_service.create_document_metadata(
            doc_id=doc_id,
            filename=filename,
            original_name=file.filename,
            file_size=file_size,
            minio_bucket="travel-documents",
            minio_folder=f"{filename}/"
        )

        # 保存页数
        if pages_count > 0:
            metadata_service._update_field(doc_id, 'pages_count', pages_count)

        logger.success(f"[Upload] Created metadata for {filename}, pages: {pages_count}")

        # 创建任务记录（快速操作）
        await document_task_service.create_task(
            task_id=task_id,
            filename=file.filename,
            file_path=str(temp_file_path),
            file_size=file_size,
            pages_count=pages_count
        )

        # 启动后台处理任务
        asyncio.create_task(
            process_document_background(task_id, doc_id, filename, str(temp_file_path))
        )

        logger.info(f"[Upload] Background task created for {filename}")

        # 立即返回响应
        return {
            "task_id": task_id,
            "document_id": doc_id,
            "filename": file.filename,
            "file_size": file_size,
            "status": "processing",
            "message": "文档上传成功，正在处理中"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(task_id: str, doc_id: str, filename: str, file_path: str):
    """
    后台处理文档（带并发限制）

    功能：
        - 使用Semaphore限制同时处理的文档数量，避免资源耗尽
        - 调用文档处理工作流执行PDF解析、分块、向量化等操作
        - 处理失败时更新元数据状态

    参数：
        task_id: 任务ID
        doc_id: 文档ID（用于元数据管理）
        filename: 文件名（不含扩展名）
        file_path: 临时文件路径
    """
    # 使用信号量限制并发（最多2个文档同时处理）
    async with processing_semaphore:
        try:
            logger.info(f"[Background] Starting document processing for task: {task_id}, doc: {doc_id}")
            logger.info(f"[Background] Semaphore acquired, concurrent tasks: {2 - processing_semaphore._value}")

            # 获取workflow服务
            workflow = get_document_workflow()

            # 执行处理（传递doc_id）
            result = await workflow.process_document(
                task_id=task_id,
                doc_id=doc_id,
                filename=filename,
                file_path=file_path,
                pages_count=0
            )

            logger.success(f"[Background] Document processing completed for task: {task_id}")

        except Exception as e:
            logger.error(f"[Background] Document processing failed for task {task_id}: {e}")
            import traceback
            traceback.print_exc()

            # 更新元数据状态为失败
            from app.services.document_metadata_service import get_document_metadata_service
            metadata_service = get_document_metadata_service()
            metadata_service.update_status(doc_id, "failed")

            # 更新旧任务状态
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
                                # 优先使用event_type，兼容旧的type字段
                                event_type = data.get('event_type') or data.get('type')

                                # 如果event_type为None，跳过该消息
                                if not event_type:
                                    logger.warning(f"[SSE] Skipping message without event_type: {data}")
                                    continue

                                # 转换为标准格式（确保有event_type字段）
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
    获取文档列表（从Redis元数据读取，带2秒缓存）

    支持分页查询，使用缓存减少Redis查询压力
    """
    try:
        import time

        # 检查缓存（带分页key）
        cache_key = f"{page}_{page_size}"
        current_time = time.time()

        if (list_cache.get("key") == cache_key and
            current_time - list_cache.get("timestamp", 0) < CACHE_TTL):
            logger.debug(f"[List] Cache hit for page {page}")
            return list_cache["data"]

        # 缓存未命中，查询Redis
        logger.debug(f"[List] Cache miss, querying Redis...")
        from app.services.document_metadata_service import get_document_metadata_service

        metadata_service = get_document_metadata_service()
        all_documents = metadata_service.list_all_documents()

        # 分页
        skip = (page - 1) * page_size
        documents = all_documents[skip:skip + page_size]
        total = len(all_documents)

        # 格式化返回数据
        formatted_docs = []
        for doc in documents:
            formatted_docs.append({
                "task_id": doc.get("doc_id"),  # 兼容前端
                "document_id": doc.get("doc_id"),
                "filename": doc.get("filename"),
                "original_name": doc.get("original_name"),
                "upload_time": doc.get("upload_time"),
                "status": doc.get("status"),
                "file_size": doc.get("file_size"),

                # 统计信息
                "destinations_count": doc.get("entities_count", 0),
                "chunks_count": doc.get("chunks_count", 0),
                "pages_count": doc.get("pages_count", 0),
                "province": doc.get("province", "-"),
                "city": doc.get("city", "-"),

                # MinIO查看URL
                "view_url": doc.get("view_url", ""),
                "minio_public_url": doc.get("minio_public_url", ""),
            })

        result = {
            "documents": formatted_docs,
            "total": total,
            "page": page,
            "page_size": page_size
        }

        # 更新缓存
        list_cache["key"] = cache_key
        list_cache["data"] = result
        list_cache["timestamp"] = current_time
        logger.debug(f"[List] Cache updated for page {page}")

        return result

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    删除文档（级联删除所有资源）

    删除内容：
    1. MinIO中的所有文件（PDF + Markdown + 图片）
    2. Milvus中的所有向量
    3. Neo4j中的所有实体
    4. Redis中的元数据
    """
    try:
        logger.info(f"[Delete] 开始删除文档: {doc_id}")

        # 使用新的级联删除服务
        from app.services.document_deletion_service import get_document_deletion_service
        deletion_service = get_document_deletion_service()

        result = await deletion_service.delete_document(doc_id)

        if not result["success"]:
            logger.warning(f"[Delete] 删除部分失败: {result}")
            return {
                "success": False,
                "message": "文档删除失败",
                "details": result["deleted"],
                "errors": result.get("errors", [])
            }

        logger.success(f"[Delete] 文档删除完成: {doc_id}")
        logger.info(f"[Delete] 删除详情: {result['deleted']}")

        return {
            "success": True,
            "message": "文档及所有资源已成功删除",
            "doc_id": doc_id,
            "deleted": result["deleted"]
        }

    except Exception as e:
        logger.error(f"[Delete] 删除失败: {e}")
        import traceback
        traceback.print_exc()
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
    获取统计信息（从新的元数据系统读取）

    返回文档总数、省份数、城市数、景点数等
    """
    try:
        from app.services.document_metadata_service import get_document_metadata_service

        metadata_service = get_document_metadata_service()
        all_documents = metadata_service.list_all_documents()

        # 文档统计
        total_docs = len(all_documents)
        processing = len([d for d in all_documents if d.get('status') == 'processing'])
        completed = len([d for d in all_documents if d.get('status') == 'completed'])

        # 从元数据聚合统计
        provinces_set = set()
        cities_set = set()
        total_entities = 0

        for doc in all_documents:
            if doc.get('status') == 'completed':
                # 统计景点数
                total_entities += doc.get('entities_count', 0)

                # 收集省份和城市
                province = doc.get('province')
                city = doc.get('city')

                logger.debug(f"[Statistics] Doc {doc.get('filename')}: province={province}, city={city}")

                if province and province != '-':
                    provinces_set.add(province)

                if city and city != '-':
                    cities_set.add(city)

        total_provinces = len(provinces_set)
        total_cities = len(cities_set)

        logger.info(f"[Statistics] Docs: {total_docs}, Entities: {total_entities}, Provinces: {total_provinces}, Cities: {total_cities}")
        logger.info(f"[Statistics] Provinces list: {list(provinces_set)}")
        logger.info(f"[Statistics] Cities list: {list(cities_set)}")

        # 从Neo4j获取图谱统计（用于验证）
        graph_destinations = 0
        try:
            from app.core.neo4j_client import get_neo4j_client
            neo4j = get_neo4j_client()

            # 统计景点数
            result = neo4j.query("MATCH (n:Destination) RETURN count(n) as count")
            if result and len(result) > 0:
                graph_destinations = result[0].get('count', 0)

        except Exception as e:
            logger.error(f"[Statistics] 获取Neo4j统计失败: {e}")
            graph_destinations = 0

        return {
            "totalDocs": total_docs,
            "processing": processing,
            "completed": completed,
            "totalProvinces": total_provinces,
            "totalCities": total_cities,
            "totalDestinations": total_entities,  # 从元数据统计
            "textRAG": total_entities,
            "graphRAG": graph_destinations  # Neo4j中的景点数
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
