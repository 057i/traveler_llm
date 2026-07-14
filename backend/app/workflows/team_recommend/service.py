"""
Team Recommendation Service
Multi-agent collaboration for travel recommendations
"""
from typing import Dict, Any, AsyncGenerator, List, Optional
from loguru import logger
import asyncio

from .team_manager import get_team_manager


class TeamRecommendService:
    """Team recommendation service with streaming support"""

    def __init__(self):
        self.team_manager = get_team_manager()

    async def recommend_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate recommendations with streaming progress updates

        Args:
            query: User query
            session_id: Session ID for chat history
            chat_history: Previous conversation history

        Yields:
            Progress updates and final result
        """
        logger.info(f"[TeamRecommend] Starting recommendation for: {query[:50]}...")

        # Progress queue for agent updates
        progress_queue = asyncio.Queue()
        task_done = asyncio.Event()

        async def progress_callback(progress_data: Dict[str, Any]):
            """Callback to receive progress from agents"""
            await progress_queue.put(progress_data)

        # Background task to run team manager
        async def run_team():
            try:
                result = await self.team_manager.run(
                    query=query,
                    chat_history=chat_history or [],
                    progress_callback=progress_callback,
                    session_id=session_id
                )
                await progress_queue.put({'_type': 'result', 'data': result})
            except Exception as e:
                logger.error(f"[TeamRecommend] Team execution failed: {e}")
                import traceback
                traceback.print_exc()
                await progress_queue.put({'_type': 'error', 'error': str(e)})
            finally:
                task_done.set()

        # Start background task
        background_task = asyncio.create_task(run_team())

        try:
            # Stream progress updates
            while not task_done.is_set() or not progress_queue.empty():
                try:
                    message = await asyncio.wait_for(progress_queue.get(), timeout=0.5)

                    if message.get('_type') == 'result':
                        # Final result received
                        result = message['data']
                        final_answer = result.get('answer', '')
                        agent_logs = result.get('agent_logs', [])

                        if final_answer and result.get('success', False):
                            yield {
                                'type': 'answer',
                                'answer': final_answer,
                                'sources': result.get('sources', []),
                                'metadata': result.get('metadata', {}),
                                'agent_logs': agent_logs
                            }
                        else:
                            yield {
                                'type': 'error',
                                'message': final_answer or 'Recommendation failed'
                            }

                        # Save to chat history if needed
                        if session_id and final_answer:
                            try:
                                from app.services.chat_history import get_chat_history_service
                                chat_service = get_chat_history_service()
                                await chat_service.add_message(
                                    session_id=session_id,
                                    role="assistant",
                                    content=final_answer,
                                    metadata={
                                        "sources": result.get('sources', []),
                                        "agent_logs": [
                                            {
                                                "agent": log.get("agent"),
                                                "status": log.get("status"),
                                                "message": log.get("message", "")[:100]
                                            }
                                            for log in agent_logs[:5]
                                        ]
                                    }
                                )
                            except Exception as e:
                                logger.warning(f"[TeamRecommend] Failed to save chat history: {e}")

                        yield {
                            'type': 'complete',
                            'message': 'Recommendation completed'
                        }
                        break

                    elif message.get('_type') == 'error':
                        yield {
                            'type': 'error',
                            'message': message.get('error', 'Unknown error')
                        }
                        break

                    else:
                        # Progress update from agents
                        yield message

                except asyncio.TimeoutError:
                    continue

        finally:
            # Ensure background task completes
            if not background_task.done():
                await background_task

    async def recommend(
        self,
        query: str,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous recommendation (non-streaming)

        Args:
            query: User query
            session_id: Session ID
            chat_history: Previous conversation

        Returns:
            Recommendation result
        """
        try:
            team_manager = get_team_manager()

            result = await team_manager.run(
                query=query,
                chat_history=chat_history or [],
                progress_callback=None
            )

            return result

        except Exception as e:
            logger.error(f"[TeamRecommend] Recommendation failed: {e}")
            return {
                'success': False,
                'answer': f'Failed to generate recommendation: {str(e)}',
                'sources': [],
                'metadata': {},
                'agent_logs': []
            }


# Singleton instance
_service_instance = None


def get_team_recommend_service() -> TeamRecommendService:
    """Get team recommendation service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = TeamRecommendService()
    return _service_instance
