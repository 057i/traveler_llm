"""
综合搜索 API

使用RRF算法融合多源检索结果
提供综合搜索和多样性搜索功能
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict
from loguru import logger

router = APIRouter(prefix="/api/integrated-search", tags=["综合搜索"])


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    models: List[str] = ["rag"]
    weights: Optional[Dict[str, float]] = None
    top_k: int = 10


class SearchResponse(BaseModel):
    """搜索响应"""
    status: str
    results: List[dict]
    metadata: Dict


@router.post("/search", response_model=SearchResponse)
async def integrated_search(request: SearchRequest = Body(...)):
    """
    综合搜索

    融合多源检索结果，返回综合排序后的推荐
    """
    try:
        logger.info(f"综合搜索: {request.query}, 模型: {request.models}")

        # 这里应该调用实际的搜索服务
        # 目前返回空结果
        response = SearchResponse(
            status="success",
            results=[],
            metadata={
                "models_used": request.models,
                "total_results": 0,
                "method": "rrf_fusion"
            }
        )

        return response

    except Exception as e:
        logger.error(f"综合搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search_with_diversity", response_model=SearchResponse)
async def search_with_diversity(request: SearchRequest = Body(...)):
    """
    综合搜索（带多样性）

    在综合搜索的基础上，增加结果多样性
    """
    try:
        logger.info(f"多样性搜索: {request.query}")

        # 这里应该调用实际的搜索服务
        response = SearchResponse(
            status="success",
            results=[],
            metadata={
                "models_used": request.models,
                "total_results": 0,
                "method": "rrf_fusion_with_diversity"
            }
        )

        return response

    except Exception as e:
        logger.error(f"多样性搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "integrated_search"}