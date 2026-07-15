"""
综合搜索 API

功能：
1. RAG多路检索（Milvus向量 + Neo4j图数据 + Tavily网络搜索）
2. 结构化筛选（按预算、季节、类型等）
3. SSE流式传输（实时推送搜索进度）
4. RRF融合算法（多路结果融合排序）
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
import json

router = APIRouter(prefix="/api/integrated-search", tags=["综合搜索"])


class SearchRequest(BaseModel):
    """
    搜索请求模型

    属性：
        query: 搜索关键词
        filters: 筛选条件字典（可选）
        top_k: 返回结果数量，默认20条
    """
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 20


@router.post("/search/stream")
async def search_stream(request: SearchRequest = Body(...)):
    """
    流式综合搜索（SSE）

    功能：
        - 使用SSE（Server-Sent Events）实时推送搜索进度
        - 并行执行多路检索（向量、图、网络）
        - 逐步推送每一路的检索结果
        - 最后推送融合后的最终结果

    参数：
        request: 搜索请求对象

    返回：
        StreamingResponse: SSE流式响应
            - type: 'progress' - 进度更新
            - type: 'result' - 单条结果
            - type: 'complete' - 搜索完成
            - type: 'error' - 错误信息

    异常：
        HTTPException: 当启动搜索流失败时抛出500错误
    """
    try:
        logger.info(f"[综合搜索] 流式搜索请求: {request.query}")

        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()

        async def event_generator():
            """
            SSE事件生成器

            功能：
                - 异步生成SSE格式的事件流
                - 处理搜索服务返回的各类事件
                - 错误处理和异常捕获
            """
            try:
                async for event in search_service.search_stream(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.top_k
                ):
                    # 转换为SSE格式：data: {JSON}\n\n
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"[综合搜索] 流处理错误: {e}")
                error_event = {
                    'type': 'error',
                    'message': f'搜索过程中发生错误: {str(e)}'
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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
        logger.error(f"[综合搜索] 启动流式搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动搜索失败: {str(e)}")


@router.post("/search")
async def search(request: SearchRequest = Body(...)):
    """
    普通综合搜索（非流式）

    功能：
        - 执行完整的综合搜索流程
        - 等待所有结果返回后一次性响应
        - 适合需要完整结果的场景

    参数：
        request: 搜索请求对象

    返回：
        dict: 搜索结果
            - status: 状态码 'success' 或 'error'
            - results: 结果列表
            - metadata: 元数据信息
                - total: 总结果数
                - returned: 实际返回数
                - message: 提示信息

    异常：
        HTTPException: 当搜索失败时抛出500错误
    """
    try:
        logger.info(f"[综合搜索] 普通搜索请求: {request.query}")

        from app.services.integrated_search_service import get_integrated_search_service
        search_service = get_integrated_search_service()

        results = []
        metadata = {}

        # 收集所有流式事件中的结果
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
        logger.error(f"[综合搜索] 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/health")
async def health():
    """
    健康检查接口

    功能：
        - 检查综合搜索服务是否正常运行
        - 用于监控和负载均衡

    返回：
        dict: 健康状态
            - status: 状态 'ok'
            - service: 服务名称
    """
    return {
        "status": "ok",
        "service": "integrated_search_v2"
    }
