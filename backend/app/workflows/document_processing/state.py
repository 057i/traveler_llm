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

    # Task info - task_id不应该被修改，保持单值
    task_id: str
    doc_id: str  # 新增：文档ID（用于元数据管理）
    filename: str
    file_path: str
    pages_count: int  # PDF页数
    original_filename: str  # 原始文件名（含扩展名）

    # Processing steps
    raw_text: str  # Raw text from MinerU
    markdown_text: str  # Markdown format from MinerU
    parsed_text: str  # Final parsed text
    chunks: List[str]  # Text chunks
    destinations: List[Destination]  # Extracted destinations

    # MinIO info
    minio_directory: str  # MinIO目录名
    minio_bucket: str  # MinIO桶名
    minio_folder: str  # MinIO文件夹路径
    minio_uploaded_files: List[str]  # 已上传的文件列表
    mineru_output_dir: Optional[str]  # MinerU输出目录
    mineru_has_package: bool  # 是否有MinerU输出包

    # Vectorization resource IDs
    milvus_chunk_ids: List[str]  # Milvus中的chunk IDs
    images_count: int  # 图片数量

    # Step success flags
    minio_success: bool
    minio_upload_success: bool  # 新增：解析后MinIO上传成功标志
    parse_success: bool
    chunk_success: bool
    extract_success: bool
    vector_success: bool  # RAG vectorization
    graph_vector_success: bool  # GraphRAG
    finalize_success: bool

    # Error tracking (使用Reducer处理并发)
    errors: Annotated[List[str], add]  # 使用add reducer合并并发错误
