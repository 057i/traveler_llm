"""
Chat Recommendation Workflow - LangGraph Implementation
User Query -> Intent Recognition -> Retrieval -> RRF Fusion -> Answer Generation
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from loguru import logger
import json


class ChatState(TypedDict):
    """Chat workflow state"""
    query: str
    user_id: str
    session_id: str

    # Intent recognition
    intent: str  # attraction, route, food, hotel, weather, other
    entities: List[str]

    # Retrieval results
    vector_results: List[Dict[str, Any]]
    graph_results: List[Dict[str, Any]]

    # RRF fusion
    fused_results: List[Dict[str, Any]]

    # Answer generation
    answer: str
    sources: List[str]

    # Metadata
    processing_time: float
    error: str | None


class ChatWorkflow:
    """Chat recommendation workflow using LangGraph"""

    def __init__(self):
        """Initialize workflow"""
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(ChatState)

        # Add nodes
        workflow.add_node("recognize_intent", self.recognize_intent)
        workflow.add_node("retrieve_vector", self.retrieve_from_vector)
        workflow.add_node("retrieve_graph", self.retrieve_from_graph)
        workflow.add_node("fuse_results", self.fuse_with_rrf)
        workflow.add_node("generate_answer", self.generate_answer)

        # Set entry point
        workflow.set_entry_point("recognize_intent")

        # Build workflow chain
        workflow.add_edge("recognize_intent", "retrieve_vector")
        workflow.add_edge("retrieve_vector", "retrieve_graph")
        workflow.add_edge("retrieve_graph", "fuse_results")
        workflow.add_edge("fuse_results", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    async def recognize_intent(self, state: ChatState) -> ChatState:
        """Step 1: Recognize user intent using Qwen"""
        logger.info(f"[Intent] Analyzing query: {state['query'][:50]}...")

        try:
            from app.services.qwen_service import get_qwen_service

            qwen = get_qwen_service()

            # Use Qwen to recognize intent
            intent_prompt = f"""Analyze the following travel query and identify the intent.
Possible intents: attraction, route, food, hotel, weather, other

Query: {state['query']}

