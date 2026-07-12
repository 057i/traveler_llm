"""
MinIO Client for File Storage

使用真实的MinIO服务器进行对象存储
"""
from minio import Minio
from minio.error import S3Error
from typing import Optional
from loguru import logger
from pathlib import Path
from config.settings import settings
import os


class MinIOClient:
    """MinIO客户端 - 使用真实MinIO服务器"""

    def __init__(self):
        """
        初始化MinIO客户端

        从环境变量读取配置：
        - MINIO_ENDPOINT: MinIO服务器地址（如：localhost:9000）
        - MINIO_ACCESS_KEY: 访问密钥
        - MINIO_SECRET_KEY: 密钥
        - MINIO_BUCKET: 存储桶名称
        - MINIO_SECURE: 是否使用HTTPS
        """
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET
        self.secure = settings.MINIO_SECURE

        try:
            # 创建MinIO客户端
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )

            # 确保bucket存在
            self._ensure_bucket()

            logger.success(f"[MinIO] Connected to {self.endpoint}, bucket: {self.bucket_name}")

        except Exception as e:
            logger.error(f"[MinIO] Connection failed: {e}")
            raise

    def _ensure_bucket(self):
        """确保bucket存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"[MinIO] Created bucket: {self.bucket_name}")
            else:
                logger.info(f"[MinIO] Bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"[MinIO] Bucket check failed: {e}")
            raise

    def save_file(self, file_path: str, destination_name: Optional[str] = None) -> str:
        """
        保存文件到MinIO

        Args:
            file_path: 源文件路径
            destination_name: 目标文件名（可选，默认使用源文件名）

        Returns:
            MinIO中的对象名称
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # 确定对象名称
            object_name = destination_name or os.path.basename(file_path)

            # 上传文件
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )

            logger.success(f"[MinIO] File uploaded: {object_name}")
            return object_name

        except S3Error as e:
            logger.error(f"[MinIO] Upload failed: {e}")
            raise
        except Exception as e:
            logger.error(f"[MinIO] Save failed: {e}")
            raise

    def get_file(self, object_name: str, local_path: str) -> str:
        """
        从MinIO下载文件

        Args:
            object_name: MinIO中的对象名称
            local_path: 本地保存路径

        Returns:
            本地文件路径
        """
        try:
            # 确保目录存在
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            # 下载文件
            self.client.fget_object(
                self.bucket_name,
                object_name,
                local_path
            )

            logger.success(f"[MinIO] File downloaded: {object_name} -> {local_path}")
            return local_path

        except S3Error as e:
            logger.error(f"[MinIO] Download failed: {e}")
            raise
        except Exception as e:
            logger.error(f"[MinIO] Get file failed: {e}")
            raise

    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_name: MinIO中的对象名称

        Returns:
            是否存在
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"[MinIO] Check existence failed: {e}")
            return False

    def delete_file(self, object_name: str) -> bool:
        """
        删除文件

        Args:
            object_name: MinIO中的对象名称

        Returns:
            是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.success(f"[MinIO] File deleted: {object_name}")
            return True

        except S3Error as e:
            logger.error(f"[MinIO] Delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"[MinIO] Delete failed: {e}")
            return False

    def list_files(self, prefix: str = "") -> list:
        """
        列出所有文件

        Args:
            prefix: 对象名称前缀（可选）

        Returns:
            对象名称列表
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            files = [obj.object_name for obj in objects]
            return files

        except S3Error as e:
            logger.error(f"[MinIO] List files failed: {e}")
            return []
        except Exception as e:
            logger.error(f"[MinIO] List files failed: {e}")
            return []

    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        获取文件的预签名URL

        Args:
            object_name: MinIO中的对象名称
            expires: URL过期时间（秒），默认1小时

        Returns:
            预签名URL
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url

        except S3Error as e:
            logger.error(f"[MinIO] Get URL failed: {e}")
            return ""
        except Exception as e:
            logger.error(f"[MinIO] Get URL failed: {e}")
            return ""


# 单例
_minio_client = None


def get_minio_client() -> MinIOClient:
    """获取MinIO客户端单例"""
    global _minio_client

    if _minio_client is None:
        _minio_client = MinIOClient()

    return _minio_client
