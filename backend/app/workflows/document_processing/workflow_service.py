"""
Document Processing Workflow with SSE Progress Tracking

6-step workflow with real-time SSE events matching frontend WorkflowProgress component
"""
from typing import Dict, Any
from loguru import logger
import asyncio

from .graph_builder import build_document_processing_workflow


class DocumentProcessingWorkflow:
    """6-step document processing workflow with real-time SSE progress"""

    # Map workflow nodes to frontend step IDs (6 steps)
    STEP_MAPPING = {
        "save_to_minio": "minio",
        "minio_fallback": "minio",
        "parse_pdf_mineru": "parse",
        "parse_fallback": "parse",
        "chunk_text": "chunk",
        "extract_entities": "extract",
        "extract_fallback": "extract",
        "vectorize_traditional": "vectorize_traditional",
        "vector_fallback": "vectorize_traditional",
        "vectorize_graph": "vectorize_graph",
        "graph_vector_fallback": "vectorize_graph",
        "finalize": "finalize"
    }

    # Chinese names for each step (7 steps including finalize)
    STEP_NAMES = {
        "minio": "MinIO存储",
        "parse": "PDF解析",
        "chunk": "文本分块",
        "extract": "实体提取",
        "vectorize_traditional": "传统向量化",
        "vectorize_graph": "图向量化",
        "finalize": "完成"
    }

    # Progress percentage for each step (6 steps)
    STEP_PROGRESS = {
        "minio": 15,
        "parse": 30,
        "chunk": 45,
        "extract": 60,
        "vectorize_traditional": 75,
        "vectorize_graph": 90,
        "finalize": 100
    }

    def __init__(self):
        self.workflow = build_document_processing_workflow()

    async def process_document(
        self,
        task_id: str,
        filename: str,
        file_path: str,
        pages_count: int = 0
    ) -> Dict[str, Any]:
        """
        Process document with SSE progress updates

        6-step workflow:
        1. MinIO存储 (15%)
        2. PDF解析 (30%)
        3. 文本分块 (45%)
        4. 实体提取 (60%)
        5. RAG向量化 (75%)
        6. 知识图谱构建 (90%)
        7. 完成 (100%)

        Args:
            task_id: Task ID
            filename: Original filename
            file_path: File path
            pages_count: PDF页数

        Returns:
            Processing result
        """
        logger.info(f"[Workflow] Starting 6-step workflow: {filename}")

        try:
            # Send start event
            await self._send_sse_event(task_id, "start", {
                "message": f"开始处理文档: {filename}",
                "filename": filename
            })

            # Initialize state
            initial_state = {
                "task_id": task_id,
                "filename": filename,
                "file_path": file_path,
                "pages_count": pages_count,  # 传递页数到state
                "raw_text": "",
                "markdown_text": "",
                "parsed_text": "",
                "chunks": [],
                "destinations": [],
                "minio_success": False,
                "parse_success": False,
                "chunk_success": False,
                "extract_success": False,
                "vector_success": False,
                "graph_vector_success": False,
                "finalize_success": False,
                "errors": []
            }

            # Track completed steps
            completed_steps = set()

            # Execute workflow
            logger.info("[Workflow] Starting astream loop...")

            async for event in self.workflow.astream(initial_state):
                for node_name, node_state in event.items():
                    logger.info(f"[Workflow] Node completed: {node_name}")

                    # Get frontend step ID
                    step_id = self.STEP_MAPPING.get(node_name)

                    logger.info(f"[Workflow] node_name={node_name}, mapped step_id={step_id}, completed_steps={completed_steps}")

                    if step_id and step_id not in completed_steps:
                        step_name = self.STEP_NAMES.get(step_id, step_id)
                        progress = self.STEP_PROGRESS.get(step_id, 0)

                        logger.info(f"[Workflow] Sending node_end event for step: {step_id} ({step_name})")

                        # 只发送END事件（START事件在节点内部发送）
                        await self._send_step_event(
                            task_id=task_id,
                            step_id=step_id,
                            step_name=step_name,
                            status="completed",
                            message=self._get_step_message(step_id, "completed", node_state),
                            progress=progress,
                            event_type="node_end"
                        )

                        completed_steps.add(step_id)
                        logger.info(f"[Workflow] Step {step_id} added to completed_steps")
                    else:
                        if not step_id:
                            logger.warning(f"[Workflow] No step_id mapping for node: {node_name}")
                        else:
                            logger.info(f"[Workflow] Step {step_id} already in completed_steps, skipping")

                    logger.info(f"[Workflow] Node END: {node_name}")

                    # Update state
                    initial_state.update(node_state)

            # Get results
            destinations_count = len(initial_state.get("destinations", []))

            # Send complete event
            await self._send_sse_event(task_id, "complete", {
                "message": f"处理完成: 提取了 {destinations_count} 个景点",
                "destinations_count": destinations_count,
                "progress": 100
            })

            logger.success(f"[Workflow] 6-step workflow completed: {destinations_count} destinations")

            return {
                "success": True,
                "destinations_count": destinations_count,
                "destinations": initial_state.get("destinations", []),
                "chunks_count": len(initial_state.get("chunks", [])),
                "statistics": initial_state.get("statistics", {})
            }

        except Exception as e:
            logger.error(f"[Workflow] Failed: {e}")
            import traceback
            traceback.print_exc()

            # Send error event
            await self._send_sse_event(task_id, "error", {
                "message": f"处理失败: {str(e)}",
                "error": str(e)
            })

            return {
                "success": False,
                "error": str(e),
                "destinations_count": 0
            }

    async def _send_step_event(
        self,
        task_id: str,
        step_id: str,
        step_name: str,
        status: str,
        message: str,
        progress: int,
        event_type: str = "update"  # "start", "end", "update"
    ):
        """
        Send step status update via SSE

        执行顺序：
        1. 先发送SSE事件到Redis event key（实时推送）
        2. 再保存到事件列表和进度key（历史记录）
        """
        import time

        event_data = {
            "event_type": event_type,  # "node_start" 或 "node_end"
            "step": step_id,
            "step_name": step_name,
            "status": status,
            "message": message,
            "progress": progress,
            "timestamp": time.time()
        }

        # Save to Redis
        from app.core.redis_client import get_redis_client
        import json

        redis_client = get_redis_client()

        # 1. 【优先】发送SSE事件（立即推送给前端）
        await self._send_sse_event(task_id, event_type, event_data)

        # 2. 保存到事件列表（用于历史回放）
        events_key = f"document:events:{task_id}"
        redis_client.rpush(events_key, json.dumps(event_data, ensure_ascii=False))
        redis_client.expire(events_key, 3600)  # 1小时过期

        # 3. 保存最新进度（用于轮询）
        progress_key = f"document:progress:{task_id}"
        redis_client.set(
            progress_key,
            json.dumps(event_data, ensure_ascii=False),
            ex=3600
        )

        logger.info(f"[{event_type.upper()}] {step_name} ({step_id}): {status} - {message} ({progress}%)")

    async def _send_sse_event(self, task_id: str, event_type: str, data: Dict):
        """Send SSE event (start, complete, error) - 使用Redis Pub/Sub实时推送"""
        from app.core.redis_client import get_redis_client
        import json

        redis_client = get_redis_client()
        event_key = f"document:event:{task_id}"

        event_data = {
            "type": event_type,
            **data
        }

        # 1. 写入event key（用于轮询fallback）
        redis_client.set(
            event_key,
            json.dumps(event_data, ensure_ascii=False),
            ex=3600
        )

        # 2. 发布到Redis Pub/Sub频道（实时推送）
        channel = f"document:events:{task_id}"
        try:
            if redis_client.client:
                redis_client.client.publish(
                    channel,
                    json.dumps(event_data, ensure_ascii=False)
                )
                logger.debug(f"[Pub/Sub] Published {event_type} to {channel}")
        except Exception as e:
            logger.warning(f"[Pub/Sub] Failed to publish: {e}")

        logger.info(f"[SSE Event] {event_type}: {data.get('message', '')}")

    def _get_step_message(self, step_id: str, status: str, state: Dict = None) -> str:
        """Get human-readable message for step"""
        messages = {
            "minio": {
                "processing": "正在保存文件到MinIO存储...",
                "completed": "文件保存成功"
            },
            "parse": {
                "processing": "正在使用MinerU解析PDF文档...",
                "completed": f"PDF解析完成 ({len(state.get('parsed_text', '')) if state else 0} 字符)"
            },
            "chunk": {
                "processing": "正在使用LangChain分割文本块...",
                "completed": f"文本分块完成 ({len(state.get('chunks', [])) if state else 0} 块)"
            },
            "extract": {
                "processing": "正在使用Qwen提取景点实体...",
                "completed": f"实体提取完成 ({len(state.get('destinations', [])) if state else 0} 个景点)"
            },
            "vectorize_traditional": {
                "processing": "正在向量化到Milvus数据库...",
                "completed": f"RAG向量化完成 ({len(state.get('destinations', [])) if state else 0} 个景点)"
            },
            "vectorize_graph": {
                "processing": "正在构建Neo4j知识图谱...",
                "completed": f"知识图谱构建完成 ({len(state.get('destinations', [])) if state else 0} 个节点)"
            }
        }

        return messages.get(step_id, {}).get(status, f"{step_id}: {status}")


# Singleton
_workflow_instance = None


def get_document_workflow() -> DocumentProcessingWorkflow:
    """Get workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = DocumentProcessingWorkflow()
    return _workflow_instance
