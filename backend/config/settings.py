"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # Qwen API 配置
    DASHSCOPE_API_KEY: str
    QWEN_MODEL_NAME: str = "qwen-turbo"
    QWEN_MODEL: str = "qwen-turbo"  # 添加别名

    # MinerU API 配置（官方API https://mineru.net）
    MINERU_API_KEY: str = ""
    MINERU_TIMEOUT: int = 300

    # Tavily API 配置
    TAVILY_API_KEY: str = ""

    # Milvus 配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "travel_destinations"
    MILVUS_URI: str = "http://localhost:19530"

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "..123456"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "travel-documents"
    MINIO_SECURE: bool = False

    # MinerU 配置 (PDF解析)
    MINERU_API_KEY: str = ""  # 旧版兼容
    MINERU_API_TOKEN: str = ""  # V2需要
    MINERU_BASE_URL: str = "https://mineru.net/api/v4"  # V2需要

    # Embedding 模型配置
    EMBEDDING_MODEL: str = "./models/bge-base-zh-v1.5"
    EMBEDDING_DIM: int = 768  # bge-base-zh-v1.5的维度

    # Rerank 模型配置
    RERANK_MODEL_PATH: str = "./models/BAAI--bge-reranker-v2-m3/snapshots/master"

    # RAG 配置
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.65

    # === Milvus混合检索配置 ===
    MILVUS_DENSE_TOP_K: int = 10        # 稠密检索返回数量
    MILVUS_SPARSE_TOP_K: int = 10       # 稀疏检索返回数量
    MILVUS_EXACT_MATCH_TOP_K: int = 5   # 精确匹配返回数量
    MILVUS_HYBRID_TOP_K: int = 15       # 混合后返回数量（增加：10→15）

    # === 质量过滤配置（方案B：分路过滤）===
    QUALITY_FILTER_ENABLED: bool = True   # 启用质量过滤
    DENSE_SCORE_THRESHOLD: float = 0.7    # 稠密检索分值阈值（保持0.7）
    SPARSE_SCORE_THRESHOLD: float = 0.35  # 稀疏检索分值阈值（保持0.35）

    # === Milvus索引配置 ===
    MILVUS_INDEX_TYPE: str = "HNSW"     # HNSW索引（高性能）
    MILVUS_INDEX_M: int = 16            # HNSW邻居数
    MILVUS_INDEX_EF_CONSTRUCTION: int = 200  # HNSW构建参数
    MILVUS_SEARCH_EF: int = 64          # HNSW搜索参数

    # === RRF融合权重配置 ===
    RRF_MILVUS_WEIGHT: float = 0.7      # Milvus结果权重
    RRF_TAVILY_WEIGHT: float = 0.3      # Tavily结果权重
    RRF_K: int = 60                     # RRF参数

    # === 置信度检查配置 ===
    CONFIDENCE_THRESHOLD: float = 0.6   # 低于此值调用Tavily

    # === Neo4j检索配置 ===
    NEO4J_NEARBY_LIMIT: int = 10        # Neo4j附近检索数量

    # RRF 配置
    RRF_K: int = 60

    # Rerank 配置
    RERANK_TOP_N: int = 10  # 最多重排10个候选
    RERANK_THRESHOLD: float = 0.5  # Rerank分数阈值（0-1）
    RERANK_MIN_RESULTS: int = 3  # 最少返回结果数（保留配置，但不强制保底）
    RERANK_MAX_RESULTS: int = 7  # 最多返回结果数
    RERANK_MODEL: str = "bge-reranker-v2-m3"  # 本地模型标识

    # ChromaDB 配置（已废弃，保留兼容）
    CHROMA_PERSIST_DIRECTORY: str = "./data/vector_store"
    CHROMA_COLLECTION_NAME: str = "travel_destinations"

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()