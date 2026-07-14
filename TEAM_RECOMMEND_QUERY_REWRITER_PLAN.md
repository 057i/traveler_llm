# AI团队推荐 - 优化方案：添加Query重写器

## 🎯 优化目标

1. **添加Query重写子智能体** - 理解用户意图，重写问题
2. **添加历史记录工具** - 获取用户历史聊天记录
3. **闲聊过滤** - 识别非旅游问题，礼貌回应
4. **优化所有子智能体Prompt** - 更专业、更清晰

---

## 📊 新的工作流程

### 当前流程（简化）
```
用户查询
  ↓
主智能体协调
  ↓
RAG检索 → 图RAG → 行程规划 → ... → 生成答案
```

### 优化后流程
```
用户查询
  ↓
主智能体（协调者）
  ↓
【1. Query重写器】
  ├─ 工具：获取历史聊天记录
  ├─ 分析：理解用户意图
  ├─ 重写：优化查询语句
  └─ 判断：是旅游问题 or 闲聊？
  
  ↓ 如果是旅游问题
  
【2. RAG知识库助手】
  └─ 工具：Milvus混合检索
  
  ↓
  
【3. 图RAG助手】
  ├─ 工具：查询附近景点
  └─ 工具：查询同城景点
  
  ↓
  
【4. 专业团队（并行）】
  ├─ 行程规划师
  ├─ 交通助手
  └─ 美食助手
  
  ↓
  
【5. 预算专家】
  └─ 估算费用
  
  ↓
  
【6. 主智能体】
  └─ 整合所有结果，生成最终答案
```

### 闲聊分支
```
用户查询: "你好" / "天气怎么样" / "讲个笑话"
  ↓
Query重写器判断：非旅游问题
  ↓
直接返回友好回复：
  "您好！我是旅游推荐助手，专注于帮您规划旅行。
   如果您有旅游相关的问题，欢迎随时提问！"
```

---

## 🛠️ 实施方案

### 1. 创建Query重写器子智能体

**文件：`backend/app/workflows/team_recommend/subagents/query_rewriter.py`**

```python
"""
Query Rewriter Assistant - 查询重写助手

负责：
1. 获取历史聊天记录
2. 理解用户意图
3. 重写优化查询
4. 判断是否为旅游问题
"""
from .langchain_base import LangChainAgent
from .query_tools import get_chat_history, is_travel_query
from loguru import logger
from typing import Dict, Any


class QueryRewriter(LangChainAgent):
    """查询重写助手 - 理解意图并重写问题"""

    def __init__(self):
        tools = [
            get_chat_history,
            is_travel_query
        ]

        system_prompt = """你是一个查询重写专家，负责理解用户意图并优化查询。

**你的工具：**
1. get_chat_history(session_id, limit) - 获取用户历史聊天记录
2. is_travel_query(query) - 判断是否为旅游相关问题

**工作流程：**

第一步：获取上下文
- 调用 get_chat_history 获取最近3-5条历史记录
- 分析用户的对话历史

第二步：理解意图
- 如果用户说"那里"、"它"、"附近"等代词，结合历史找到指代对象
- 识别用户真正想问什么

第三步：判断问题类型
- 调用 is_travel_query 判断是否为旅游问题
- 旅游问题包括：景点推荐、行程规划、交通、美食、住宿等
- 非旅游问题：闲聊、天气、新闻、笑话等

第四步：重写查询
- 如果是旅游问题：补充上下文，优化为完整清晰的问题
  例如："那里怎么去？" → "从上饶市区到三清山怎么去？"
  
- 如果是闲聊：标记为非旅游问题，准备礼貌回复

**返回格式（JSON）：**
```json
{
  "is_travel_related": true/false,
  "rewritten_query": "重写后的完整问题",
  "original_intent": "用户意图描述",
  "should_continue": true/false,
  "friendly_response": "如果是闲聊，这里放回复内容"
}
```

**注意事项：**
- 保持用户原意，不要过度解读
- 如果历史记录中有明确的地点/景点，优先使用
- 闲聊时要友好礼貌，引导用户提旅游问题
"""

        super().__init__(
            name="查询重写助手",
            system_prompt=system_prompt,
            tools=tools
        )

        logger.info("[Query Rewriter] Initialized with history + intent tools")

    async def rewrite(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        重写用户查询

        Args:
            query: 用户原始查询
            session_id: 会话ID

        Returns:
            {
                "is_travel_related": bool,
                "rewritten_query": str,
                "should_continue": bool,
                "friendly_response": str (optional)
            }
        """
        try:
            # 调用LangChain Agent执行重写
            task = f"用户查询: {query}\n会话ID: {session_id}\n\n请分析并重写查询。"
            result_text = await self.execute(task)

            # 解析结果
            import json
            import re
            
            # 尝试从结果中提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 回退：解析失败，假设是旅游问题
                result = {
                    "is_travel_related": True,
                    "rewritten_query": query,
                    "should_continue": True
                }

            logger.info(f"[Query Rewriter] Result: {result}")
            return result

        except Exception as e:
            logger.error(f"[Query Rewriter] Failed: {e}")
            import traceback
            traceback.print_exc()
            
            # 回退：出错时假设是旅游问题
            return {
                "is_travel_related": True,
                "rewritten_query": query,
                "should_continue": True
            }
```

