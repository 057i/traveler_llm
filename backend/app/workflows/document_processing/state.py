"""
Document Processing Workflow State
"""
from typing import TypedDict, List, Dict, Any


class DocumentProcessingState(TypedDict):
    """State for document processing workflow"""

    # Task info
    task_id: str
    filename: str
    file_path: str

    # Processing steps
    parsed_text: str
    chunks: List[str]
    destinations: List[Dict[str, Any]]

    # Step success flags
    minio_success: bool
    parse_success: bool
    extract_success: bool
    vector_success: bool
    graph_vector_success: bool
