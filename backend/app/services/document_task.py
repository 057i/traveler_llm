"""
文档任务服务

管理文档处理任务的创建、查询、删除等操作
使用Redis存储任务状态和进度
"""
from typing import Optional, List, Dict
from loguru import logger
from datetime import datetime
import json
import os

from app.core.redis_client import get_redis_client


class DocumentTaskService:
    """
    文档任务服务 - 文档处理任务管理

    功能：
    - 创建文档处理任务
    - 更新任务进度和状态
    - 查询任务信息（单个/列表）
    - 统计任务数量
    - 删除任务

    存储结构（Redis）：
    - document:task:{task_id}: 任务详细信息
    - document:tasks: 任务ID列表（LPUSH）
    - document:progress:{task_id}: 最新进度信息

    任务信息：
    - task_id: 任务唯一ID
    - filename: 文件名
    - file_path: 文件路径
    - file_size: 文件大小
    - pages_count: PDF页数
    - status: 状态（pending/processing/completed/failed）
    - progress: 进度值（0-100）
    - destinations_count: 提取的景点数量
    - created_at: 创建时间
    - updated_at: 更新时间

    优化：
    - 使用Pipeline批量查询（避免N+1问题）
    - 24小时自动过期
    """

    def __init__(self):
        self.redis_client = get_redis_client()

    async def create_task(
        self,
        task_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        pages_count: int = 0
    ) -> Dict:
        """
        创建文档处理任务

        Args:
            task_id: 任务ID
            filename: 文件名
            file_path: 文件路径
            file_size: 文件大小
            pages_count: PDF页数

        Returns:
            任务信息字典
        """
        task_info = {
            "task_id": task_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "status": "pending",
            "progress": 0,
            "message": "等待处理",
            "destinations_count": 0,
            "pages_count": pages_count,  # 使用传入的页数
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "upload_time": datetime.now().isoformat()  # 添加upload_time
        }

        # 存储到Redis
        task_key = f"document:task:{task_id}"
        self.redis_client.set(task_key, json.dumps(task_info), ex=86400)  # 24小时过期

        # 添加到任务列表
        self.redis_client.lpush("document:tasks", task_id)

        logger.info(f"创建文档任务: {task_id}")
        return task_info

    async def update_progress(
        self,
        task_id: str,
        progress: int,
        status: str = "processing",
        message: str = ""
    ) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度（0-100）
            status: 状态
            message: 消息

        Returns:
            是否成功
        """
        try:
            progress_info = {
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            # 存储进度信息
            progress_key = f"document:progress:{task_id}"
            self.redis_client.set(progress_key, json.dumps(progress_info), ex=3600)  # 1小时过期

            # 更新任务状态
            task_key = f"document:task:{task_id}"
            task_data = self.redis_client.get(task_key)

            if task_data:
                task_info = json.loads(task_data)
                task_info.update({
                    "status": status,
                    "progress": progress,
                    "updated_at": datetime.now().isoformat()
                })
                self.redis_client.set(task_key, json.dumps(task_info), ex=86400)

            return True

        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return False

    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        获取文档信息

        Args:
            doc_id: 文档ID

        Returns:
            文档信息或None
        """
        try:
            task_key = f"document:task:{doc_id}"
            task_data = self.redis_client.get(task_key)

            if task_data:
                return json.loads(task_data)

            return None

        except Exception as e:
            logger.error(f"获取文档信息失败: {e}")
            return None

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取文档列表（使用Pipeline优化）

        Args:
            skip: 跳过数量
            limit: 返回数量

        Returns:
            文档列表
        """
        try:
            # 从任务列表获取ID
            task_ids = self.redis_client.lrange("document:tasks", skip, skip + limit - 1)

            if not task_ids:
                return []

            # 使用Pipeline批量获取文档数据（性能优化）
            documents = []
            if self.redis_client.client:
                pipeline = self.redis_client.client.pipeline()

                for task_id in task_ids:
                    task_key = f"document:task:{task_id}"
                    pipeline.get(task_key)

                results = pipeline.execute()

                for task_data in results:
                    if task_data:
                        documents.append(json.loads(task_data))
            else:
                # Fallback: 逐个获取（当pipeline不可用时）
                for task_id in task_ids:
                    task_key = f"document:task:{task_id}"
                    task_data = self.redis_client.get(task_key)
                    if task_data:
                        documents.append(json.loads(task_data))

            return documents

        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

    async def count_documents(self) -> int:
        """
        统计文档总数

        Returns:
            文档总数
        """
        try:
            return self.redis_client.llen("document:tasks")
        except Exception as e:
            logger.error(f"统计文档失败: {e}")
            return 0

    async def count_processing(self) -> int:
        """
        统计处理中的文档数量

        Returns:
            处理中的文档数量
        """
        try:
            task_ids = self.redis_client.lrange("document:tasks", 0, -1)
            processing_count = 0

            for task_id in task_ids:
                task_key = f"document:task:{task_id}"
                task_data = self.redis_client.get(task_key)

                if task_data:
                    task_info = json.loads(task_data)
                    if task_info.get("status") == "processing":
                        processing_count += 1

            return processing_count

        except Exception as e:
            logger.error(f"统计处理中文档失败: {e}")
            return 0

    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        try:
            # 获取文档信息
            doc_info = await self.get_document(doc_id)

            if not doc_info:
                return False

            # 删除文件
            file_path = doc_info.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"删除文件: {file_path}")

            # 从Redis删除
            task_key = f"document:task:{doc_id}"
            progress_key = f"document:progress:{doc_id}"

            self.redis_client.delete(task_key)
            self.redis_client.delete(progress_key)
            self.redis_client.lrem("document:tasks", 0, doc_id)

            logger.info(f"删除文档: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
