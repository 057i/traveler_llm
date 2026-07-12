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

    # Embedding 模型配置
    EMBEDDING_MODEL: str = "./models/bge-base-zh-v1.5"
    EMBEDDING_DIM: int = 768  # bge-base-zh-v1.5的维度

    # Rerank 模型配置
    RERANK_MODEL_PATH: str = "./models/BAAI--bge-reranker-v2-m3/snapshots/master"

    # RAG 配置
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.65

    # RRF 配置
    RRF_K: int = 60

    # Rerank 配置
    RERANK_TOP_N: int = 3
    RERANK_MODEL: str = "qwen-turbo"

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