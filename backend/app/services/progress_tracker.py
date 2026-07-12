"""
进度追踪服务

管理异步任务的进度追踪
使用Redis存储进度信息
"""
from typing import Dict, Optional
from loguru import logger
from datetime import datetime
import json

from app.core.redis_client import get_redis_client


class ProgressTracker:
    """进度追踪器"""

    def __init__(self):
        self.redis_client = get_redis_client()

    def start_progress(self, session_id: str, task_name: str) -> bool:
        """
        开始追踪进度

        Args:
            session_id: 会话ID
            task_name: 任务名称

        Returns:
            是否成功
        """
        try:
            progress_data = {
                "session_id": session_id,
                "task_name": task_name,
                "progress": 0,
                "status": "processing",
                "started_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            key = f"progress:{session_id}"
            self.redis_client.set(key, json.dumps(progress_data), ex=3600)  # 1小时过期

            logger.info(f"开始追踪进度: {session_id} - {task_name}")
            return True

        except Exception as e:
            logger.error(f"开始追踪进度失败: {e}")
            return False

    def update_progress(
        self,
        session_id: str,
        progress: int,
        message: str = "",
        status: str = "processing"
    ) -> bool:
        """
        更新进度

        Args:
            session_id: 会话ID
            progress: 进度值（0-100）
            message: 进度消息
            status: 状态

        Returns:
            是否成功
        """
        try:
            key = f"progress:{session_id}"
            data_str = self.redis_client.get(key)

            if data_str:
                progress_data = json.loads(data_str)
            else:
                progress_data = {
                    "session_id": session_id,
                    "task_name": "unknown"
                }

            progress_data.update({
                "progress": progress,
                "message": message,
                "status": status,
                "updated_at": datetime.now().isoformat()
            })

            self.redis_client.set(key, json.dumps(progress_data), ex=3600)
            return True

        except Exception as e:
            logger.error(f"更新进度失败: {e}")
            return False

    def complete_progress(self, session_id: str, message: str = "完成") -> bool:
        """
        完成进度追踪

        Args:
            session_id: 会话ID
            message: 完成消息

        Returns:
            是否成功
        """
        return self.update_progress(session_id, 100, message, "completed")

    def fail_progress(self, session_id: str, error_message: str) -> bool:
        """
        标记进度失败

        Args:
            session_id: 会话ID
            error_message: 错误消息

        Returns:
            是否成功
        """
        return self.update_progress(session_id, 0, error_message, "failed")

    def get_progress(self, session_id: str) -> Optional[Dict]:
        """
        获取进度信息

        Args:
            session_id: 会话ID

        Returns:
            进度信息或None
        """
        try:
            key = f"progress:{session_id}"
            data_str = self.redis_client.get(key)

            if data_str:
                return json.loads(data_str)

            return None

        except Exception as e:
            logger.error(f"获取进度失败: {e}")
            return None

    def delete_progress(self, session_id: str) -> bool:
        """
        删除进度信息

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        try:
            key = f"progress:{session_id}"
            self.redis_client.delete(key)
            logger.info(f"删除进度信息: {session_id}")
            return True

        except Exception as e:
            logger.error(f"删除进度失败: {e}")
            return False


# 全局进度追踪器实例
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """获取进度追踪器单例"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker