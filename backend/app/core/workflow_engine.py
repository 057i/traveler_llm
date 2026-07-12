"""Workflow Engine - Compatibility Layer"""
from loguru import logger

from app.workflows.document_processing import (
    DocumentProcessingState,
    build_document_processing_graph
)


class WorkflowEngine:
    """Workflow Engine for document processing"""

    def __init__(self):
        """Initialize workflow engine"""
        self.graph = build_document_processing_graph()
        logger.info("Workflow engine initialized")

    async def process_document(
        self,
        task_id: str,
        filename: str,
        file_content: bytes
    ) -> Dict[str, Any]:
        """
        Process document workflow

        Args:
            task_id: Task ID
            filename: Filename
            file_content: File content bytes

        Returns:
            Processing result
        """
        logger.info(f"[WorkflowEngine] Starting document processing: {filename}")

        initial_state = DocumentProcessingState(
            task_id=task_id,
            filename=filename,
            file_content=file_content,
            file_size=len(file_content),
            status="processing",
            current_step="Initializing",
            progress=0,
            error=None,
            error_messages=[],
            minio_path=None,
            parsed_text=None,
            parsed_images=[],
            pages=0,
            text_chunks=[],
            entities=[],
            vector_ids=[],
            graph_ids=[],
            destinations_count=0,
            city="Unknown",
            graph_entities_count=0,
            graph_relationships_count=0,
            minio_success=False,
            parse_success=False,
            chunk_success=False,
            extract_success=False,
            vector_success=False,
            graph_vector_success=False,
        )

        # Execute workflow
        try:
            final_state = await self.graph.ainvoke(initial_state)

            result = {
                "task_id": task_id,
                "status": final_state.get("status", "completed"),
                "filename": final_state["filename"],
                "pages": final_state.get("pages", 0),
                "destinations_count": final_state.get("destinations_count", 0),
                "city": final_state.get("city", "Unknown"),
                "entities": final_state.get("entities", []),
                "graph_entities_count": final_state.get("graph_entities_count", 0),
                "graph_relationships_count": final_state.get("graph_relationships_count", 0),
                "error_messages": final_state.get("error_messages", []),
            }

            logger.success(f"[WorkflowEngine] Completed: {filename}")
            return result

        except Exception as e:
            logger.error(f"[WorkflowEngine] Workflow failed: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "filename": filename,
                "error": str(e),
                "error_messages": [str(e)],
            }


_workflow_engine = None


def get_workflow_engine() -> WorkflowEngine:
    """Get singleton workflow engine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
