"""
AI Recommendation Service - Integrates LangGraph + SSE streaming + Redis caching
"""
from typing import AsyncGenerator, Optional
from loguru import logger
import json

from .state import AIRecommendState
from .graph_builder import get_ai_recommend_workflow


class AIRecommendService:
    """AI Recommendation Service with streaming support"""

    def __init__(self):
        self.workflow = get_ai_recommend_workflow()

    async def process_stream(
        self,
        user_query: str,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Process user query and stream results via SSE

        Args:
            user_query: User query text
            session_id: Session ID for caching

        Yields:
            SSE formatted messages
        """
        logger.info(f"[AIRecommend] Processing query: {user_query[:50]}...")

        try:
            initial_state: AIRecommendState = {
                "query": user_query,
                "session_id": session_id,
                "rewritten_query": "",
                "entities": [],
                "milvus_results": [],
                "neo4j_results": [],
                "rrf_results": [],
                "confidence_score": 0.0,
                "needs_web_search": False,
                "tavily_results": [],
                "reranked_results": [],
                "final_answer": ""
            }

            async for event in self.workflow.astream(initial_state):
                for node_name, node_state in event.items():
                    progress_msg = self._get_progress_message(node_name, node_state)
                    if progress_msg:
                        yield self._format_sse(progress_msg)

                    node_data = self._get_node_data(node_name, node_state)
                    if node_data:
                        yield self._format_sse(node_data)

            logger.success(f"[AIRecommend] Completed processing for query: {user_query[:50]}")

        except Exception as e:
            logger.error(f"[AIRecommend] Processing failed: {e}")
            yield self._format_sse({
                "type": "error",
                "message": str(e)
            })

    def _format_sse(self, data: dict) -> str:
        """Format message as SSE"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _get_progress_message(self, node_name: str, state: AIRecommendState) -> Optional[dict]:
        """Get progress message for a node"""
        if node_name == "query_rewriter":
            rewritten = state.get("rewritten_query", "")
            if rewritten:
                return {
                    "type": "progress",
                    "node": node_name,
                    "message": f"Query rewritten: {rewritten}"
                }

        elif node_name == "parallel_retrieval":
            milvus_count = len(state.get("milvus_results", []))
            neo4j_count = len(state.get("neo4j_results", []))
            return {
                "type": "progress",
                "node": node_name,
                "message": f"Retrieved: Milvus {milvus_count} results + Neo4j {neo4j_count} results"
            }

        elif node_name == "rrf_fusion":
            rrf_count = len(state.get("rrf_results", []))
            return {
                "type": "progress",
                "node": node_name,
                "message": f"RRF fusion: {rrf_count} results"
            }

        elif node_name == "confidence_check":
            score = state.get("confidence_score", 0)
            needs_search = state.get("needs_web_search", False)
            return {
                "type": "progress",
                "node": node_name,
                "message": f"Confidence: {score:.2f} {'(web search needed)' if needs_search else '(sufficient)'}"
            }

        elif node_name == "tavily_search":
            tavily_results = state.get("tavily_results")
            if tavily_results:
                return {
                    "type": "progress",
                    "node": node_name,
                    "message": f"Web search: {len(tavily_results)} results"
                }

        elif node_name == "rerank":
            reranked_count = len(state.get("reranked_results", []))
            return {
                "type": "progress",
                "node": node_name,
                "message": f"Reranked: {reranked_count} results"
            }

        return None

    def _get_node_data(self, node_name: str, state: AIRecommendState) -> Optional[dict]:
        """Get data to send for a node"""
        if node_name == "synthesizer":
            return {
                "type": "complete",
                "answer": state.get("final_answer", ""),
                "sources": state.get("reranked_results", [])[:3]
            }
        return None


_service_instance = None


def get_ai_recommend_service() -> AIRecommendService:
    """Get service singleton"""
    global _service_instance

    if _service_instance is None:
        _service_instance = AIRecommendService()

    return _service_instance
