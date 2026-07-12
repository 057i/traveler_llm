"""
Workflow Manager - Centralized workflow management
"""
from app.workflows.sse_workflow import get_sse_workflow
from app.workflows.rrf_workflow import get_rrf_workflow
from loguru import logger


class WorkflowManager:
    """Manages different workflow instances"""

    def __init__(self):
        self.sse_workflow = None
        self.rrf_workflow = None
        self.ws_workflow = None
        self.pdf_workflow = None

    def get_sse_workflow(self):
        if self.sse_workflow is None:
            logger.info("Initializing SSE workflow")
            self.sse_workflow = get_sse_workflow()
        return self.sse_workflow

    def get_rrf_workflow(self):
        if self.rrf_workflow is None:
            logger.info("Initializing RRF workflow")
            self.rrf_workflow = get_rrf_workflow()
        return self.rrf_workflow

    def get_ws_workflow(self):
        if self.ws_workflow is None:
            logger.info("Initializing WebSocket workflow")
            from app.workflows.websocket_workflow import get_websocket_workflow
            self.ws_workflow = get_websocket_workflow()
        return self.ws_workflow


_workflow_manager = None


def get_workflow_manager() -> WorkflowManager:
    """Get workflow manager singleton"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager
