# AI团队推荐 - 流程优化方案：智能分支

## 🎯 优化目标

根据RAG和GraphRAG的检索结果，智能决定是否需要调用专业团队，避免无效调用。

---

## 📊 当前流程 vs 优化后流程

### 当前流程（固定流程）
```
用户查询
  ↓
🔍 Query重写器
  ↓
📚 RAG检索 (Milvus)
  ↓
🗺️ 图RAG (Neo4j)
  ↓
📅 行程规划师 (总是调用)
  ↓
🚗 交通助手 (总是调用)
  ↓
🍜 美食助手 (总是调用)
  ↓
💰 预算专家 (总是调用)
  ↓
最终答案
```

**问题：**
- ❌ 即使RAG没查到结果，也调用所有专业团队
- ❌ 浪费Token和时间
- ❌ 答案质量差（无数据支撑）

---

### 优化后流程（智能分支）

```
用户查询
  ↓
🔍 Query重写器
  ↓
📚 RAG检索 (Milvus) → 返回 N 条结果
  ↓
🗺️ 图RAG (Neo4j) → 返回 M 条结果
  ↓
📊 智能判断：
  
  情况1: N > 0 或 M > 0 (有检索结果)
  ├─ 判断用户意图类型：
  │   
  │   ├─ 景点推荐类: "推荐景点" / "有什么好玩的"
  │   │   → 仅用RAG+图RAG结果，不调用专业团队
  │   │   → 直接整合润色返回
  │   │
  │   ├─ 行程规划类: "X天攻略" / "行程安排"
  │   │   → 调用: 行程规划师 + 交通助手
  │   │   → 跳过: 美食助手、预算专家
  │   │
  │   ├─ 全面攻略类: "完整攻略" / "旅游指南"
  │   │   → 调用所有专业团队
  │   │
  │   └─ 特定咨询类: "怎么去" / "吃什么"
  │       → 只调用相关助手
  │
  └─ 生成答案
  
  情况2: N = 0 且 M = 0 (无检索结果)
  └─ 知识缺口回复：
      "抱歉，暂无相关信息..."
      不调用任何专业团队
```

---

## 🛠️ 实施方案

### 方案核心：意图分类 + 智能调度

#### 1. 在Query重写器中添加意图分类

**扩展 `query_rewriter.py`**

```python
async def rewrite(self, query: str, session_id: str = None) -> Dict[str, Any]:
    """
    重写用户查询并分类意图
    
    Returns:
        {
            "is_travel_related": bool,
            "rewritten_query": str,
            "should_continue": bool,
            "intent_type": str,  # 新增：意图类型
            "friendly_response": str (optional)
        }
    """
    # ... 现有逻辑
    
    # 新增：意图分类
    intent = self._classify_intent(query)
    
    return {
        "is_travel_related": True,
        "rewritten_query": optimized_query,
        "should_continue": True,
        "intent_type": intent  # 新增字段
    }

def _classify_intent(self, query: str) -> str:
    """
    分类用户意图
    
    Returns:
        - "spot_recommendation": 景点推荐（只要结果列表）
        - "itinerary_planning": 行程规划（需要详细安排）
        - "comprehensive_guide": 全面攻略（需要所有信息）
        - "specific_query": 特定咨询（交通/美食/预算）
    """
    query_lower = query.lower()
    
    # 景点推荐关键词
    spot_keywords = ['推荐', '有什么', '哪些景点', '好玩的', '值得去']
    
    # 行程规划关键词
    itinerary_keywords = ['天', '行程', '安排', '路线', '怎么玩']
    
    # 全面攻略关键词
    comprehensive_keywords = ['攻略', '旅游指南', '完整', '全部', '详细']
    
    # 特定咨询关键词
    transport_keywords = ['怎么去', '交通', '车', '飞机', '高铁']
    food_keywords = ['吃', '美食', '餐厅', '特色菜']
    budget_keywords = ['预算', '费用', '多少钱', '价格']
    
    # 判断逻辑
    if any(kw in query_lower for kw in comprehensive_keywords):
        return "comprehensive_guide"
    
    if any(kw in query_lower for kw in itinerary_keywords):
        return "itinerary_planning"
    
    if any(kw in query_lower for kw in transport_keywords):
        return "specific_query:transport"
    
    if any(kw in query_lower for kw in food_keywords):
        return "specific_query:food"
    
    if any(kw in query_lower for kw in budget_keywords):
        return "specific_query:budget"
    
    if any(kw in query_lower for kw in spot_keywords):
        return "spot_recommendation"
    
    # 默认：如果不确定，归为全面攻略
    return "comprehensive_guide"
```

