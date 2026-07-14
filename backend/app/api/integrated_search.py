"""
综合搜索 API - 升级版

添加：
1. RAG多路检索
2. 结构化筛选
3. SSE流式传输
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
import json

router = APIRouter(prefix="/api/integrated-search", tags=["综合搜索"])


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 20


@router.post("/search/stream")
async def search_stream(request: SearchRequest = Body(...)):
    """
    流式综合搜索（SSE）
    
    返回SSE流，实时传输搜索进度和结果
    """
    try:
        logger.info(f"[IntegratedSearch] Stream search: {request.query}")
        
        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()
        
        async def event_generator():
            """SSE事件生成器"""
            try:
                async for event in search_service.search_stream(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.top_k
                ):
                    # 转换为SSE格式
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
            except Exception as e:
                logger.error(f"[IntegratedSearch] Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"[IntegratedSearch] Failed to start stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(request: SearchRequest = Body(...)):
    """
    普通综合搜索（非流式）
    
    直接返回所有结果
    """
    try:
        logger.info(f"[IntegratedSearch] Search: {request.query}")
        
        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()
        
        results = []
        metadata = {}
        
        async for event in search_service.search_stream(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k
        ):
            if event['type'] == 'result':
                results.append(event['data'])
            elif event['type'] == 'complete':
                metadata = {
                    'total': event['total'],
                    'returned': event['returned'],
                    'message': event['message']
                }
        
        return {
            "status": "success",
            "results": results,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"[IntegratedSearch] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "integrated_search_v2"}
