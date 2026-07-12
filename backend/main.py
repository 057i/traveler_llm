"""
FastAPI 主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config.settings import settings
from app.api import documents, chat, ai_recommend, team_recommend_ws, integrated_search

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
        from app.core.neo4j_graph_client import get_graph_rag_engine
        graph_engine = get_graph_rag_engine()
        graph_engine.close()
        logger.info("图数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭资源时出错: {e}")


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
app.include_router(chat.router)
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