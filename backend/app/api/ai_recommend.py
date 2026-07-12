"""
AI Recommendation API

Real-time AI recommendation using SSE streaming
Integrates with LangGraph workflow for intelligent travel suggestions
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import json
import asyncio

from app.workflows.ai_recommend.service import get_ai_recommend_service
from app.services.progress_tracker import get_progress_tracker
from app.core.redis_client import get_redis_client

router = APIRouter(prefix="/api/ai-recommend", tags=["AI Recommendation"])


class RecommendRequest(BaseModel):
    """Recommendation request"""
    query: str
    session_id: str
    budget: Optional[str] = None
    season: Optional[str] = None
    travel_type: Optional[str] = None
    duration: Optional[str] = None
    interests: Optional[List[str]] = None


@router.get("/stream")
async def ai_recommend_stream_get(
    query: str,
    session_id: str,
    budget: Optional[str] = None,
    season: Optional[str] = None,
    travel_type: Optional[str] = None,
    duration: Optional[str] = None
):
    """
    AI Recommendation with SSE streaming (GET method for EventSource)

    Real-time progress updates through Server-Sent Events
    Shows detailed workflow execution steps
    """
    try:
        async def event_generator():
            """Generate SSE event stream"""
            try:
                # Initialize progress tracking
                tracker = get_progress_tracker()
                tracker.start_progress(session_id, "AI Recommendation")

                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting AI recommendation workflow'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                # Get AI recommendation service
                service = get_ai_recommend_service()

                # Track nodes for frontend display
                executed_nodes = []

                # Process with workflow
                async for event in service.process_stream(
                    user_query=query,
                    session_id=session_id
                ):
                    # Parse SSE data
                    if event.startswith('data: '):
                        data_str = event[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)

                                # Track node execution
                                if data.get('type') == 'progress' and data.get('node'):
                                    node_name = data.get('node')
                                    executed_nodes.append({
                                        'name': node_name,
                                        'message': data.get('message', ''),
                                        'status': 'success',
                                        'icon': 'Check',
                                        'color': '#67c23a'
                                    })

                                    # Send progress with nodes
                                    progress_event = {
                                        'type': 'progress',
                                        'node': node_name,
                                        'message': data.get('message', ''),
                                        'nodes': executed_nodes.copy()
                                    }
                                    yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

                                elif data.get('type') == 'complete':
                                    # Final result
                                    result = {
                                        'type': 'complete',
                                        'answer': data.get('answer', ''),
                                        'sources': data.get('sources', []),
                                        'nodes': executed_nodes,
                                        'message': 'AI recommendation completed'
                                    }
                                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

                                    # Save to Redis history
                                    try:
                                        redis_client = get_redis_client()
                                        history_key = f"ai_recommend:history:{session_id}"
                                        redis_client.lpush(history_key, json.dumps({
                                            'query': query,
                                            'answer': data.get('answer', ''),
                                            'sources': data.get('sources', []),
                                            'timestamp': asyncio.get_event_loop().time()
                                        }, ensure_ascii=False))
                                        redis_client.expire(history_key, 86400)
                                    except Exception as redis_error:
                                        logger.warning(f"Failed to save to Redis: {redis_error}")

                                elif data.get('type') == 'error':
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                            except json.JSONDecodeError:
                                pass

                    # Forward the event
                    yield event

                # Update progress
                tracker.complete_progress(session_id)

            except Exception as e:
                logger.error(f"AI recommendation streaming failed: {e}")
                import traceback
                traceback.print_exc()

                error_data = {
                    'type': 'error',
                    'error': str(e),
                    'message': 'AI recommendation failed'
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"AI recommendation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def ai_recommend_stream(request: RecommendRequest):
    """
    AI Recommendation with SSE streaming

    Real-time progress updates through Server-Sent Events
    Shows detailed workflow execution steps
    """
    try:
        async def event_generator():
            """Generate SSE event stream"""
            try:
                # Initialize progress tracking
                tracker = get_progress_tracker()
                tracker.start_progress(request.session_id, "AI Recommendation")

                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting AI recommendation workflow'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                # Get AI recommendation service
                service = get_ai_recommend_service()

                # Track nodes for frontend display
                executed_nodes = []

                # Process with workflow
                async for event in service.process_stream(
                    user_query=request.query,
                    session_id=request.session_id
                ):
                    # Parse SSE data
                    if event.startswith('data: '):
                        data_str = event[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)

                                # Track node execution
                                if data.get('type') == 'progress' and data.get('node'):
                                    node_name = data.get('node')
                                    executed_nodes.append({
                                        'name': node_name,
                                        'message': data.get('message', ''),
                                        'status': 'success',
                                        'icon': 'Check',
                                        'color': '#67c23a'
                                    })

                                    # Send progress with nodes
                                    progress_event = {
                                        'type': 'progress',
                                        'node': node_name,
                                        'message': data.get('message', ''),
                                        'nodes': executed_nodes.copy()
                                    }
                                    yield f"data: {json.dumps(progress_event, ensure_ascii=False)}\n\n"

                                elif data.get('type') == 'complete':
                                    # Final result
                                    result = {
                                        'type': 'complete',
                                        'answer': data.get('answer', ''),
                                        'sources': data.get('sources', []),
                                        'nodes': executed_nodes,
                                        'message': 'AI recommendation completed'
                                    }
                                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

                                    # Save to Redis history
                                    try:
                                        redis_client = get_redis_client()
                                        history_key = f"ai_recommend:history:{request.session_id}"
                                        redis_client.lpush(history_key, json.dumps({
                                            'query': request.query,
                                            'answer': data.get('answer', ''),
                                            'sources': data.get('sources', []),
                                            'timestamp': asyncio.get_event_loop().time()
                                        }, ensure_ascii=False))
                                        redis_client.expire(history_key, 86400)
                                    except Exception as redis_error:
                                        logger.warning(f"Failed to save to Redis: {redis_error}")

                                elif data.get('type') == 'error':
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                            except json.JSONDecodeError:
                                pass

                    # Forward the event
                    yield event

                # Update progress
                tracker.complete_progress(request.session_id)

            except Exception as e:
                logger.error(f"AI recommendation streaming failed: {e}")
                import traceback
                traceback.print_exc()

                error_data = {
                    'type': 'error',
                    'error': str(e),
                    'message': 'AI recommendation failed'
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"AI recommendation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "ai_recommend",
        "version": "1.0.0"
    }
