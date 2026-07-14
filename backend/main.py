"""
FastAPI 主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config.settings import settings
from app.api import documents, ai_recommend, team_recommend_ws, integrated_search

# 配置日志
logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info("=" * 80)
    logger.info("[SYSTEM] 智能旅行推荐系统启动中...")
    logger.info("=" * 80)

    # 服务健康检查
    await check_services()

    logger.info(f"API 地址: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"文档地址: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"日志文件: {settings.LOG_FILE}")
    logger.info(f"Milvus URI: {settings.MILVUS_URI}")
    logger.info(f"Neo4j URI: {settings.NEO4J_URI}")
    logger.info(f"Redis HOST: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info("=" * 80)
    logger.success("[SYSTEM] 智能旅行推荐系统启动完成")
    logger.info("=" * 80)

    yield

    # 关闭事件
    logger.info("智能旅行推荐系统正在关闭...")
    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()
        neo4j_client.close()
        logger.info("图数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭资源时出错: {e}")


async def check_services():
    """检查所有服务连接状态"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("[健康检查] 检查服务连接...")
    logger.info("=" * 80)

    all_ok = True

    # 1. 检查Milvus
    logger.info("[1/4] 检查Milvus连接...")
    try:
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client
        milvus = get_milvus_hybrid_client()
        count = milvus.get_count()
        logger.success(f"  ✓ Milvus连接成功 (当前向量数: {count})")
    except Exception as e:
        logger.error(f"  ✗ Milvus连接失败: {str(e)[:100]}")
        logger.warning("  → 启动命令: start_milvus.bat")
        all_ok = False

    # 2. 检查Neo4j
    logger.info("[2/4] 检查Neo4j连接...")
    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j = get_neo4j_client()
        result = neo4j.query("MATCH (n) RETURN count(n) as count")
        node_count = result[0]['count'] if result else 0
        logger.success(f"  ✓ Neo4j连接成功 (当前节点数: {node_count})")
    except Exception as e:
        logger.error(f"  ✗ Neo4j连接失败: {str(e)[:100]}")
        logger.warning("  → 访问 http://localhost:7474")
        all_ok = False

    # 3. 检查Redis
    logger.info("[3/4] 检查Redis连接...")
    try:
        from app.core.redis_client import get_redis_client
        redis = get_redis_client()
        # 测试连接
        redis.get("_health_check")
        logger.success("  ✓ Redis连接成功")
    except Exception as e:
        logger.error(f"  ✗ Redis连接失败: {str(e)[:100]}")
        all_ok = False

    # 4. 检查MinIO/本地存储
    logger.info("[4/4] 检查MinIO/存储...")
    try:
        from app.core.minio_client import get_minio_client
        minio = get_minio_client()
        files = minio.list_files()
        logger.success(f"  ✓ 存储可用 (当前文件数: {len(files)})")
    except Exception as e:
        logger.error(f"  ✗ 存储检查失败: {str(e)[:100]}")
        all_ok = False

    logger.info("=" * 80)
    if all_ok:
        logger.success("[健康检查] 所有服务连接正常 ✓")
    else:
        logger.warning("[健康检查] 部分服务连接失败，请检查上述提示")
    logger.info("=" * 80)
    logger.info("")


# 创建 FastAPI 应用
app = FastAPI(
    title="智能旅行推荐系统",
    description="基于 RAG + GraphRAG + RRF + Rerank 的智能旅行推荐系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(integrated_search.router)
app.include_router(documents.router)
app.include_router(ai_recommend.router)
app.include_router(team_recommend_ws.router)


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "智能旅行推荐系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )