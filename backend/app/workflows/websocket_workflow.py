"""
WebSocket Workflow
Real-time bidirectional communication for recommendations
"""
from typing import Dict, Any
from loguru import logger
import json


class WebSocketWorkflow:
    """WebSocket workflow for real-time recommendations"""

    async def process_message(self, websocket, message: Dict[str, Any]) -> None:
        """
        Process incoming WebSocket message and stream response

        Args:
            websocket: WebSocket connection
            message: Incoming message dictionary
        """
        msg_type = message.get("type", "")
        query = message.get("query", "")

        logger.info(f"[WebSocket] Processing message type: {msg_type}")

        try:
            if msg_type == "recommendation":
                await self._handle_recommendation(websocket, query)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

        except Exception as e:
            logger.error(f"[WebSocket] Error processing message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })

    async def _handle_recommendation(self, websocket, query: str) -> None:
        """
        Handle recommendation request with streaming updates

        Args:
            websocket: WebSocket connection
            query: User query
        """
        logger.info(f"[WebSocket] Recommendation query: {query[:50]}...")

        # Step 1: Intent recognition
        await websocket.send_json({
            "type": "progress",
            "step": "intent",
            "message": "Recognizing intent...",
            "progress": 20
        })

        try:
            from app.services.qwen_service import get_qwen_service
            qwen = get_qwen_service()

            intent_prompt = f"""Analyze this travel query and identify the intent.
Query: {query}

Respond with JSON: {{"intent": "attraction/route/food/hotel/other"}}
"""
            intent_response = await qwen.chat(intent_prompt)

            try:
                intent_data = json.loads(intent_response)
                intent = intent_data.get("intent", "other")
            except:
                intent = "other"

            await websocket.send_json({
                "type": "progress",
                "step": "intent",
                "intent": intent,
                "progress": 40
            })

        except Exception as e:
            logger.error(f"[WebSocket] Intent recognition failed: {e}")
            intent = "other"

        # Step 2: Vector retrieval
        await websocket.send_json({
            "type": "progress",
            "step": "retrieval",
            "message": "Searching database...",
            "progress": 50
        })

        try:
            from app.core.chroma_client import get_chroma_client
            chroma = get_chroma_client()

            search_results = chroma.search(query_text=query, n_results=10)

            vector_results = []
            if search_results and 'documents' in search_results:
                for i, doc in enumerate(search_results['documents'][0][:5]):
                    result = {
                        'content': doc,
                        'rank': i + 1,
                        'score': 1.0 / (i + 1)
                    }
                    vector_results.append(result)

                    # Send each result as it's processed
                    await websocket.send_json({
                        "type": "result",
                        "data": result,
                        "progress": 50 + (i + 1) * 4
                    })

            await websocket.send_json({
                "type": "progress",
                "step": "retrieval",
                "results_count": len(vector_results),
                "progress": 70
            })

        except Exception as e:
            logger.error(f"[WebSocket] Retrieval failed: {e}")
            vector_results = []

        # Step 3: Generate answer
        await websocket.send_json({
            "type": "progress",
            "step": "generation",
            "message": "Generating answer...",
            "progress": 80
        })

        try:
            context = "\n\n".join([r['content'][:300] for r in vector_results[:3]])

            answer_prompt = f"""Based on the following context, answer the user's question.

Question: {query}

Context:
{context}

Provide a helpful answer in Chinese.
"""

            answer = await qwen.chat(answer_prompt)

            await websocket.send_json({
                "type": "progress",
                "step": "generation",
                "progress": 95
            })

        except Exception as e:
            logger.error(f"[WebSocket] Answer generation failed: {e}")
            answer = "Sorry, failed to generate answer. Please try again later."

        # Step 4: Send final result
        await websocket.send_json({
            "type": "complete",
            "answer": answer,
            "sources": [r['content'][:100] for r in vector_results[:3]],
            "intent": intent,
            "results_count": len(vector_results),
            "progress": 100
        })

        logger.success(f"[WebSocket] Completed recommendation for: {query[:50]}")

    async def handle_connection(self, websocket) -> None:
        """
        Handle WebSocket connection lifecycle

        Args:
            websocket: WebSocket connection
        """
        logger.info("[WebSocket] New connection established")

        try:
            # Send welcome message
            await websocket.send_json({
                "type": "connected",
                "message": "Connected to recommendation service"
            })

            # Listen for messages
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                await self.process_message(websocket, message)

        except Exception as e:
            logger.error(f"[WebSocket] Connection error: {e}")
        finally:
            logger.info("[WebSocket] Connection closed")


# Singleton instance
_workflow_instance = None


def get_websocket_workflow() -> WebSocketWorkflow:
    """Get workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = WebSocketWorkflow()
    return _workflow_instance