---

### 2. 创建Query工具函数

**文件：`backend/app/workflows/team_recommend/subagents/query_tools.py`**

```python
"""
Query处理工具

1. 获取历史聊天记录
2. 判断是否为旅游问题
"""
from typing import List, Optional
from loguru import logger
import json

try:
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available, using fallback decorator")
    LANGCHAIN_AVAILABLE = False

    def tool(func):
        func.name = func.__name__
        func.description = func.__doc__
        async def ainvoke(args):
            if isinstance(args, dict):
                return await func(**args)
            else:
                return await func(args)
        func.ainvoke = ainvoke
        return func


@tool
async def get_chat_history(session_id: str, limit: int = 5) -> str:
    """
    获取用户历史聊天记录

    Args:
        session_id: 会话ID
        limit: 获取最近N条记录，默认5条

    Returns:
        JSON字符串，包含历史对话
    """
    logger.info(f"[Tool] get_chat_history called: session_id={session_id}, limit={limit}")

    try:
        from app.api.index import getChatHistory

        # 获取历史记录
        response = await getChatHistory(session_id, limit)

        if not response or not response.get('messages'):
            return json.dumps({
                "success": True,
                "count": 0,
                "messages": [],
                "summary": "没有历史记录"
            }, ensure_ascii=False)

        # 格式化历史记录
        messages = response.get('messages', [])
        formatted = []
        
        for msg in messages[-limit:]:  # 只取最近N条
            formatted.append({
                "role": msg.get('type', 'user'),  # user or assistant
                "content": msg.get('content', '')[:200],  # 限制长度
                "timestamp": msg.get('timestamp', '')
            })

        result = {
            "success": True,
            "count": len(formatted),
            "messages": formatted,
            "summary": f"最近{len(formatted)}条对话"
        }

        logger.success(f"[Tool] get_chat_history: found {len(formatted)} messages")

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] get_chat_history failed: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": str(e),
            "count": 0,
            "messages": []
        }, ensure_ascii=False)


@tool
async def is_travel_query(query: str) -> str:
    """
    判断是否为旅游相关问题

    Args:
        query: 用户查询

    Returns:
        JSON字符串，包含判断结果
    """
    logger.info(f"[Tool] is_travel_query called: query='{query}'")

    try:
        # 旅游相关关键词
        travel_keywords = [
            '景点', '旅游', '攻略', '游玩', '推荐', '路线', '行程',
            '酒店', '住宿', '门票', '美食', '特产', '交通', '怎么去',
            '好玩', '值得', '附近', '周边', '几天', '预算', '费用',
            '山', '寺', '湖', '岛', '古镇', '公园', '博物馆', '风景'
        ]

        # 闲聊关键词
        chitchat_keywords = [
            '你好', 'hello', 'hi', '天气', '笑话', '故事', '新闻',
            '聊天', '陪我', '你是谁', '你叫什么', '你会什么',
            '唱歌', '跳舞', '做饭', '游戏', '电影', '音乐'
        ]

        query_lower = query.lower()

        # 检查旅游关键词
        travel_score = sum(1 for kw in travel_keywords if kw in query_lower)

        # 检查闲聊关键词
        chitchat_score = sum(1 for kw in chitchat_keywords if kw in query_lower)

        # 判断
        is_travel = travel_score > 0 or (travel_score == 0 and chitchat_score == 0)

        result = {
            "success": True,
            "is_travel_related": is_travel,
            "travel_score": travel_score,
            "chitchat_score": chitchat_score,
            "confidence": 0.8 if travel_score > 0 else 0.5,
            "reason": f"旅游关键词匹配: {travel_score}, 闲聊关键词匹配: {chitchat_score}"
        }

        logger.info(f"[Tool] is_travel_query: {result}")

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] is_travel_query failed: {e}")
        return json.dumps({
            "success": False,
            "is_travel_related": True,  # 出错时假设是旅游问题
            "error": str(e)
        }, ensure_ascii=False)
```

---

### 3. 优化所有子智能体Prompt

#### 3.1 RAG知识库助手

```python
system_prompt = """你是RAG知识库检索专家，负责从向量数据库中精准检索旅游信息。

**你的工具：**
- search_travel_knowledge(query, entities) - Milvus混合检索

**工作原则：**
1. 理解查询的核心需求（景点特色、游玩攻略、实用信息等）
2. 使用混合检索确保结果的相关性和准确性
3. 返回最相关的TOP结果，不要遗漏关键信息

**注意事项：**
- 如果查询包含明确的景点名称，优先精确匹配
- 如果是泛指性查询（"好玩的地方"），扩大检索范围
- 结果要包含：景点名称、描述、类别、评分

你的输出将被其他智能体使用，请确保信息完整准确。"""
```

#### 3.2 图RAG助手

```python
system_prompt = """你是知识图谱查询专家，负责从Neo4j图数据库中挖掘景点关系。

**你的工具：**
1. search_nearby_destinations(destination) - 查询附近景点（基于地理关系）
2. search_same_city_destinations(destination) - 查询同城景点（丰富选择）

**工作策略：**
- 当用户问"附近还有什么"时，调用附近景点查询
- 当用户想了解"更多选择"时，调用同城景点查询
- 可以组合使用两个工具，提供全面的关联推荐

**返回要点：**
- 景点名称 + 位置
- 与原景点的关系（附近/同城/同类）
- 简短描述

你的结果将帮助用户发现更多旅游选项。"""
```

#### 3.3 行程规划师

```python
system_prompt = """你是专业的旅行行程规划师，负责设计合理的旅游路线。

**输入信息：**
- 用户需求（天数、偏好）
- RAG检索的景点列表
- 图RAG推荐的关联景点

**规划原则：**
1. **时间合理** - 考虑游玩时长、路程时间
2. **路线顺畅** - 减少往返，地理位置就近安排
3. **劳逸结合** - 热门景点+休闲景点搭配
4. **留有余地** - 不要排得太满

**输出格式：**
Day 1:
  上午：景点A（游玩时间、特色）
  中午：午餐推荐
  下午：景点B
  晚上：住宿建议

请提供可执行的行程，不要泛泛而谈。"""
```

#### 3.4 交通助手

```python
system_prompt = """你是交通规划专家，负责提供详细的交通方案。

**你需要考虑：**
1. **到达景区** - 从出发地到目的地的大交通（飞机、高铁、汽车）
2. **景区间移动** - 景点之间的交通方式
3. **当地交通** - 公交、出租车、租车、包车等选择

**输出要点：**
- 推荐的交通方式（理由：时间、费用、便利性）
- 预计用时
- 大概费用
- 实用建议（订票、乘车地点）

请提供可操作的具体方案，不要只说"可以坐车"。"""
```

#### 3.5 美食助手

```python
system_prompt = """你是当地美食向导，负责推荐特色美食和餐厅。

**推荐维度：**
1. **必吃美食** - 当地特色菜品
2. **餐厅推荐** - 具体店铺（如果知道）
3. **用餐建议** - 哪里吃、什么时候吃
4. **注意事项** - 价格区间、营业时间

**风格：**
- 描述要生动，让人有食欲
- 突出特色，为什么值得尝试
- 考虑不同预算（高中低档都推荐）

例如："上饶特色三清山野菜，清爽可口，是当地人最爱的家常菜。"
"""
```

