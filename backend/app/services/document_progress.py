"""
Document Processing Progress Service

Real-time progress tracking for document processing workflow
Sends detailed node execution logs to frontend via SSE
"""
from typing import Dict, Any
from loguru import logger
from datetime import datetime
import json

from app.core.redis_client import get_redis_client


class DocumentProgressService:
    """Document processing progress service"""

    def __init__(self):
        self.redis_client = get_redis_client()

    async def send_progress(
        self,
        task_id: str,
        step: int,
        progress: int,
        message: str,
        detail: str = "",
        status: str = "processing"
    ):
        """
        Send progress update to Redis for SSE streaming

        Args:
            task_id: Task ID
            step: Current step index (0-5)
            progress: Progress percentage (0-100)
            message: Progress message
            detail: Detailed message
            status: Status (processing, completed, failed)
        """
        try:
            progress_data = {
                "type": "progress",
                "task_id": task_id,
                "step": step,
                "progress": progress,
                "message": message,
                "detail": detail,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }

            # Save to Redis
            progress_key = f"document:progress:{task_id}"
            self.redis_client.set(
                progress_key,
                json.dumps(progress_data, ensure_ascii=False),
                ex=3600  # 1 hour expiry
            )

            logger.info(f"[Progress] Task {task_id}: {message} ({progress}%)")

        except Exception as e:
            logger.error(f"Failed to send progress: {e}")

    async def send_start(self, task_id: str, filename: str):
        """Send start message"""
        await self.send_progress(
            task_id=task_id,
            step=0,
            progress=0,
            message="Document processing started",
            detail=f"Processing: {filename}",
            status="processing"
        )

    async def send_complete(
        self,
        task_id: str,
        destinations_count: int,
        message: str = "Processing completed"
    ):
        """Send completion message"""
        complete_data = {
            "type": "complete",
            "task_id": task_id,
            "progress": 100,
            "message": message,
            "destinations_count": destinations_count,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }

        progress_key = f"document:progress:{task_id}"
        self.redis_client.set(
            progress_key,
            json.dumps(complete_data, ensure_ascii=False),
            ex=3600
        )

        logger.success(f"[Progress] Task {task_id} completed: {destinations_count} destinations")

    async def send_error(self, task_id: str, error: str):
        """Send error message"""
        error_data = {
            "type": "error",
            "task_id": task_id,
            "progress": 0,
            "message": "Processing failed",
            "detail": error,
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }

        progress_key = f"document:progress:{task_id}"
        self.redis_client.set(
            progress_key,
            json.dumps(error_data, ensure_ascii=False),
            ex=3600
        )

        logger.error(f"[Progress] Task {task_id} failed: {error}")

    async def send_node_log(
        self,
        task_id: str,
        node_name: str,
        log_message: str
    ):
        """
        Send node execution log

        Args:
            task_id: Task ID
            node_name: Node name (e.g., "MinIO", "PDF Parse", "Chunk")
            log_message: Log message
        """
        try:
            # Add to logs list in Redis
            logs_key = f"document:logs:{task_id}"
            log_entry = {
                "node": node_name,
                "message": log_message,
                "timestamp": datetime.now().isoformat()
            }

            self.redis_client.rpush(
                logs_key,
                json.dumps(log_entry, ensure_ascii=False)
            )
            self.redis_client.expire(logs_key, 3600)

            logger.debug(f"[NodeLog] {node_name}: {log_message}")

        except Exception as e:
            logger.error(f"Failed to send node log: {e}")


# Singleton instance
_progress_service = None


def get_document_progress_service() -> DocumentProgressService:
    """Get document progress service singleton"""
    global _progress_service
    if _progress_service is None:
        _progress_service = DocumentProgressService()
    return _progress_service