---

#### 2. 更新Master Agent的coordinate方法

**修改 `master_agent.py`**

```python
async def coordinate(self, query: str, ..., session_id: str = None):
    """主协调方法"""
    
    # Step 0: Query重写
    rewrite_result = await self.query_rewriter.rewrite(query, session_id)
    
    if not rewrite_result.get('should_continue'):
        # 闲聊，直接返回
        return {...}
    
    # 获取意图类型
    intent_type = rewrite_result.get('intent_type', 'comprehensive_guide')
    optimized_query = rewrite_result.get('rewritten_query', query)
    
    logger.info(f"[Master] Intent detected: {intent_type}")
    
    # Step 1: RAG检索
    rag_results = await self._run_rag_assistant(optimized_query)
    
    # Step 2: 图RAG检索
    graph_results = await self._run_graph_rag_assistant(optimized_query, rag_results)
    
    # 检查是否有检索结果
    has_results = len(rag_results) > 0 or len(graph_results) > 0
    
    if not has_results:
        # 无检索结果，直接返回知识缺口回复
        logger.warning("[Master] No results from RAG or Graph RAG")
        return {
            'success': True,
            'answer': self._generate_no_result_message(optimized_query),
            'sources': [],
            'metadata': {'workflow': 'team_recommend', 'type': 'no_results'},
            'agent_logs': agent_logs
        }
    
    # 有检索结果，根据意图决定调用哪些专业团队
    if intent_type == "spot_recommendation":
        # 只要景点列表，不调用专业团队
        logger.info("[Master] Spot recommendation - skipping specialized agents")
        final_answer = await self._synthesize_simple_recommendation(
            optimized_query, rag_results, graph_results
        )
        
    elif intent_type == "itinerary_planning":
        # 调用行程规划师 + 交通助手
        logger.info("[Master] Itinerary planning - calling planner + transport")
        itinerary = await self._run_itinerary_planner(optimized_query, rag_results)
        transport = await self._run_transport_assistant(optimized_query, rag_results)
        
        final_answer = await self._synthesize_itinerary(
            optimized_query, rag_results, graph_results, itinerary, transport
        )
        
    elif intent_type.startswith("specific_query:"):
        # 特定咨询，只调用相关助手
        specific_type = intent_type.split(":")[1]
        logger.info(f"[Master] Specific query: {specific_type}")
        
        if specific_type == "transport":
            transport = await self._run_transport_assistant(optimized_query, rag_results)
            final_answer = await self._synthesize_specific(
                optimized_query, rag_results, transport_info=transport
            )
        elif specific_type == "food":
            food = await self._run_food_assistant(optimized_query, rag_results)
            final_answer = await self._synthesize_specific(
                optimized_query, rag_results, food_info=food
            )
        # ... 其他特定类型
        
    else:
        # comprehensive_guide - 调用所有专业团队
        logger.info("[Master] Comprehensive guide - calling all agents")
        # ... 现有的完整流程
    
    return {
        'success': True,
        'answer': final_answer,
        'sources': sources,
        'metadata': {...},
        'agent_logs': agent_logs
    }
```

---

#### 3. 添加简化的合成方法

**在 `master_agent.py` 中添加**

