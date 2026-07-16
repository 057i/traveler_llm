"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

# 显式加载 .env 文件
from dotenv import load_dotenv

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# 加载 .env 文件
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    print(f"[CONFIG] 已加载配置文件: {ENV_FILE}")
else:
    print(f"[CONFIG] 警告: .env 文件不存在: {ENV_FILE}")


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() == "true"

    # Qwen API 配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "")  # 添加别名

    # Tavily API 配置
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Milvus 配置
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", ""))
    MILVUS_COLLECTION_NAME: str = os.getenv("MILVUS_COLLECTION_NAME", "")
    MILVUS_URI: str = os.getenv("MILVUS_URI", "")

    # Neo4j 配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", ""))
    REDIS_DB: int = int(os.getenv("REDIS_DB", ""))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # MinIO 配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"

    # MinerU 配置 (PDF解析 - V2 API)
    MINERU_API_KEY: str = os.getenv("MINERU_API_KEY", "")  # 旧版兼容（V1）
    MINERU_API_TOKEN: str = os.getenv("MINERU_API_TOKEN", "")  # V2需要
    MINERU_BASE_URL: str = os.getenv("MINERU_BASE_URL", "https://mineru.net/api/v4")  # V2 API地址
    MINERU_TIMEOUT: int = int(os.getenv("MINERU_TIMEOUT", "300"))  # 请求超时时间（秒）

    # Embedding 模型配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "./models/bge-base-zh-v1.5")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))  # bge-base-zh-v1.5的维度

    # Rerank 模型配置
    RERANK_MODEL_PATH: str = os.getenv("RERANK_MODEL_PATH", "./models/BAAI--bge-reranker-v2-m3/snapshots/master")

    # RAG 配置
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.65"))

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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://103.236.98.149:12580",  # 生产环境前端地址
        "http://103.236.98.149:64042",  # 生产环境后端地址（如果需要）
        "*"  # 允许所有来源（仅开发/测试环境，生产环境应删除）
    ]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()