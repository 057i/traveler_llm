"""
Team Recommendation WebSocket API - Enhanced with detailed progress tracking

Real-time AI team recommendation with step-by-step progress updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import json

router = APIRouter(prefix="/api/team-recommend-ws", tags=["Team Recommendation"])


@router.websocket("/stream")
async def team_recommend_websocket(websocket: WebSocket):
    """
    Team recommendation WebSocket endpoint with enhanced progress tracking

    Streams real-time progress from multiple AI agents:
    - Budget Expert
    - Itinerary Planner
    - Food Assistant
    - Transport Assistant
    - RAG Assistant
    """
    await websocket.accept()
    logger.info("[TeamRecommendWS] Client connected")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get('query', '')
            session_id = message.get('session_id')

            logger.info(f"[TeamRecommendWS] Query received: {query[:50]}...")

            # Send initialization message
            await websocket.send_json({
                "type": "start",
                "message": "AI Team is analyzing your request",
                "timestamp": None
            })

            # Import and use the service
            try:
                from app.workflows.team_recommend.service import get_team_recommend_service

                service = get_team_recommend_service()

                # Stream results
                async for progress_update in service.recommend_stream(
                    query=query,
                    session_id=session_id
                ):
                    # Enhanced progress messages with better formatting
                    if progress_update.get('type') == 'progress':
                        # Agent progress update
                        agent_name = progress_update.get('agent', 'Unknown Agent')
                        status = progress_update.get('status', 'working')
                        message_text = progress_update.get('message', '')
                        progress_value = progress_update.get('progress', 0)

                        # Map status to user-friendly messages
                        status_messages = {
                            'started': f'{agent_name} started analysis',
                            'working': f'{agent_name}: {message_text}',
                            'completed': f'{agent_name} completed',
                            'error': f'{agent_name} encountered an issue'
                        }

                        await websocket.send_json({
                            "type": "progress",
                            "agent": agent_name,
                            "status": status,
                            "message": status_messages.get(status, message_text),
                            "progress": progress_value,
                            "detail": message_text
                        })

                    elif progress_update.get('type') == 'answer':
                        # Final answer received
                        await websocket.send_json({
                            "type": "answer",
                            "answer": progress_update.get('answer', ''),
                            "sources": progress_update.get('sources', []),
                            "metadata": progress_update.get('metadata', {}),
                            "agent_logs": progress_update.get('agent_logs', [])
                        })

                    elif progress_update.get('type') == 'complete':
                        # Completion message
                        await websocket.send_json({
                            "type": "complete",
                            "message": "AI Team recommendation completed successfully",
                            "progress": 100
                        })

                    elif progress_update.get('type') == 'error':
                        # Error message
                        await websocket.send_json({
                            "type": "error",
                            "message": progress_update.get('message', 'An error occurred'),
                            "error": progress_update.get('error', '')
                        })

            except Exception as e:
                logger.error(f"[TeamRecommendWS] Service error: {e}")
                import traceback
                traceback.print_exc()

                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to process recommendation",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        logger.info("[TeamRecommendWS] Client disconnected")
    except Exception as e:
        logger.error(f"[TeamRecommendWS] Connection error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "WebSocket connection error",
                "error": str(e)
            })
        except:
            pass


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "team_recommend_ws",
        "version": "1.0.0"
    }
