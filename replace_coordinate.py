import re

# 读取文件
with open("E:/大模型开发/代码/网站/travel_proj/backend/app/workflows/team_recommend/master_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 新的coordinate方法
new_coordinate = '''    async def coordinate(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        progress_callback = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Coordinate all subagents to generate comprehensive recommendation

        智能路由逻辑：根据意图和检索结果决定调用哪些Agent
        """
        logger.info(f"Master Agent coordinating for: {query[:50]}...")

        agent_logs = []

        try:
            # ========== Step 0: Query重写 ==========
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': '查询重写助手',
                    'status': 'working',
                    'message': '正在理解您的问题...',
                    'progress': 5
                })

            rewrite_result = await self.query_rewriter.rewrite(query, session_id)

            agent_logs.append({
                'agent': '查询重写助手',
                'status': 'completed',
                'summary': f"问题分析完成：{'旅游问题' if rewrite_result.get('is_travel_related') else '闲聊'}"
            })

            # 如果不是旅游问题，直接返回友好回复
            if not rewrite_result.get('should_continue', True):
                friendly_response = rewrite_result.get(
                    'friendly_response',
                    "您好！我是旅游推荐助手，专注于帮您规划旅行。如果您有旅游相关的问题，欢迎随时提问！😊"
                )

                logger.info(f"[Master] Non-travel query detected, returning friendly response")

                return {
                    'success': True,
                    'answer': friendly_response,
                    'sources': [],
                    'metadata': {'workflow': 'team_recommend', 'type': 'chitchat'},
                    'agent_logs': agent_logs
                }

            # 使用重写后的查询和意图
            optimized_query = rewrite_result.get('rewritten_query', query)
            intent_type = rewrite_result.get('intent_type', 'comprehensive_guide')

            logger.info(f"[Master] Original query: {query}")
            logger.info(f"[Master] Rewritten query: {optimized_query}")
            logger.info(f"[Master] Intent type: {intent_type}")

            # ========== Step 1: RAG检索 ==========
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'RAG知识库助手',
                    'status': 'working',
                    'message': '正在搜索知识库...',
                    'progress': 10
                })

            rag_results = await self._run_rag_assistant(optimized_query)
            agent_logs.append({
                'agent': 'RAG知识库助手',
                'status': 'completed',
                'summary': f'从向量数据库检索到 {len(rag_results)} 条结果',
                'result_count': len(rag_results)
            })

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': 'RAG知识库助手',
                    'status': 'completed',
                    'message': f'找到 {len(rag_results)} 条相关结果',
                    'progress': 20
                })

            # ========== Step 2: 图RAG检索 ==========
            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': '图RAG知识库助手',
                    'status': 'working',
                    'message': '正在分析知识图谱...',
                    'progress': 30
                })

            graph_results = await self._run_graph_rag_assistant(optimized_query, rag_results)
            agent_logs.append({
                'agent': '图RAG知识库助手',
                'status': 'completed',
                'summary': f'找到 {len(graph_results)} 个相关景点',
                'result_count': len(graph_results)
            })

            if progress_callback:
                await progress_callback({
                    'type': 'progress',
                    'agent': '图RAG知识库助手',
                    'status': 'completed',
                    'message': f'找到 {len(graph_results)} 个相关地点',
                    'progress': 40
                })

            # ========== 智能判断：检查是否有检索结果 ==========
            has_results = len(rag_results) > 0 or len(graph_results) > 0

            if not has_results:
                # 无检索结果，直接返回知识缺口回复
                logger.warning("[Master] No results - returning no result message")

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '主智能体',
                        'status': 'completed',
                        'message': '知识库暂无相关信息',
                        'progress': 100
                    })

                return {
                    'success': True,
                    'answer': self._generate_no_result_message(optimized_query),
                    'sources': [],
                    'metadata': {
                        'workflow': 'team_recommend',
                        'type': 'no_results',
                        'intent': intent_type
                    },
                    'agent_logs': agent_logs
                }

            # ========== 有结果，根据意图智能路由 ==========
            logger.info(f"[Master] Has results, routing by intent: {intent_type}")

            # 准备sources
            sources = []
            for result in rag_results[:5]:
                sources.append({
                    'name': result.get('name', 'Unknown'),
                    'location': result.get('city', ''),
                    'description': result.get('description', '')[:200],
                    'score': result.get('score', 0.5),
                    'category': result.get('category', '')
                })

            # 根据不同意图类型处理
            if intent_type == "spot_recommendation":
                # 景点推荐：只用RAG+图RAG，不调用专业团队
                logger.info("[Master] Spot recommendation - skipping specialized agents")

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '主智能体',
                        'status': 'working',
                        'message': '正在整理景点推荐...',
                        'progress': 60
                    })

                final_answer = await self._synthesize_simple_recommendation(
                    optimized_query, rag_results, graph_results
                )

                agent_logs.append({
                    'agent': '主智能体',
                    'status': 'completed',
                    'summary': '景点推荐已生成（简化流程）'
                })

            elif intent_type == "itinerary_planning":
                # 行程规划：只调用行程+交通
                logger.info("[Master] Itinerary planning - calling planner + transport")

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '专业团队',
                        'status': 'working',
                        'message': '行程和交通专家正在工作...',
                        'progress': 50
                    })

                itinerary, transport = await asyncio.gather(
                    self._run_itinerary_planner(optimized_query, rag_results),
                    self._run_transport_assistant(optimized_query, rag_results)
                )

                agent_logs.extend([
                    {'agent': '行程规划师', 'status': 'completed', 'summary': '旅行计划已生成'},
                    {'agent': '交通助手', 'status': 'completed', 'summary': '交通方案已提供'}
                ])

                # 简化合成
                prompt = f"""用户查询: {optimized_query}

行程安排:
{itinerary[:1000]}

交通建议:
{transport[:800]}

请整合以上信息，生成简洁的行程规划方案。用中文回答。"""

                response = Generation.call(
                    model=self.llm,
                    messages=[{'role': 'user', 'content': prompt}],
                    result_format='message'
                )
                final_answer = response.output.choices[0].message.content

            elif intent_type.startswith("specific_query:"):
                # 特定咨询：只调用相关助手
                specific_type = intent_type.split(":")[1]
                logger.info(f"[Master] Specific query: {specific_type}")

                if specific_type == "transport":
                    transport = await self._run_transport_assistant(optimized_query, rag_results)
                    agent_logs.append({'agent': '交通助手', 'status': 'completed', 'summary': '交通方案已提供'})
                    final_answer = transport

                elif specific_type == "food":
                    food = await self._run_food_assistant(optimized_query, rag_results)
                    agent_logs.append({'agent': '美食助手', 'status': 'completed', 'summary': '美食推荐已准备'})
                    final_answer = food

                else:
                    # 其他特定咨询，回退到简单推荐
                    final_answer = await self._synthesize_simple_recommendation(
                        optimized_query, rag_results, graph_results
                    )

            else:
                # comprehensive_guide：调用所有专业团队（完整流程）
                logger.info("[Master] Comprehensive guide - calling all agents")

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '专业团队',
                        'status': 'working',
                        'message': '行程、交通、美食专家正在并行工作...',
                        'progress': 50
                    })

                itinerary, transport, food = await asyncio.gather(
                    self._run_itinerary_planner(optimized_query, rag_results),
                    self._run_transport_assistant(optimized_query, rag_results),
                    self._run_food_assistant(optimized_query, rag_results)
                )

                agent_logs.extend([
                    {'agent': '行程规划师', 'status': 'completed', 'summary': '旅行计划已生成'},
                    {'agent': '交通助手', 'status': 'completed', 'summary': '交通方案已提供'},
                    {'agent': '美食助手', 'status': 'completed', 'summary': '美食推荐已准备'}
                ])

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '预算专家',
                        'status': 'working',
                        'message': '正在计算预算...',
                        'progress': 80
                    })

                budget = await self._run_budget_expert(optimized_query, itinerary, transport, food)
                agent_logs.append({
                    'agent': '预算专家',
                    'status': 'completed',
                    'summary': '预算分析已完成'
                })

                if progress_callback:
                    await progress_callback({
                        'type': 'progress',
                        'agent': '主智能体',
                        'status': 'working',
                        'message': '正在生成最终方案...',
                        'progress': 95
                    })

                final_answer = await self._synthesize_final_answer(
                    optimized_query, itinerary, transport, food, budget, rag_results
                )

            logger.success("Master Agent coordination completed")

            return {
                'success': True,
                'answer': final_answer,
                'sources': sources,
                'metadata': {
                    'workflow': 'team_recommend',
                    'agents_used': len(agent_logs),
                    'intent': intent_type
                },
                'agent_logs': agent_logs
            }

        except Exception as e:
            logger.error(f"Master Agent coordination failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'answer': f'推荐生成失败: {str(e)}',
                'sources': [],
                'metadata': {},
                'agent_logs': agent_logs
            }
'''

# 使用正则表达式替换coordinate方法
pattern = r'    async def coordinate\([\s\S]*?(?=\n    async def _run_rag_assistant)'
content = re.sub(pattern, new_coordinate + '\n', content)

# 写回文件
with open("E:/大模型开发/代码/网站/travel_proj/backend/app/workflows/team_recommend/master_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("coordinate method replaced successfully")
