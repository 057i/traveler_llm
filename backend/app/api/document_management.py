"""
API Router: Document Management

文档管理API：
- 列出所有文档
- 获取文档详情
- 删除文档（级联删除所有资源）
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from loguru import logger

from app.services.document_metadata_service import get_document_metadata_service
from app.services.document_deletion_service import get_document_deletion_service


router = APIRouter(prefix="/api/documents", tags=["Document Management"])


@router.get("/list", summary="列出所有文档")
async def list_documents() -> Dict[str, Any]:
    """
    列出所有已上传的文档

    Returns:
        {
            "success": true,
            "documents": [
                {
                    "doc_id": "uuid",
                    "filename": "峨眉山攻略.pdf",
                    "upload_time": "2026-07-13 22:30:00",
                    "status": "completed",
                    "chunks_count": 15,
                    "entities_count": 8,
                    ...
                }
            ]
        }
    """
    try:
        metadata_service = get_document_metadata_service()
        documents = metadata_service.list_all_documents()

        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        logger.error(f"[DocumentAPI] Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", summary="获取文档详情")
async def get_document(doc_id: str) -> Dict[str, Any]:
    """
    获取指定文档的详细信息

    Args:
        doc_id: 文档ID

    Returns:
        文档元数据
    """
    try:
        metadata_service = get_document_metadata_service()
        metadata = metadata_service.get_document_metadata(doc_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "success": True,
            "document": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DocumentAPI] Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    级联删除文档及其所有资源

    删除内容：
    1. MinIO中的所有文件（PDF + Markdown + 图片）
    2. Milvus中的所有向量
    3. Neo4j中的所有实体
    4. Redis中的元数据

    Args:
        doc_id: 文档ID

    Returns:
        {
            "success": true,
            "deleted": {
                "minio": true,
                "milvus": 15,  # 删除的chunk数量
                "neo4j": 8,    # 删除的实体数量
                "redis": true
            },
            "message": "文档及所有资源已删除"
        }
    """
    try:
        deletion_service = get_document_deletion_service()
        result = await deletion_service.delete_document(doc_id)

        if not result["success"]:
            return {
                "success": False,
                "message": "文档删除失败",
                "details": result["deleted"],
                "errors": result.get("errors", [])
            }

        return {
            "success": True,
            "deleted": result["deleted"],
            "message": "文档及所有资源已成功删除"
        }

    except Exception as e:
        logger.error(f"[DocumentAPI] Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-temp", summary="清理所有临时文件")
async def cleanup_temp_files() -> Dict[str, Any]:
    """
    清理所有临时文件（管理员功能）

    Returns:
        清理的文件数量
    """
    try:
        from app.utils.temp_file_manager import get_temp_file_manager
        temp_manager = get_temp_file_manager()

        count = temp_manager.cleanup_all_temp_files()

        return {
            "success": True,
            "cleaned_count": count,
            "message": f"已清理 {count} 个临时目录"
        }

    except Exception as e:
        logger.error(f"[DocumentAPI] Failed to cleanup temp files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
