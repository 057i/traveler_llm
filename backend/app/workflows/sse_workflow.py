"""
SSE Recommendation Workflow
Real-time streaming recommendation using Server-Sent Events
"""
from typing import AsyncGenerator, Dict, Any
from loguru import logger
import json


class SSEWorkflow:
    """SSE streaming workflow"""

    async def process_stream(self, query: str) -> AsyncGenerator[str, None]:
        """
        Process query and stream results via SSE

        Args:
            query: User query string

        Yields:
            SSE formatted messages
        """
        logger.info(f"[SSE] Starting stream for query: {query[:50]}...")

        try:
            # Step 1: Intent recognition
            yield self._format_sse("intent", {"message": "Recognizing intent...", "progress": 20})

            from app.services.qwen_service import get_qwen_service
            qwen = get_qwen_service()

            intent_prompt = f"""Analyze this travel query and identify the intent.
Query: {query}

Respond with JSON: {{"intent": "attraction/route/food/hotel/other", "entities": []}}
"""
            intent_response = await qwen.chat(intent_prompt)

            try:
                intent_data = json.loads(intent_response)
                intent = intent_data.get("intent", "other")
            except:
                intent = "other"

            yield self._format_sse("intent", {"intent": intent, "progress": 40})

            # Step 2: Vector retrieval
            yield self._format_sse("retrieval", {"message": "Searching vector database...", "progress": 50})

            from app.core.chroma_client import get_chroma_client
            chroma = get_chroma_client()

            search_results = chroma.search(query_text=query, n_results=10)

            vector_results = []
            if search_results and 'documents' in search_results:
                for i, doc in enumerate(search_results['documents'][0][:5]):
                    vector_results.append({
                        'content': doc,
                        'rank': i + 1,
                        'source': 'vector'
                    })

            yield self._format_sse("retrieval", {
                "results_count": len(vector_results),
                "progress": 70
            })

            # Step 3: Generate answer
            yield self._format_sse("generation", {"message": "Generating answer...", "progress": 80})

            context = "\n\n".join([r['content'][:300] for r in vector_results[:3]])

            answer_prompt = f"""Based on the following context, answer the user's question.

Question: {query}

Context:
{context}

Provide a helpful answer in Chinese.
"""

            answer = await qwen.chat(answer_prompt)

            yield self._format_sse("generation", {"answer": answer, "progress": 95})

            # Step 4: Complete
            yield self._format_sse("complete", {
                "message": "Processing complete",
                "answer": answer,
                "sources": [r['content'][:100] for r in vector_results[:3]],
                "progress": 100
            })

            logger.success(f"[SSE] Stream completed for query: {query[:50]}")

        except Exception as e:
            logger.error(f"[SSE] Stream error: {e}")
            yield self._format_sse("error", {"message": str(e)})

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format message as SSE"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


# Singleton instance
_workflow_instance = None


def get_sse_workflow() -> SSEWorkflow:
    """Get workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = SSEWorkflow()
    return _workflow_instance
