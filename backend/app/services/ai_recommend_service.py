"""
AI Recommendation Service - Integrates LangGraph + SSE streaming + Redis caching
"""
from typing import AsyncGenerator, Optional
from loguru import logger
import json
import time
import asyncio

from app.workflows.ai_recommend.state import AIRecommendState
from app.workflows.ai_recommend.graph_builder import get_ai_recommend_workflow
from app.core.redis_client import get_redis_client


# 防止重复处理同一个session
_processing_sessions = set()


class AIRecommendService:
    """
    AI推荐服务 - 基于LangGraph工作流

    功能：
    - 查询改写和扩展
    - 多路RAG检索（Milvus混合检索 + Neo4j图谱检索）
    - 置信度评估（决定是否触发网络搜索）
    - Tavily网络搜索（补充最新信息）
    - RRF结果融合
    - 重排序（BGE Reranker）
    - LLM综合生成答案
    - SSE流式推送进度

    工作流节点：
    1. query_rewriter: 查询改写
    2. milvus_hybrid: Milvus混合检索
    3. neo4j_nearby: Neo4j附近景点检索
    4. confidence_check: 置信度评估
    5. tavily_search: 网络搜索（条件触发）
    6. rrf_fusion: RRF融合
    7. rerank: 重排序
    8. synthesizer: 生成答案

    使用场景：
    - 旅游目的地推荐
    - 攻略问答
    - 智能客服
    """

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
                "expanded_query": "",
                "entities": [],
                "needs_nearby_search": False,
                "is_travel_related": True,
                "should_skip_retrieval": False,
                "milvus_hybrid_results": [],
                "milvus_confidence": 0.0,
                "neo4j_results": [],
                "confidence_score": 0.0,
                "needs_web_search": False,
                "tavily_results": [],
                "rrf_results": [],
                "reranked_results": [],
                "final_answer": "",
                "sources": []
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

    async def process_query_async(self, query: str, session_id: str):
        """
        异步处理查询，工作流节点通过SSE发送事件到Redis Pub/Sub

        Args:
            query: 用户查询
            session_id: 会话ID
        """
        # 防止重复处理
        if session_id in _processing_sessions:
            logger.warning(f"[AIRecommend] Session {session_id} is already processing, ignoring duplicate request")
            return

        _processing_sessions.add(session_id)

        # ========== 从Redis读取task_id（由API端点生成） ==========
        redis_client = get_redis_client()
        task_key = f"ai:recommend:current_task:{session_id}"
        task_id = redis_client.get(task_key)
        if task_id:
            task_id = task_id.decode('utf-8') if isinstance(task_id, bytes) else task_id
        else:
            # 降级：如果没有找到，生成一个新的
            task_id = f"task_{int(time.time() * 1000)}_{session_id.split('_')[-1]}"
            redis_client.set(task_key, task_id, ex=300)

        logger.info(f"[AIRecommend] Starting async workflow for session: {session_id}, task: {task_id}")
        # ===========================================================

        try:
            # 构建初始state
            initial_state: AIRecommendState = {
                "query": query,
                "session_id": session_id,
                "rewritten_query": "",
                "expanded_query": "",
                "entities": [],
                "needs_nearby_search": False,
                "is_travel_related": True,
                "should_skip_retrieval": False,
                "milvus_hybrid_results": [],
                "milvus_confidence": 0.0,
                "neo4j_results": [],
                "confidence_score": 0.0,
                "needs_web_search": False,
                "tavily_results": [],
                "rrf_results": [],
                "reranked_results": [],
                "final_answer": "",
                "sources": []
            }

            # 执行工作流（各节点内部会发送SSE事件）
            result = await self.workflow.ainvoke(initial_state)

            # 调试日志 - 检查workflow返回值
            logger.info("=" * 80)
            logger.info("[DEBUG] Workflow result:")
            logger.info(f"  result type: {type(result)}")
            logger.info(f"  result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            logger.info(f"  'final_answer' in result: {'final_answer' in result if isinstance(result, dict) else False}")
            logger.info(f"  result.get('final_answer'): {repr(result.get('final_answer', 'KEY_NOT_FOUND'))}")
            logger.info("=" * 80)

            # 获取最终答案和来源
            final_answer = result.get('final_answer', '')
            sources = result.get('sources', [])
            nearby_recommendations = result.get('nearby_recommendations', [])  # 新增：附近推荐

            logger.info(f"[AIRecommend] Final answer length: {len(final_answer)} chars")
            logger.info(f"[AIRecommend] Sources count: {len(sources)}")
            logger.info(f"[AIRecommend] Nearby recommendations count: {len(nearby_recommendations)}")

            # 保存到历史记录
            history_key = f"ai_recommend:history:{session_id}"
            history_item = {
                "query": query,  # ← 使用正确的变量名
                "answer": final_answer,
                "sources": sources,
                "nearby_recommendations": nearby_recommendations,  # 保存附近推荐
                "timestamp": time.time()
            }
            redis_client = get_redis_client()
            redis_client.rpush(history_key, json.dumps(history_item, ensure_ascii=False))
            redis_client.expire(history_key, 86400 * 7)  # 7天过期

            logger.info(f"[AIRecommend] History saved to: {history_key}")

            # 发送result事件（包含answer、sources、nearby_recommendations和task_id）
            events_key = f"ai:recommend:events:{session_id}"
            result_event = {
                "event_type": "result",  # 使用event_type而不是type
                "answer": final_answer,
                "sources": sources,
                "nearby_recommendations": nearby_recommendations,  # 新增：附近推荐
                "task_id": task_id,  # 新增：task_id
                "timestamp": time.time()
            }

            logger.info(f"[AIRecommend] Sending result event with answer ({len(final_answer)} chars) and task_id: {task_id}")
            redis_client.rpush(events_key, json.dumps(result_event, ensure_ascii=False))
            redis_client.expire(events_key, 3600)
            redis_client.publish(events_key, json.dumps(result_event, ensure_ascii=False))
            logger.success(f"[AIRecommend] Result event sent")

            await asyncio.sleep(0.1)

            # 发送完成事件（不包含answer，只表示流程结束）
            from app.utils.sse_utils import send_complete_event
            await send_complete_event(
                task_id=session_id,
                flow_type="ai_recommend",
                message=f"AI推荐完成"
            )

            logger.success(f"[AIRecommend] Workflow completed for session: {session_id}")

        except Exception as e:
            logger.error(f"[AIRecommend] Workflow failed: {e}")
            import traceback
            traceback.print_exc()

            # 发送错误事件
            from app.utils.sse_utils import send_error_event
            await send_error_event(
                task_id=session_id,
                flow_type="ai_recommend",
                error_message=str(e)
            )

        finally:
            # 清理session标记
            _processing_sessions.discard(session_id)
            logger.info(f"[AIRecommend] Cleaned up session: {session_id}")

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

        elif node_name == "milvus_hybrid":
            hybrid_count = len(node_state.get("milvus_hybrid_results", []))
            confidence = node_state.get("milvus_confidence", 0)
            return {
                "type": "progress",
                "node": node_name,
                "message": f"混合检索完成: {hybrid_count}条结果, 置信度{confidence:.2f}"
            }

        elif node_name == "neo4j_nearby":
            neo4j_count = len(node_state.get("neo4j_results", []))
            if neo4j_count > 0:
                return {
                    "type": "progress",
                    "node": node_name,
                    "message": f"附近检索完成: {neo4j_count}条结果"
                }
            return None

        elif node_name == "rrf_fusion":
            rrf_count = len(node_state.get("rrf_results", []))
            return {
                "type": "progress",
                "node": node_name,
                "message": f"RRF融合完成: {rrf_count}条结果（已归一化）"
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