```python
async def _synthesize_simple_recommendation(
    self,
    query: str,
    rag_results: List[Dict],
    graph_results: List[Dict]
) -> str:
    """
    简单推荐：仅基于RAG和图RAG结果
    
    不调用专业团队，直接整合润色
    """
    logger.info("[Master] Synthesizing simple recommendation")
    
    # 构建上下文
    context = "根据您的查询，以下是推荐的景点：\n\n"
    
    # RAG结果
    if rag_results:
        context += "=== 主要推荐 ===\n"
        for i, r in enumerate(rag_results[:5], 1):
            context += f"{i}. {r.get('name', '未知景点')}\n"
            context += f"   类别: {r.get('category', '未分类')}\n"
            context += f"   描述: {r.get('description', '暂无描述')[:100]}...\n\n"
    
    # 图RAG结果
    if graph_results:
        context += "\n=== 附近/相关景点 ===\n"
        for i, r in enumerate(graph_results[:5], 1):
            context += f"{i}. {r.get('name')}\n"
            context += f"   位置: {r.get('city')}\n"
            context += f"   描述: {r.get('description', '')[:80]}...\n\n"
    
    # 使用LLM润色
    prompt = f"""请根据以下景点信息，生成一个简洁友好的推荐回答。

用户查询: {query}

{context}

要求：
1. 突出每个景点的特色
2. 按重要程度排序
3. 简洁明了，不要过于冗长
4. 使用友好的语气
"""
    
    try:
        response = Generation.call(
            model=self.llm,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message'
        )
        
        final_answer = response.output.choices[0].message.content
        return final_answer
        
    except Exception as e:
        logger.error(f"[Master] LLM synthesis failed: {e}")
        # 回退：返回原始context
        return context


def _generate_no_result_message(self, query: str) -> str:
    """生成知识缺口回复"""
    return f"""很抱歉，我们的知识库中暂时还没有收录关于「{query}」的相关信息。

**这可能是因为：**
- 该内容尚未录入我们的旅游数据库
- 查询的关键词与数据库内容匹配度较低
- 该类型的信息暂未覆盖

**您可以尝试：**
- 换用更通用的关键词重新搜索
- 询问热门旅游目的地或景点
- 联系我们，我们会尽快补充相关内容

感谢您的理解与支持！🙏"""
```

---

## 📋 实施步骤

### Phase 1: 扩展Query重写器
- [ ] 添加 `_classify_intent()` 方法
- [ ] 返回结果中添加 `intent_type` 字段
- [ ] 测试意图分类准确性

### Phase 2: 更新Master Agent
- [ ] 添加结果检查逻辑
- [ ] 添加智能分支调度
- [ ] 实现 `_synthesize_simple_recommendation()`
- [ ] 实现 `_generate_no_result_message()`

### Phase 3: 测试优化效果
- [ ] 测试景点推荐场景
- [ ] 测试行程规划场景
- [ ] 测试无结果场景
- [ ] 性能对比（Token消耗、响应时间）

---

## 🎯 预期效果

### 场景1: 景点推荐
```
输入: "推荐三清山附近的景点"

流程:
  🔍 Query重写 → intent: spot_recommendation
  📚 RAG检索 → 8条结果
  🗺️ 图RAG → 5条结果
  
  ✅ 有结果 + 景点推荐类型
  ❌ 跳过：行程规划师、交通、美食、预算
  ✅ 直接润色返回

结果: 快速返回景点列表，节省80% Token
```

### 场景2: 行程规划
```
输入: "三清山3天旅游攻略"

流程:
  🔍 Query重写 → intent: comprehensive_guide
  📚 RAG检索 → 8条结果
  🗺️ 图RAG → 5条结果
  
  ✅ 有结果 + 全面攻略类型
  ✅ 调用所有专业团队
  
结果: 完整的行程+交通+美食+预算
```

### 场景3: 无结果
```
输入: "华山的交通"

流程:
  🔍 Query重写 → intent: specific_query:transport
  📚 RAG检索 → 0条结果
  🗺️ 图RAG → 0条结果
  
  ❌ 无结果
  ❌ 跳过所有专业团队
  ✅ 直接返回知识缺口回复
  
结果: "很抱歉，暂无华山相关信息..."
```

---

## 📊 优化收益

| 场景 | 当前Token | 优化后Token | 节省 | 响应时间 |
|------|-----------|-------------|------|----------|
| 景点推荐 | ~8000 | ~1500 | 81% | ↓60% |
| 无结果 | ~5000 | ~500 | 90% | ↓80% |
| 完整攻略 | ~10000 | ~10000 | 0% | 不变 |

---

**准备开始实施吗？我可以逐步帮你完成每个修改！**
