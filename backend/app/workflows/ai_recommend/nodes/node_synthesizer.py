"""
AI Recommendation Workflow - Node: Synthesizer

Generate final answer using LLM
"""
from loguru import logger
from dashscope import Generation

from config.settings import settings
from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "ai_recommend"


async def synthesizer_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: LLM synthesizer

    Generates natural language answer from reranked results
    """
    session_id = state.get("session_id")

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="synthesize",
            step_name="答案生成",
            progress=100,
            message="正在生成推荐答案..."
        )

    logger.info("=" * 80)
    logger.info("[Synthesizer] Starting answer generation")
    logger.info("=" * 80)

    query = state.get("query", "")
    reranked_results = state.get("reranked_results", [])
    neo4j_results = state.get("neo4j_results", [])  # 获取Neo4j附近信息

    logger.info(f"[Synthesizer] Query: {query}")
    logger.info(f"[Synthesizer] Results to synthesize: {len(reranked_results)}")
    logger.info(f"[Synthesizer] Nearby info from Neo4j: {len(neo4j_results)}")

    if not reranked_results and not neo4j_results:
        logger.warning("[Synthesizer] No results to synthesize - knowledge gap detected")

        # 生成友好的知识缺口提示
        state["final_answer"] = f"""很抱歉，我们的知识库中暂时还没有收录关于「{query}」的相关信息。

**这可能是因为：**
- 该内容尚未录入我们的旅游数据库
- 查询的关键词与数据库内容匹配度较低
- 该类型的信息暂未覆盖

**您可以尝试：**
- 换用更通用的关键词重新搜索
- 询问热门旅游目的地或景点
- 联系我们，我们会尽快补充相关内容

感谢您的理解与支持！🙏"""

        state["sources"] = []
        logger.info("=" * 80)
        logger.success("[Synthesizer] Node completed with knowledge gap message")
        logger.info("=" * 80)
        return state

    try:
        # 判断是否是附近搜索场景
        needs_nearby = state.get("needs_nearby_search", False)
        nearby_type = state.get("nearby_type", "all")

        # Build context from results
        context_parts = []

        # === 场景A: 附近搜索 - 优先使用Neo4j结果 ===
        if needs_nearby and neo4j_results:
            logger.info(f"[Synthesizer] 📍 Nearby search mode - using Neo4j results as primary")

            # 1. Neo4j附近结果（主要内容）
            for i, nr in enumerate(neo4j_results[:7]):  # Top 7附近推荐
                if isinstance(nr, dict):
                    name = nr.get('name', '')
                    description = nr.get('description', '')
                    city = nr.get('city', '')
                    category = nr.get('category', '')

                    context_parts.append(
                        f"附近景点 {i+1}: {name}\n"
                        f"位置: {city}\n"
                        f"类型: {category}\n"
                        f"描述: {description[:500]}"
                    )

            # 2. Milvus结果作为补充（如果有）
            if reranked_results:
                context_parts.append("\n=== 其他相关推荐 ===\n")
                for i, r in enumerate(reranked_results[:3]):  # 补充3个
                    if isinstance(r, dict):
                        title = r.get('name', f'景点{i+1}')
                        content = r.get('description', '')
                        context_parts.append(
                            f"推荐 {i+1}: {title}\n描述: {content[:300]}"
                        )

        # === 场景B: 常规搜索 - 使用Milvus reranked结果 ===
        else:
            logger.info(f"[Synthesizer] 🔍 Regular search mode - using reranked results")

            for i, r in enumerate(reranked_results):
                if hasattr(r, 'name'):
                    title = r.name
                    content = r.destination.description if hasattr(r, 'destination') else ''
                elif isinstance(r, dict):
                    title = r.get('name') or r.get('title', f'Result {i+1}')
                    content = r.get('description') or r.get('content', '')
                else:
                    continue

                context_parts.append(
                    f"景点 {i+1}: {title}\n描述: {content[:500]}"
                )

            # 附近信息作为补充
            if neo4j_results:
                context_parts.append("\n=== 附近景点信息 ===\n")
                for i, nr in enumerate(neo4j_results[:3]):
                    nearby_name = nr.get('name', '')
                    nearby_desc = nr.get('description', '')
                    if nearby_name:
                        context_parts.append(f"- {nearby_name}: {nearby_desc[:200]}")

        context = "\n\n".join(context_parts)

        # Build prompt (根据场景调整)
        if needs_nearby and neo4j_results:
            # === 附近搜索场景的Prompt ===
            prompt = f"""你是一位专业、贴心的旅游顾问。用户正在寻找**附近/周边**的推荐，请重点介绍检索到的附近景点。

【用户问题】
{query}

【检索到的附近景点】
{context}

【核心原则 - 必须严格遵守】

1. **重点介绍附近景点**
   - 用户询问的是"附近"或"周边"，检索结果已经是附近景点
   - ✅ 直接介绍这些附近景点的特色、位置、游玩建议
   - ❌ 不要说"很抱歉没有找到"，因为已经找到了附近景点

2. **真实性第一**
   - ✅ 只使用检索结果中的信息
   - ❌ 不要编造景点名称、价格、营业时间等

3. **回答结构建议**
   - 开头：简要说明找到了X个附近景点
   - 主体：逐一介绍这些景点（特色、位置、游玩建议）
   - 结尾：给出一般性的出行建议

4. **回答格式**
   - 使用Markdown格式，结构清晰
   - 适当使用emoji增强可读性（不要过度）
   - 重点信息使用加粗**强调**
   - 分段合理，便于阅读

