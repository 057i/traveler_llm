"""
Document Processing Workflow with Progress Tracking

Enhanced version with SSE events matching frontend WorkflowProgress component
"""
from typing import Dict, Any
from loguru import logger
import asyncio

from .graph_builder import build_document_processing_workflow
from app.services.document_progress import get_document_progress_service


class DocumentProcessingWorkflow:
    """Document processing workflow with real-time SSE progress"""

    # Map workflow nodes to frontend step IDs
    STEP_MAPPING = {
        "save_to_minio": "minio",
        "minio_fallback": "minio",
        "parse_pdf_mineru": "parse",
        "parse_fallback": "parse",
        "chunk_text": "chunk",
        "extract_entities": "extract",
        "extract_fallback": "extract",
        "vectorize": "vectorize_traditional",
        "vector_fallback": "vectorize_traditional",
        "vectorize_graph": "vectorize_graph",
        "graph_vector_fallback": "vectorize_graph",
        "finalize": "vectorize_graph"
    }

    # Progress percentage for each step
    STEP_PROGRESS = {
        "minio": 15,
        "parse": 35,
        "chunk": 50,
        "extract": 65,
        "vectorize_traditional": 80,
        "vectorize_graph": 95
    }

    def __init__(self):
        self.workflow = build_document_processing_workflow()
        self.progress_service = get_document_progress_service()

    async def process_document(
        self,
        task_id: str,
        filename: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process document with SSE progress updates

        Args:
            task_id: Task ID
            filename: Original filename
            file_path: File path

        Returns:
            Processing result
        """
        logger.info(f"[Workflow] Starting: {filename}")

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
                "parsed_text": "",
                "chunks": [],
                "destinations": [],
                "minio_success": False,
                "parse_success": False,
                "extract_success": False,
                "vector_success": False,
                "graph_vector_success": False
            }

            # Track completed steps
            completed_steps = set()

            # Execute workflow
            async for event in self.workflow.astream(initial_state):
                for node_name, node_state in event.items():
                    logger.info(f"[Workflow] Node executed: {node_name}")

                    # Get frontend step ID
                    step_id = self.STEP_MAPPING.get(node_name)

                    if step_id and step_id not in completed_steps:
                        # Mark as processing
                        await self._send_step_event(
                            task_id=task_id,
                            step_id=step_id,
                            status="processing",
                            message=self._get_step_message(step_id, "processing"),
                            progress=self.STEP_PROGRESS.get(step_id, 0)
                        )

                        # Wait a moment for visual effect
                        await asyncio.sleep(0.1)

                        # Mark as completed
                        await self._send_step_event(
                            task_id=task_id,
                            step_id=step_id,
                            status="completed",
                            message=self._get_step_message(step_id, "completed", node_state),
                            progress=self.STEP_PROGRESS.get(step_id, 0)
                        )

                        completed_steps.add(step_id)

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

            logger.success(f"[Workflow] Completed: {destinations_count} destinations")

            return {
                "success": True,
                "destinations_count": destinations_count,
                "destinations": initial_state.get("destinations", []),
                "chunks_count": len(initial_state.get("chunks", []))
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
        status: str,
        message: str,
        progress: int
    ):
        """Send step status update via SSE"""
        event_data = {
            "step": step_id,
            "status": status,
            "message": message,
            "progress": progress
        }

        # Save to Redis for SSE streaming
        from app.core.redis_client import get_redis_client
        import json

        redis_client = get_redis_client()
        progress_key = f"document:progress:{task_id}"

        redis_client.set(
            progress_key,
            json.dumps(event_data, ensure_ascii=False),
            ex=3600
        )

        logger.info(f"[Progress] {step_id}: {status} - {message} ({progress}%)")

    async def _send_sse_event(self, task_id: str, event_type: str, data: Dict):
        """Send SSE event"""
        from app.core.redis_client import get_redis_client
        import json

        redis_client = get_redis_client()
        event_key = f"document:event:{task_id}"

        event_data = {
            "type": event_type,
            **data
        }

        redis_client.set(
            event_key,
            json.dumps(event_data, ensure_ascii=False),
            ex=3600
        )

    def _get_step_message(self, step_id: str, status: str, state: Dict = None) -> str:
        """Get human-readable message for step"""
        messages = {
            "minio": {
                "processing": "正在保存文件到存储...",
                "completed": "文件保存成功"
            },
            "parse": {
                "processing": "正在解析PDF文档...",
                "completed": f"PDF解析完成 ({len(state.get('parsed_text', '')) if state else 0} 字符)"
            },
            "chunk": {
                "processing": "正在分割文本块...",
                "completed": f"文本分块完成 ({len(state.get('chunks', [])) if state else 0} 块)"
            },
            "extract": {
                "processing": "正在提取景点实体...",
                "completed": f"实体提取完成 ({len(state.get('destinations', [])) if state else 0} 个景点)"
            },
            "vectorize_traditional": {
                "processing": "正在向量化到ChromaDB...",
                "completed": "向量化完成"
            },
            "vectorize_graph": {
                "processing": "正在构建知识图谱...",
                "completed": "知识图谱构建完成"
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