#### 3.6 预算专家

```python
system_prompt = """你是旅游预算规划专家，负责估算旅行费用。

**费用构成：**
1. **交通费** - 大交通 + 当地交通
2. **住宿费** - 根据天数和档次
3. **门票费** - 景点门票
4. **餐饮费** - 一日三餐
5. **其他费用** - 购物、保险等

**输出格式：**
```
总预算：¥X - ¥Y（人均）

费用明细：
- 交通：¥X（高铁往返 + 当地打车）
- 住宿：¥Y（X晚，中档酒店）
- 门票：¥Z（主要景点）
- 餐饮：¥W（X天）
- 其他：¥V
```

**原则：**
- 给出区间范围（经济型 vs 舒适型）
- 标注主要花费项目
- 提供省钱建议
"""
```

---

### 4. 更新Master Agent

**修改协调逻辑：**

```python
async def coordinate(self, query: str, progress_callback=None, session_id: str = None):
    """
    主智能体协调所有子智能体

    新流程：
    1. Query重写器（理解意图）
    2. 如果是旅游问题 → 继续
    3. 如果是闲聊 → 直接返回友好回复
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
            'summary': f"问题分析完成：{'旅游问题' if rewrite_result['is_travel_related'] else '闲聊'}"
        })
        
        # 如果不是旅游问题，直接返回友好回复
        if not rewrite_result.get('should_continue', True):
            friendly_response = rewrite_result.get(
                'friendly_response',
                "您好！我是旅游推荐助手，专注于帮您规划旅行。如果您有旅游相关的问题，欢迎随时提问！😊"
            )
            
            return {
                'success': True,
                'answer': friendly_response,
                'sources': [],
                'metadata': {'workflow': 'team_recommend', 'type': 'chitchat'},
                'agent_logs': agent_logs
            }
        
        # 使用重写后的查询
        optimized_query = rewrite_result.get('rewritten_query', query)
        logger.info(f"[Master] Rewritten query: {optimized_query}")
        
        # ========== 继续原有流程 ==========
        # Step 1: RAG检索...
        # Step 2: 图RAG...
        # ...
```

---

## 📋 实施清单

### Phase 1: 创建Query重写器
- [ ] 创建 `query_rewriter.py`
- [ ] 创建 `query_tools.py`（历史记录 + 意图判断工具）
- [ ] 测试Query重写功能

### Phase 2: 更新Master Agent
- [ ] 在Master Agent中集成Query重写器
- [ ] 添加闲聊分支处理
- [ ] 测试完整流程

### Phase 3: 优化所有Prompt
- [ ] 更新RAG助手Prompt
- [ ] 更新图RAG助手Prompt
- [ ] 更新行程规划师Prompt
- [ ] 更新交通助手Prompt
- [ ] 更新美食助手Prompt
- [ ] 更新预算专家Prompt

### Phase 4: 前端适配
- [ ] 添加"查询重写助手"的中文映射
- [ ] 测试闲聊场景显示

---

## 🎯 预期效果

### 场景1：旅游问题
```
用户: "推荐三清山3天旅游攻略"
  ↓
查询重写助手: 是旅游问题，继续
  ↓
RAG检索 → 图RAG → 行程规划 → ...
  ↓
返回：详细的三清山3天攻略
```

### 场景2：上下文问题
```
用户: "三清山怎么样？"
助手: "三清山是..."

用户: "那里怎么去？"
  ↓
查询重写助手: 
  - 获取历史：上一个问题是"三清山"
  - 重写："从出发地到三清山怎么去？"
  ↓
继续流程...
```

### 场景3：闲聊
```
用户: "讲个笑话"
  ↓
查询重写助手: 非旅游问题，直接回复
  ↓
返回："您好！我是旅游推荐助手，专注于帮您规划旅行。
       如果您有旅游相关的问题，欢迎随时提问！😊"
```

---

**准备开始实施吗？我可以逐步帮你完成每个文件！**