【绝对禁止的行为】
❌ 编造任何未在检索结果中出现的景点、酒店、餐厅名称
❌ 编造距离、价格、营业时间等具体数据
❌ 说"很抱歉没有找到附近景点"（明明已经找到了）

---
回答："""
        else:
            # === 常规搜索场景的Prompt ===
            prompt = f"""你是一位专业、贴心的旅游顾问。请根据检索到的信息，为用户提供准确、实用的旅游建议。

【用户问题】
{query}

【检索到的信息】
{context}

【核心原则 - 必须严格遵守】

1. **真实性第一 - 只使用检索结果中的信息**
   - ✅ 检索结果中有什么，就介绍什么
   - ❌ 检索结果中没有的，绝对不能提及或编造
   - ❌ 禁止编造景点名称、酒店名称、餐厅名称、价格、营业时间等任何具体信息

2. **诚实告知信息缺口**
   - 如果检索结果与用户问题**类型不匹配**：
     * 例如：用户问美食推荐，但检索到的都是景点
     * 例如：用户问酒店住宿，但检索到的都是自然景观
   - **必须明确说明**：
     > "很抱歉，我们的数据库中暂时还没有关于【XXX】的详细信息，但为您找到了以下相关的【YYY】信息供参考。"
   - 然后简要介绍检索到的内容，**不要试图回答用户的原始问题**

3. **匹配时的回答策略**
   - 如果检索结果与用户问题匹配良好，直接提供：
     * 景点特色与亮点
     * 游玩建议（最佳时间、游览路线等）
     * 注意事项
   - 语言风格：专业但亲切，信息丰富但条理清晰

4. **一般性建议的边界**
   - ✅ 可以给出常识性的旅游建议：
     * "建议提前预订门票"
     * "推荐使用公共交通前往"
     * "注意防晒和补水"
   - ❌ 不要推荐具体的商家、服务：
     * "XXX酒店性价比高"
     * "推荐去XXX餐厅"

5. **回答格式**
   - 使用Markdown格式，结构清晰
   - 适当使用emoji增强可读性（不要过度）
   - 重点信息使用加粗**强调**
   - 分段合理，便于阅读

【绝对禁止的行为】
❌ 编造任何未在检索结果中出现的景点、酒店、餐厅名称
❌ 编造距离、价格、营业时间、联系方式等具体数据
❌ 用户问美食却介绍美食（如果检索结果是景点）
❌ 使用"附近还有XXX"（除非检索结果明确包含）
❌ 为了回答完整而添加检索结果之外的信息

【期望输出】
请生成一个专业、友好、准确的旅游建议，帮助用户做出更好的旅行决策。

---
回答："""

        # Call LLM
        response = Generation.call(
            model=settings.QWEN_MODEL,
            prompt=prompt,
            api_key=settings.DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            final_answer = response.output.text.strip()
            state["final_answer"] = final_answer

            # 打印LLM生成的答案（调试用）
            logger.info("=" * 80)
            logger.info("[Synthesizer] LLM Generated Answer:")
            logger.info(final_answer)
            logger.info("=" * 80)

            # 准备sources用于前端展示（使用所有通过rerank阈值过滤的结果）
            sources = []
            for i, r in enumerate(reranked_results):
                if isinstance(r, dict):
                    rerank_score = r.get('rerank_score', 0)
                    fallback_score = r.get('score', 0)
                    final_score = rerank_score if rerank_score > 0 else fallback_score

                    logger.info(f"[Synthesizer] Source #{i+1}: {r.get('name')} | rerank_score={rerank_score:.4f}, score={fallback_score:.4f}, final={final_score:.4f}")

                    sources.append({
                        "name": r.get('name', f'景点{i+1}'),
                        "description": r.get('description', '')[:300],
                        "score": final_score,
                        "source": r.get('source', 'unknown')
                    })

            state["sources"] = sources

            logger.info(f"[Synthesizer] Prepared sources: {[s['name'] + ' - ' + str(s['score']) for s in sources]}")

            # 准备附近推荐（单独保存）
            nearby_recommendations = []
            if neo4j_results:
                nearby_type = state.get('nearby_type', 'all')
                for i, nr in enumerate(neo4j_results[:5]):  # Top 5附近推荐
                    if isinstance(nr, dict):
                        nearby_recommendations.append({
                            "name": nr.get('name', f'附近景点{i+1}'),
                            "description": nr.get('description', '')[:300],
                            "province": nr.get('province', ''),
                            "city": nr.get('city', ''),
                            "category": nr.get('category', ''),
                            "type": nearby_type,  # attraction/hotel/food/all
                            "source": "neo4j_nearby"
                        })

            state["nearby_recommendations"] = nearby_recommendations

            logger.success(f"[Synthesizer] Generated answer: {len(final_answer)} characters")
            logger.info(f"[Synthesizer] Prepared {len(sources)} sources for frontend")
            logger.info(f"[Synthesizer] Prepared {len(nearby_recommendations)} nearby recommendations")
        else:
            logger.error(f"[Synthesizer] LLM call failed: {response.status_code}")
            state["final_answer"] = "生成回答失败，请稍后重试。"
            state["sources"] = []
            state["nearby_recommendations"] = []

    except Exception as e:
        logger.error(f"[Synthesizer] Generation failed: {e}")
        import traceback
        traceback.print_exc()

        state["final_answer"] = f"生成回答时出错: {str(e)}"
        state["sources"] = []
        state["nearby_recommendations"] = []

    logger.info("=" * 80)
    logger.success("[Synthesizer] Node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="synthesize",
            step_name="答案生成",
            progress=100,
            message="推荐答案生成完成"
        )

    return state
