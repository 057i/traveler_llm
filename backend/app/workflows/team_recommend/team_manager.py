"""
Team Manager - Coordinates multiple AI agents for travel recommendations
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio

from .master_agent import MasterAgent


class TeamManager:
    """Manages the team of AI agents"""

    def __init__(self):
        """Initialize team manager"""
        logger.info("=" * 80)
        logger.info("Initializing Team Manager")
        logger.info("=" * 80)

        self.master_agent = MasterAgent()
        logger.success("Team Manager initialized successfully")

    async def run(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Execute team recommendation workflow

        Args:
            query: User query
            chat_history: Previous conversation history
            progress_callback: Callback function for progress updates

        Returns:
            Recommendation result with answer, sources, and agent logs
        """
        logger.info("=" * 80)
        logger.info(f"Team Manager starting: {query[:50]}...")
        logger.info("=" * 80)

        try:
            # Send start notification
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Team Manager',
                    'status': 'started',
                    'message': 'AI Team is analyzing your request',
                    'progress': 0
                })

            # Execute coordination through master agent
            result = await self.master_agent.coordinate(
                query=query,
                chat_history=chat_history or [],
                progress_callback=progress_callback
            )

            logger.info("=" * 80)
            logger.success("Team Manager completed successfully")
            logger.info("=" * 80)

            # Send completion notification
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Team Manager',
                    'status': 'completed',
                    'message': 'Team recommendation completed',
                    'progress': 100
                })

            return result

        except Exception as e:
            logger.error(f"Team Manager execution failed: {e}")
            import traceback
            traceback.print_exc()

            # Send error notification
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Team Manager',
                    'status': 'error',
                    'message': f'Team execution failed: {str(e)}',
                    'progress': 0
                })

            return {
                'success': False,
                'answer': f'Failed to generate recommendation: {str(e)}',
                'sources': [],
                'metadata': {},
                'agent_logs': []
            }


# Singleton instance
_team_manager_instance = None


def get_team_manager() -> TeamManager:
    """Get team manager singleton"""
    global _team_manager_instance
    if _team_manager_instance is None:
        _team_manager_instance = TeamManager()
    return _team_manager_instance
