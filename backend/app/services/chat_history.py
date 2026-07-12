"""
Chat History Service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.core.redis_client import get_redis_client


class ChatHistoryService:
    """Manage chat history using Redis"""

    def __init__(self):
        """Initialize chat history service"""
        self.redis_client = get_redis_client()
        self.ttl = 86400 * 7  # 7 days

    def get_history_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"chat:history:{session_id}"

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add message to chat history"""
        try:
            key = self.get_history_key(session_id)

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            # Append to list
            import json
            self.redis_client.client.rpush(key, json.dumps(message))
            self.redis_client.client.expire(key, self.ttl)

            logger.info(f"Added message to session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get chat history for session"""
        try:
            key = self.get_history_key(session_id)

            messages = self.redis_client.client.lrange(key, 0, -1)

            import json
            history = [json.loads(msg) for msg in messages]

            if limit:
                history = history[-limit:]

            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def clear_history(self, session_id: str) -> bool:
        """Clear chat history for session"""
        try:
            key = self.get_history_key(session_id)
            self.redis_client.client.delete(key)

            logger.info(f"Cleared history for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False

    async def get_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> str:
        """Get formatted context from recent history"""
        history = await self.get_history(session_id, limit=max_messages)

        context_parts = []
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)


_chat_history_service = None


def get_chat_history_service() -> ChatHistoryService:
    """Get singleton chat history service instance"""
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service
