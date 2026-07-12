"""
Node: Finalize

Complete the workflow and save results
"""
from loguru import logger
from ..state import DocumentProcessingState


async def finalize(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 7: Finalize workflow
    """
    logger.info("[Finalize] Completing workflow")

    destinations_count = len(state.get('destinations', []))

    logger.success(f"[Workflow] Completed: {destinations_count} destinations processed")

    return state
