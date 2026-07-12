"""
聊天推荐 API

提供基于聊天的智能旅行推荐功能
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

router = APIRouter(prefix="/api/chat", tags=["聊天推荐"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    context: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    session_id: str
    recommendations: Optional[List[dict]] = None


@router.post("/recommend", response_model=ChatResponse)
async def chat_recommend(request: ChatRequest = Body(...)):
    """
    聊天推荐

    基于用户的聊天消息提供智能推荐

    Args:
        request: 聊天请求
            - message: 用户消息
            - session_id: 会话ID（可选）
            - context: 上下文（可选）

    Returns:
        ChatResponse: 聊天响应
            - reply: 回复内容
            - session_id: 会话ID
            - recommendations: 推荐结果（可选）
    """
    try:
        # 这里应该调用实际的聊天服务
        # 目前返回简单响应
        
        import uuid
        session_id = request.session_id or str(uuid.uuid4())

        response = ChatResponse(
            reply="感谢您的咨询！请使用AI推荐或AI团队推荐功能获取详细建议。",
            session_id=session_id,
            recommendations=None
        )

        return response

    except Exception as e:
        logger.error(f"聊天推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "chat_recommend"}