"""
Node: MinIO Storage
"""
import os
import tempfile
from loguru import logger
from ..state import DocumentProcessingState


async def save_to_minio(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 1: Save file to MinIO (currently local storage)
    """
    logger.info("[MinIO] Saving file to local storage")

    try:
        file_path = state.get('file_path')

        if file_path and os.path.exists(file_path):
            state['minio_success'] = True
            state['minio_path'] = file_path
            logger.success(f"[MinIO] Using file: {file_path}")
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    except Exception as e:
        logger.error(f"[MinIO] Save failed: {e}")
        state["minio_success"] = False

    return state


async def minio_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip MinIO storage
    """
    logger.warning("[MinIO] Using fallback - skipping MinIO storage")
    state["minio_success"] = True
    return state
