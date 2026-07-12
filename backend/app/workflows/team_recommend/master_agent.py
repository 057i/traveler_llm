"""
Master Agent - Coordinates subagents for comprehensive travel recommendations
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from dashscope import Generation
from config.settings import settings
import asyncio

from .subagents.rag_assistant import RAGAssistant
from .subagents.graph_rag_assistant import GraphRAGAssistant
from .subagents.itinerary_planner import ItineraryPlanner
from .subagents.budget_expert import BudgetExpert
from .subagents.transport_assistant import TransportAssistant
from .subagents.food_assistant import FoodAssistant


class MasterAgent:
    """Master agent that coordinates multiple specialized subagents"""

    def __init__(self):
        """Initialize master agent and all subagents"""
        self.llm = settings.QWEN_MODEL

        # Initialize subagents
        self.rag_assistant = RAGAssistant()
        self.graph_rag_assistant = GraphRAGAssistant()
        self.itinerary_planner = ItineraryPlanner()
        self.budget_expert = BudgetExpert()
        self.transport_assistant = TransportAssistant()
        self.food_assistant = FoodAssistant()

        logger.success("Master Agent initialized with 6 subagents")

    async def coordinate(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Coordinate all subagents to generate comprehensive recommendation

        Args:
            query: User query
            chat_history: Previous conversation
            progress_callback: Function to report progress

        Returns:
            Complete recommendation result
        """
        logger.info(f"Master Agent coordinating for: {query[:50]}...")

        agent_logs = []

        try:
            # Step 1: RAG Assistant - Retrieve knowledge base
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'RAG Knowledge Assistant',
                    'status': 'working',
                    'message': 'Searching knowledge base...',
                    'progress': 10
                })

            rag_results = await self._run_rag_assistant(query)
            agent_logs.append({
                'agent': 'RAG Knowledge Assistant',
                'status': 'completed',
                'summary': f'Retrieved {len(rag_results)} results from vector database',
                'result_count': len(rag_results)
            })

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'RAG Knowledge Assistant',
                    'status': 'completed',
                    'message': f'Found {len(rag_results)} relevant results',
                    'progress': 20
                })

            # Step 2: Graph RAG Assistant - Retrieve related destinations
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Graph RAG Assistant',
                    'status': 'working',
                    'message': 'Analyzing knowledge graph...',
                    'progress': 30
                })

            graph_results = await self._run_graph_rag_assistant(query, rag_results)
            agent_logs.append({
                'agent': 'Graph RAG Assistant',
                'status': 'completed',
                'summary': f'Found {len(graph_results)} related destinations',
                'result_count': len(graph_results)
            })

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Graph RAG Assistant',
                    'status': 'completed',
                    'message': f'Found {len(graph_results)} related locations',
                    'progress': 40
                })

            # Step 3: Parallel execution of specialized agents
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Specialized Team',
                    'status': 'working',
                    'message': 'Itinerary, Transport, and Food experts working in parallel...',
                    'progress': 50
                })

            itinerary_task = self._run_itinerary_planner(query, rag_results)
            transport_task = self._run_transport_assistant(query, rag_results)
            food_task = self._run_food_assistant(query, rag_results)

            itinerary, transport, food = await asyncio.gather(
                itinerary_task,
                transport_task,
                food_task
            )

            agent_logs.extend([
                {'agent': 'Itinerary Planner', 'status': 'completed', 'summary': 'Travel plan generated'},
                {'agent': 'Transport Assistant', 'status': 'completed', 'summary': 'Transport options provided'},
                {'agent': 'Food Assistant', 'status': 'completed', 'summary': 'Food recommendations ready'}
            ])

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Specialized Team',
                    'status': 'completed',
                    'message': 'All specialized agents completed',
                    'progress': 70
                })

            # Step 4: Budget Expert
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Budget Expert',
                    'status': 'working',
                    'message': 'Calculating budget estimates...',
                    'progress': 80
                })

            budget = await self._run_budget_expert(query, itinerary, transport, food)
            agent_logs.append({
                'agent': 'Budget Expert',
                'status': 'completed',
                'summary': 'Budget analysis completed'
            })

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Budget Expert',
                    'status': 'completed',
                    'message': 'Budget calculated',
                    'progress': 90
                })

            # Step 5: Master synthesis
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'Master Agent',
                    'status': 'working',
                    'message': 'Synthesizing final recommendation...',
                    'progress': 95
                })

            final_answer = await self._synthesize_final_answer(
                query, itinerary, transport, food, budget, rag_results
            )

            # Prepare sources
            sources = []
            for result in rag_results[:5]:
                sources.append({
                    'name': result.get('name', 'Unknown'),
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'score': result.get('score', 0.5),
                    'tags': result.get('tags', [])
                })

            logger.success("Master Agent coordination completed")

            return {
                'success': True,
                'answer': final_answer,
                'sources': sources,
                'metadata': {
                    'workflow': 'team_recommend',
                    'agents_used': len(agent_logs)
                },
                'agent_logs': agent_logs
            }

        except Exception as e:
            logger.error(f"Master Agent coordination failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'answer': f'Failed to generate recommendation: {str(e)}',
                'sources': [],
                'metadata': {},
                'agent_logs': agent_logs
            }

    async def _run_rag_assistant(self, query: str) -> List[Dict[str, Any]]:
        """Execute RAG assistant"""
        try:
            result = await self.rag_assistant.execute(query, {})
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"RAG Assistant failed: {e}")
            return []

    async def _run_graph_rag_assistant(
        self,
        query: str,
        rag_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute Graph RAG assistant"""
        try:
            context = {'rag_results': rag_results}
            result = await self.graph_rag_assistant.execute(query, context)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Graph RAG Assistant failed: {e}")
            return []

    async def _run_itinerary_planner(
        self,
        query: str,
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """Execute itinerary planner"""
        try:
            context = {'destinations': rag_results[:5]}
            return await self.itinerary_planner.execute(query, context)
        except Exception as e:
            logger.error(f"Itinerary Planner failed: {e}")
            return "Unable to generate itinerary."

    async def _run_transport_assistant(
        self,
        query: str,
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """Execute transport assistant"""
        try:
            context = {'destinations': rag_results[:5]}
            return await self.transport_assistant.execute(query, context)
        except Exception as e:
            logger.error(f"Transport Assistant failed: {e}")
            return "Unable to provide transport options."

    async def _run_food_assistant(
        self,
        query: str,
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """Execute food assistant"""
        try:
            context = {'destinations': rag_results[:5]}
            return await self.food_assistant.execute(query, context)
        except Exception as e:
            logger.error(f"Food Assistant failed: {e}")
            return "Unable to provide food recommendations."

    async def _run_budget_expert(
        self,
        query: str,
        itinerary: str,
        transport: str,
        food: str
    ) -> str:
        """Execute budget expert"""
        try:
            context = {
                'itinerary': itinerary,
                'transport': transport,
                'food': food
            }
            return await self.budget_expert.execute(query, context)
        except Exception as e:
            logger.error(f"Budget Expert failed: {e}")
            return "Unable to estimate budget."

    async def _synthesize_final_answer(
        self,
        query: str,
        itinerary: str,
        transport: str,
        food: str,
        budget: str,
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """Synthesize final comprehensive answer"""
        try:
            prompt = f"""As a professional travel consultant, synthesize a comprehensive travel recommendation.

User Query: {query}

Available Information:
1. Itinerary Plan:
{itinerary[:800]}

2. Transport Options:
{transport[:600]}

3. Food Recommendations:
{food[:600]}

4. Budget Estimate:
{budget[:400]}

5. Knowledge Base Results ({len(rag_results)} destinations)

Generate a well-structured, comprehensive travel recommendation in Chinese that includes:
1. Overview and highlights
2. Detailed itinerary
3. Transport recommendations
4. Food suggestions
5. Budget summary
6. Practical tips

Format the response with clear sections and bullet points."""

            response = Generation.call(
                model=self.llm,
                prompt=prompt,
                api_key=settings.DASHSCOPE_API_KEY
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                return self._fallback_answer(itinerary, transport, food, budget)

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._fallback_answer(itinerary, transport, food, budget)

    def _fallback_answer(
        self,
        itinerary: str,
        transport: str,
        food: str,
        budget: str
    ) -> str:
        """Fallback answer when synthesis fails"""
        return f"""# Travel Recommendation

## Itinerary
{itinerary}

## Transport
{transport}

## Food
{food}

## Budget
{budget}
"""
