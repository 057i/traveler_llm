"""
Document Metadata Service

管理文档元数据，使用Redis存储文档与资源的映射关系
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import json
from datetime import datetime

from app.core.redis_client import get_redis_client


class DocumentMetadataService:
    """文档元数据服务"""

    def __init__(self):
        self.redis = get_redis_client()

    # ==================== 创建文档元数据 ====================

    def create_document_metadata(
        self,
        doc_id: str,
        filename: str,
        original_name: str,
        file_size: int,
        minio_bucket: str,
        minio_folder: str
    ) -> bool:
        """
        创建文档基本元数据

        Args:
            doc_id: 文档唯一ID
            filename: 标准化文件名
            original_name: 原始文件名
            file_size: 文件大小（字节）
            minio_bucket: MinIO桶名
            minio_folder: MinIO文件夹路径
        """
        try:
            metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "original_name": original_name,
                "upload_time": datetime.now().isoformat(),
                "file_size": file_size,
                "status": "processing",

                # MinIO路径
                "minio_bucket": minio_bucket,
                "minio_folder": minio_folder,
                "minio_paths": {
                    "pdf": f"{minio_folder}{filename}_origin.pdf",
                    "markdown": f"{minio_folder}{filename}.md",
                    "images_folder": f"{minio_folder}images/"
                },

                # 向量化资源ID（初始为空）
                "milvus_chunk_ids": [],
                "neo4j_entity_names": [],

                # 统计信息
                "chunks_count": 0,
                "entities_count": 0,
                "images_count": 0
            }

            # 保存到Redis
            key = f"doc:metadata:{doc_id}"
            self.redis.set(key, json.dumps(metadata, ensure_ascii=False))

            # 添加到文档列表
            self.redis.lpush("docs:list", doc_id)

            # 文件名映射
            self.redis.set(f"docs:filename:{filename}", doc_id)

            logger.success(f"[DocMetadata] Created metadata for {filename}")
            return True

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to create metadata: {e}")
            return False

    # ==================== 更新文档元数据 ====================

    def update_status(self, doc_id: str, status: str) -> bool:
        """更新文档状态：processing/completed/failed"""
        return self._update_field(doc_id, "status", status)

    def update_milvus_chunks(self, doc_id: str, chunk_ids: List[str]) -> bool:
        """更新Milvus chunk IDs"""
        success = self._update_field(doc_id, "milvus_chunk_ids", chunk_ids)
        if success:
            self._update_field(doc_id, "chunks_count", len(chunk_ids))
        return success

    def update_neo4j_entities(self, doc_id: str, entity_names: List[str]) -> bool:
        """更新Neo4j实体名称"""
        success = self._update_field(doc_id, "neo4j_entity_names", entity_names)
        if success:
            self._update_field(doc_id, "entities_count", len(entity_names))
        return success

    def update_images_count(self, doc_id: str, count: int) -> bool:
        """更新图片数量"""
        return self._update_field(doc_id, "images_count", count)

    def _update_field(self, doc_id: str, field: str, value: Any) -> bool:
        """更新元数据中的某个字段"""
        try:
            key = f"doc:metadata:{doc_id}"
            metadata_str = self.redis.get(key)

            if not metadata_str:
                logger.warning(f"[DocMetadata] Document {doc_id} not found")
                return False

            metadata = json.loads(metadata_str)
            metadata[field] = value

            self.redis.set(key, json.dumps(metadata, ensure_ascii=False))
            logger.info(f"[DocMetadata] Updated {field} for {doc_id}")
            return True

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to update {field}: {e}")
            return False

    # ==================== 查询文档元数据 ====================

    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档元数据"""
        try:
            key = f"doc:metadata:{doc_id}"
            metadata_str = self.redis.get(key)

            if not metadata_str:
                return None

            return json.loads(metadata_str)

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to get metadata: {e}")
            return None

    def get_document_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """通过文件名获取文档元数据"""
        try:
            doc_id = self.redis.get(f"docs:filename:{filename}")
            if not doc_id:
                return None

            return self.get_document_metadata(doc_id)

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to get by filename: {e}")
            return None

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """列出所有文档"""
        try:
            doc_ids = self.redis.lrange("docs:list", 0, -1)

            documents = []
            for doc_id in doc_ids:
                metadata = self.get_document_metadata(doc_id)
                if metadata:
                    documents.append(metadata)

            return documents

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to list documents: {e}")
            return []

    # ==================== 删除文档元数据 ====================

    def delete_document_metadata(self, doc_id: str) -> bool:
        """
        删除文档元数据（级联删除前调用，获取资源ID）

        返回True表示成功删除元数据
        """
        try:
            metadata = self.get_document_metadata(doc_id)
            if not metadata:
                logger.warning(f"[DocMetadata] Document {doc_id} not found")
                return False

            # 删除元数据
            self.redis.delete(f"doc:metadata:{doc_id}")

            # 从列表中移除
            self.redis.lrem("docs:list", 0, doc_id)

            # 删除文件名映射
            filename = metadata.get("filename")
            if filename:
                self.redis.delete(f"docs:filename:{filename}")

            logger.success(f"[DocMetadata] Deleted metadata for {doc_id}")
            return True

        except Exception as e:
            logger.error(f"[DocMetadata] Failed to delete metadata: {e}")
            return False


# ==================== 单例 ====================

_metadata_service = None


def get_document_metadata_service() -> DocumentMetadataService:
    """获取文档元数据服务单例"""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = DocumentMetadataService()
    return _metadata_service