Respond with JSON format:
{{"intent": "attraction", "entities": ["Beijing", "Great Wall"]}}
"""

            response = await qwen.chat(intent_prompt)

            # Parse response
            try:
                result = json.loads(response)
                state["intent"] = result.get("intent", "other")
                state["entities"] = result.get("entities", [])
            except:
                # Fallback to simple keyword matching
                query_lower = state['query'].lower()
                if any(k in query_lower for k in ['attraction', 'scenic', 'tourist']):
                    state["intent"] = "attraction"
                elif any(k in query_lower for k in ['route', 'itinerary']):
                    state["intent"] = "route"
                elif any(k in query_lower for k in ['food', 'restaurant']):
                    state["intent"] = "food"
                elif any(k in query_lower for k in ['hotel', 'accommodation']):
                    state["intent"] = "hotel"
                else:
                    state["intent"] = "other"
                state["entities"] = []

            logger.success(f"[Intent] Recognized: {state['intent']}, Entities: {state['entities']}")

        except Exception as e:
            logger.error(f"[Intent] Recognition failed: {e}")
            state["intent"] = "other"
            state["entities"] = []

        return state

    async def retrieve_from_vector(self, state: ChatState) -> ChatState:
        """Step 2: Retrieve from vector database (ChromaDB)"""
        logger.info("[Vector] Retrieving from ChromaDB...")

        try:
            from app.core.chroma_client import get_chroma_client

            chroma = get_chroma_client()

            # Search vector database
            results = chroma.search(
                query_text=state['query'],
                n_results=10
            )

            # Format results
            vector_results = []
            if results and 'documents' in results:
                for i, doc in enumerate(results['documents'][0]):
                    vector_results.append({
                        'content': doc,
                        'score': 1.0 / (i + 1),  # Simple relevance score
                        'source': 'vector',
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results else {}
                    })

            state["vector_results"] = vector_results
            logger.success(f"[Vector] Retrieved {len(vector_results)} results")

        except Exception as e:
            logger.error(f"[Vector] Retrieval failed: {e}")
            state["vector_results"] = []

        return state

    async def retrieve_from_graph(self, state: ChatState) -> ChatState:
        """Step 3: Retrieve from knowledge graph (Neo4j)"""
        logger.info("[Graph] Retrieving from Neo4j...")

        try:
            # TODO: Implement Neo4j retrieval
            # from app.core.neo4j_client import get_neo4j_client
            # neo4j = get_neo4j_client()
            # graph_results = neo4j.search(state['query'], state['entities'])

            state["graph_results"] = []
            logger.warning("[Graph] Neo4j not configured, skipping")

        except Exception as e:
            logger.error(f"[Graph] Retrieval failed: {e}")
            state["graph_results"] = []

        return state

    async def fuse_with_rrf(self, state: ChatState) -> ChatState:
        """Step 4: Fuse results using Reciprocal Rank Fusion (RRF)"""
        logger.info("[RRF] Fusing results...")

        try:
            vector_results = state.get("vector_results", [])
            graph_results = state.get("graph_results", [])

            # RRF algorithm
            k = 60  # RRF constant
            scores = {}

            # Score vector results
            for rank, result in enumerate(vector_results, start=1):
                content = result['content']
                rrf_score = 1.0 / (k + rank)
                if content in scores:
                    scores[content]['score'] += rrf_score
                else:
                    scores[content] = {
                        'content': content,
                        'score': rrf_score,
                        'sources': ['vector'],
                        'metadata': result.get('metadata', {})
                    }

            # Score graph results
            for rank, result in enumerate(graph_results, start=1):
                content = result['content']
                rrf_score = 1.0 / (k + rank)
                if content in scores:
                    scores[content]['score'] += rrf_score
                    scores[content]['sources'].append('graph')
                else:
                    scores[content] = {
                        'content': content,
                        'score': rrf_score,
                        'sources': ['graph'],
                        'metadata': result.get('metadata', {})
                    }

            # Sort by RRF score
            fused_results = sorted(scores.values(), key=lambda x: x['score'], reverse=True)

            state["fused_results"] = fused_results[:5]  # Top 5
            logger.success(f"[RRF] Fused {len(fused_results)} results")

        except Exception as e:
            logger.error(f"[RRF] Fusion failed: {e}")
            state["fused_results"] = state.get("vector_results", [])[:5]

        return state

    async def generate_answer(self, state: ChatState) -> ChatState:
        """Step 5: Generate answer using Qwen"""
        logger.info("[Answer] Generating answer with Qwen...")

        try:
            from app.services.qwen_service import get_qwen_service

            qwen = get_qwen_service()
            fused_results = state.get("fused_results", [])

            # Build context from fused results
            context = "\n\n".join([
                f"[Source {i+1}] {r['content'][:500]}"
                for i, r in enumerate(fused_results[:3])
            ])

            # Generate answer prompt
            answer_prompt = f"""Based on the following travel information, answer the user's question.

User Question: {state['query']}

Context:
{context}

Please provide a helpful and accurate answer in Chinese. If the context doesn't contain relevant information, say so.
"""

            answer = await qwen.chat(answer_prompt)

            state["answer"] = answer
            state["sources"] = [r['content'][:100] for r in fused_results[:3]]

            logger.success(f"[Answer] Generated answer: {len(answer)} chars")

        except Exception as e:
            logger.error(f"[Answer] Generation failed: {e}")
            state["answer"] = "Sorry, I cannot generate an answer."
            state["sources"] = []

        return state

    async def run(self, query: str, user_id: str = "default", session_id: str = "default") -> Dict[str, Any]:
        """Run the workflow"""
        import time

        start_time = time.time()
        logger.info(f"[Workflow] Starting chat workflow for query: {query[:50]}...")

        # Initialize state
        initial_state = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "intent": "",
            "entities": [],
            "vector_results": [],
            "graph_results": [],
            "fused_results": [],
            "answer": "",
            "sources": [],
            "processing_time": 0.0,
            "error": None
        }

        # Run workflow
        result = await self.graph.ainvoke(initial_state)

        # Calculate processing time
        result["processing_time"] = time.time() - start_time

        logger.success(f"[Workflow] Completed in {result['processing_time']:.2f}s")

        return result


# Singleton instance
_workflow_instance = None


def get_chat_workflow() -> ChatWorkflow:
    """Get workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ChatWorkflow()
    return _workflow_instance
