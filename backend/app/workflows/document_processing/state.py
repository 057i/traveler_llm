"""
Document Processing State with comprehensive fields
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add


class Destination(TypedDict):
    """Destination entity structure"""
    name: str
    city: str
    province: str
    type: str  # "Attraction", "Hotel", "Restaurant", etc.
    description: str
    tags: List[str]
    best_season: List[str]
    budget_range: List[float]  # [min, max]
    suitable_for: List[str]
    features: List[str]
    rating: float
    image_url: str
    graph_id: str
    category: str
    address: str
    opening_hours: str
    ticket_price: str
    visit_duration: str


class DocumentProcessingState(TypedDict):
    """State for document processing workflow"""

    # Task info - 使用Annotated避免并发更新冲突
    task_id: Annotated[str, lambda x, y: y if y else x]  # 保留最新值
    doc_id: Annotated[str, lambda x, y: y if y else x]  # 文档ID，保留最新值
    filename: Annotated[str, lambda x, y: y if y else x]  # 文件名，保留最新值
    file_path: Annotated[str, lambda x, y: y if y else x]  # 文件路径，保留最新值
    pages_count: Annotated[int, lambda x, y: y if y else x]  # PDF页数，保留最新值
    original_filename: Annotated[str, lambda x, y: y if y else x]  # 原始文件名，保留最新值

    # Processing steps - 使用Annotated处理并发
    raw_text: Annotated[str, lambda x, y: y if y else x]  # Raw text from MinerU
    markdown_text: Annotated[str, lambda x, y: y if y else x]  # Markdown format from MinerU
    parsed_text: Annotated[str, lambda x, y: y if y else x]  # Final parsed text
    chunks: Annotated[List[str], lambda x, y: y if y else x]  # Text chunks
    destinations: Annotated[List[Destination], lambda x, y: y if y else x]  # Extracted destinations

    # MinIO info - 使用Annotated处理并发
    minio_directory: Annotated[str, lambda x, y: y if y else x]  # MinIO目录名
    minio_bucket: Annotated[str, lambda x, y: y if y else x]  # MinIO桶名
    minio_folder: Annotated[str, lambda x, y: y if y else x]  # MinIO文件夹路径
    minio_uploaded_files: Annotated[List[str], lambda x, y: y if y else x]  # 已上传的文件列表
    mineru_output_dir: Annotated[Optional[str], lambda x, y: y if y else x]  # MinerU输出目录
    mineru_has_package: Annotated[bool, lambda x, y: y if y else x]  # 是否有MinerU输出包

    # Vectorization resource IDs - 使用Annotated处理并发
    milvus_chunk_ids: Annotated[List[str], lambda x, y: y if y else x]  # Milvus中的chunk IDs
    images_count: Annotated[int, lambda x, y: y if y else x]  # 图片数量

    # Step success flags - 使用Annotated处理并发
    minio_success: Annotated[bool, lambda x, y: y if y else x]
    minio_upload_success: Annotated[bool, lambda x, y: y if y else x]  # 解析后MinIO上传成功标志
    parse_success: Annotated[bool, lambda x, y: y if y else x]
    chunk_success: Annotated[bool, lambda x, y: y if y else x]
    extract_success: Annotated[bool, lambda x, y: y if y else x]
    vector_success: Annotated[bool, lambda x, y: y if y else x]  # RAG vectorization
    graph_vector_success: Annotated[bool, lambda x, y: y if y else x]  # GraphRAG
    finalize_success: Annotated[bool, lambda x, y: y if y else x]

    # Error tracking (使用add reducer合并并发错误)
    errors: Annotated[List[str], add]  # 使用add reducer合并并发错误
