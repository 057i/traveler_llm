"""
Node: Finalize

完成工作流：
1. 保存元数据到Redis
2. 清理临时文件
3. 发送完成通知
"""
from loguru import logger
from ..state import DocumentProcessingState
from app.utils.sse_utils import send_node_start, send_node_end
from app.services.document_metadata_service import get_document_metadata_service
from app.utils.temp_file_manager import get_temp_file_manager

FLOW_TYPE = "document"


async def finalize(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 完成处理

    流程:
        1. 保存文档元数据到Redis
        2. 清理临时文件
        3. 发送完成通知

    Args:
        state: 工作流状态

    Returns:
        更新后的状态
    """
    task_id = state.get('task_id')
    doc_id = state.get('doc_id')

    # 发送node_start事件
    if task_id:
        await send_node_start(
            task_id=task_id,
            flow_type=FLOW_TYPE,
            step_id="finalize",
            step_name="完成",
            progress=100,
            message="正在完成处理..."
        )

    logger.info("[Finalize] === Finalizing workflow ===")

    try:
        # Step 1: 保存元数据到Redis
        metadata_service = get_document_metadata_service()

        # 更新Milvus chunk IDs
        milvus_chunk_ids = state.get('milvus_chunk_ids', [])
        if milvus_chunk_ids:
            metadata_service.update_milvus_chunks(doc_id, milvus_chunk_ids)
            logger.info(f"[Finalize] Updated Milvus chunks: {len(milvus_chunk_ids)}")

        # 更新Neo4j实体名称
        destinations = state.get('destinations', [])
        entity_names = [d.get('name') for d in destinations if d.get('name')]
        if entity_names:
            metadata_service.update_neo4j_entities(doc_id, entity_names)
            logger.info(f"[Finalize] Updated Neo4j entities: {len(entity_names)}")

        # 更新图片数量
        images_count = state.get('images_count', 0)
        if images_count > 0:
            metadata_service.update_images_count(doc_id, images_count)

        # 更新页数
        pages_count = state.get('pages_count', 0)
        if pages_count > 0:
            metadata_service._update_field(doc_id, 'pages_count', pages_count)

        # 提取省份和城市（从第一个实体）
        if destinations:
            first_dest = destinations[0]
            province = first_dest.get('province', '-')
            city = first_dest.get('city', '-')
            metadata_service._update_field(doc_id, 'province', province)
            metadata_service._update_field(doc_id, 'city', city)
            logger.info(f"[Finalize] Updated location: {province} - {city}")

        # 更新状态为completed
        metadata_service.update_status(doc_id, "completed")

        logger.success(f"[Finalize] ✅ Metadata saved to Redis")

        # Step 2: 清理临时文件
        temp_manager = get_temp_file_manager()
        cleanup_success = temp_manager.cleanup_temp_dir(doc_id)

        if cleanup_success:
            logger.success(f"[Finalize] ✅ Cleaned up temp files")
        else:
            logger.warning(f"[Finalize] ⚠️ Failed to cleanup temp files")

        # 统计信息
        chunks_count = len(state.get('chunks', []))
        stats = {
            'destinations_count': len(destinations),
            'chunks_count': chunks_count,
            'images_count': images_count,
            'pages_count': pages_count
        }

        state['finalize_success'] = True
        state['statistics'] = stats

        logger.success(
            f"[Finalize] === Workflow completed: {stats['destinations_count']} destinations, "
            f"{stats['chunks_count']} chunks, {stats['pages_count']} pages ==="
        )

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="finalize",
                step_name="完成",
                progress=100,
                message=f"处理完成 ({stats['destinations_count']} 个景点, {stats['chunks_count']} 个文本块)"
            )

    except Exception as e:
        logger.error(f"[Finalize] Finalization failed: {e}")
        import traceback
        traceback.print_exc()
        return {"finalize_success": False}

    # 只返回修改的字段，避免并发冲突
    return {"finalize_success": True}
