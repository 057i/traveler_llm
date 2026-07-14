# AI团队推荐 - LangChain + Function Calling 详细方案

## 🎯 目标

使用LangChain框架 + 支持function calling的模型（Qwen/GLM），让LLM自主决定何时调用哪些工具。

---

## 📊 架构对比

### 当前架构
```
Master Agent
  ↓ 手动调用
RAG Assistant (BaseSubAgent)
  ↓ execute()
DashScope Generation.call()
  ↓
返回文本
```

### 新架构（方案B）
```
Master Agent
  ↓ 任务分配
RAG Assistant (LangChain Agent)
  ↓ 使用tools
LangChain + Qwen (function calling)
  ↓ 自主决策
调用工具: search_milvus_hybrid()
  ↓
返回结构化结果
```

---

## 🛠️ 技术栈

### 核心依赖
```bash
pip install langchain langchain-community
pip install dashscope  # Qwen API支持function calling
```

### 支持Function Calling的模型
1. **Qwen-Max / Qwen-Plus** - 阿里通义千问（推荐，已有API key）
2. **GLM-4** - 智谱清言
3. **GPT-4** - OpenAI（需要国际网络）

---

## 📝 实施步骤

### Step 1: 定义工具函数（使用@tool装饰器）

**文件：`backend/app/workflows/team_recommend/subagents/rag_tools.py`**

```python
"""
RAG工具定义 - 使用LangChain的@tool装饰器
"""
from langchain.tools import tool
from typing import List, Dict, Any
from loguru import logger
from app.core.milvus_hybrid_client import get_milvus_hybrid_client
from app.utils.ranking import rrf_fusion


@tool
async def search_travel_knowledge(query: str, entities: List[str] = None) -> str:
    """
    从旅游知识库中搜索相关信息
    
    使用Milvus向量数据库进行混合检索（稠密向量+稀疏向量+精确匹配）
    
    Args:
        query: 用户查询，例如"三清山的旅游攻略"
        entities: 实体列表，例如["三清山", "上饶"]
        
    Returns:
        JSON字符串，包含检索到的景点信息
    """
    logger.info(f"[Tool] search_travel_knowledge called: query='{query}', entities={entities}")
    
    try:
        milvus_client = get_milvus_hybrid_client()
        
        # 1. 稠密检索
        dense_results = await milvus_client.search_dense(
            query_text=query,
            top_k=10
        )
        
        # 2. 稀疏检索
        sparse_results = await milvus_client.search_sparse(
            query_text=query,
            top_k=10
        )
        
        # 3. 精确匹配
        exact_results = []
        if entities:
            for entity in entities[:5]:
                matches = await milvus_client.search_exact(
                    entity_name=entity,
                    top_k=3
                )
                exact_results.extend(matches)
        
        # 4. RRF融合
        fused_results = rrf_fusion(
            dense_results,
            sparse_results,
            exact_results,
            k=60
        )
        
        # 5. 质量过滤
        filtered_results = [
            r for r in fused_results
            if r.get('score', 0) >= 0.5
        ]
        
        # 格式化返回
        import json
        result_summary = {
            "found": len(filtered_results),
            "top_results": [
                {
                    "name": r.get('name'),
                    "description": r.get('description', '')[:200],
                    "category": r.get('category'),
                    "score": round(r.get('score', 0), 3)
                }
                for r in filtered_results[:5]
            ]
        }
        
        logger.success(f"[Tool] search_travel_knowledge: found {len(filtered_results)} results")
        
        return json.dumps(result_summary, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Tool] search_travel_knowledge failed: {e}")
        import json
        return json.dumps({"error": str(e), "found": 0}, ensure_ascii=False)


@tool
async def search_nearby_destinations(destination_name: str) -> str:
    """
    查询指定景点附近的其他景点
    
    使用Neo4j知识图谱查询NEARBY_OF关系
    
    Args:
        destination_name: 景点名称，例如"三清山"
        
    Returns:
        JSON字符串，包含附近景点列表
    """
    logger.info(f"[Tool] search_nearby_destinations called: destination='{destination_name}'")
    
    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()
        
        query = """
        MATCH (d1:Destination {name: $name})-[:NEARBY_OF]->(d2:Destination)
        WHERE d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT 5
        """
        
        results = neo4j_client.query(query, {"name": destination_name})
        
        import json
        formatted = {
            "destination": destination_name,
            "nearby_count": len(results),
            "nearby_places": [
                {
                    "name": r.get('name'),
                    "city": r.get('city'),
                    "category": r.get('category'),
                    "description": r.get('description', '')[:150]
                }
                for r in results
            ]
        }
        
        logger.success(f"[Tool] search_nearby_destinations: found {len(results)} nearby places")
        
        return json.dumps(formatted, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Tool] search_nearby_destinations failed: {e}")
        import json
        return json.dumps({"error": str(e), "nearby_count": 0}, ensure_ascii=False)


@tool
async def search_same_city_destinations(destination_name: str) -> str:
    """
    查询与指定景点在同一城市的其他景点
    
    使用Neo4j知识图谱查询LOCATED_IN关系
    
    Args:
        destination_name: 景点名称，例如"三清山"
        
    Returns:
        JSON字符串，包含同城景点列表
    """
    logger.info(f"[Tool] search_same_city_destinations called: destination='{destination_name}'")
    
    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()
        
        query = """
        MATCH (d1:Destination {name: $name})-[:LOCATED_IN]->(c:City)
        MATCH (d2:Destination)-[:LOCATED_IN]->(c)
        WHERE d2.name <> d1.name AND d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT 5
        """
        
        results = neo4j_client.query(query, {"name": destination_name})
        
        import json
        formatted = {
            "destination": destination_name,
            "same_city_count": len(results),
            "same_city_places": [
                {
                    "name": r.get('name'),
                    "city": r.get('city'),
                    "category": r.get('category'),
                    "description": r.get('description', '')[:150]
                }
                for r in results
            ]
        }
        
        logger.success(f"[Tool] search_same_city_destinations: found {len(results)} same city places")
        
        return json.dumps(formatted, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[Tool] search_same_city_destinations failed: {e}")
        import json
        return json.dumps({"error": str(e), "same_city_count": 0}, ensure_ascii=False)
```

---

### Step 2: 创建基于LangChain的子智能体

**文件：`backend/app/workflows/team_recommend/subagents/langchain_base.py`**

```python
"""
LangChain基础Agent - 支持function calling
"""
from typing import List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatTongyi  # Qwen模型
from langchain.tools import BaseTool
from loguru import logger
from config.settings import settings


class LangChainAgent:
    """基于LangChain的智能体基类"""
    
    def __init__(self, name: str, system_prompt: str, tools: List[BaseTool]):
        """
        初始化LangChain Agent
        
        Args:
            name: Agent名称
            system_prompt: 系统提示词
            tools: 工具列表
        """
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        
        # 初始化Qwen模型（支持function calling）
        self.llm = ChatTongyi(
            model_name="qwen-max",  # 或 qwen-plus
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=0.7
        )
        
        # 创建prompt模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # 创建executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
        
        logger.info(f"[{self.name}] LangChain Agent initialized with {len(tools)} tools")
    
    async def execute(self, task: str) -> str:
        """
        执行任务
        
        Args:
            task: 任务描述
            
        Returns:
            执行结果
        """
        logger.info(f"[{self.name}] Executing task: {task[:100]}...")
        
        try:
            result = await self.agent_executor.ainvoke({
                "input": task
            })
            
            output = result.get("output", "")
            logger.success(f"[{self.name}] Task completed")
            
            return output
            
        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}")
            import traceback
            traceback.print_exc()
            raise
```

---

### Step 3: 重构RAG和GraphRAG子智能体

**文件：`backend/app/workflows/team_recommend/subagents/rag_assistant.py`**

```python
"""
RAG Assistant - 基于LangChain + Function Calling
"""
from .langchain_base import LangChainAgent
from .rag_tools import (
    search_travel_knowledge,
    search_nearby_destinations,
    search_same_city_destinations
)
from loguru import logger


class RAGAssistant(LangChainAgent):
    """RAG知识库助手 - 使用LangChain + tools"""
    
    def __init__(self):
        tools = [
            search_travel_knowledge,
            search_nearby_destinations,
            search_same_city_destinations
        ]
        
        system_prompt = """你是一个旅游知识库助手，负责从知识库中检索相关信息。

你有以下工具可用：
1. search_travel_knowledge - 从Milvus向量库搜索旅游信息
2. search_nearby_destinations - 查询景点附近的其他景点
3. search_same_city_destinations - 查询同城的其他景点

**工作流程：**
1. 首先使用 search_travel_knowledge 搜索主要信息
2. 如果用户询问附近景点，使用 search_nearby_destinations
3. 如果用户询问同城景点，使用 search_same_city_destinations

请根据用户查询自主决定调用哪些工具，并整合结果返回。

**返回格式：**
- 如果找到结果，列出景点名称、描述、类别
- 如果没有找到，礼貌告知用户
- 保持回答简洁专业"""
        
        super().__init__(
            name="RAG Knowledge Assistant",
            system_prompt=system_prompt,
            tools=tools
        )
        
        logger.info("[RAG Assistant] Initialized with LangChain + function calling")
```

**文件：`backend/app/workflows/team_recommend/subagents/graph_rag_assistant.py`**

```python
"""
Graph RAG Assistant - 基于LangChain + Function Calling
"""
from .langchain_base import LangChainAgent
from .rag_tools import (
    search_nearby_destinations,
    search_same_city_destinations
)
from loguru import logger


class GraphRAGAssistant(LangChainAgent):
    """图RAG助手 - 使用LangChain + Neo4j tools"""
    
    def __init__(self):
        tools = [
            search_nearby_destinations,
            search_same_city_destinations
        ]
        
        system_prompt = """你是一个知识图谱助手，负责从Neo4j图数据库中查询景点关系。

你有以下工具可用：
1. search_nearby_destinations - 查询附近景点
2. search_same_city_destinations - 查询同城景点

**工作策略：**
- 当用户询问"附近有什么"时，使用 search_nearby_destinations
- 当用户询问"同城推荐"时，使用 search_same_city_destinations
- 可以同时调用多个工具获取全面信息

请自主决定调用哪些工具，并整合结果返回清晰的推荐列表。"""
        
        super().__init__(
            name="Graph RAG Assistant",
            system_prompt=system_prompt,
            tools=tools
        )
        
        logger.info("[Graph RAG Assistant] Initialized with LangChain + function calling")
```

---

### Step 4: 更新Master Agent

**文件：`backend/app/workflows/team_recommend/master_agent.py`**

```python
# 只需要更新调用方式

async def _run_rag_assistant(self, query: str) -> str:
    """执行RAG助手（LangChain自动调用工具）"""
    try:
        # LangChain Agent会自动决定调用哪些工具
        result = await self.rag_assistant.execute(query)
        return result
    except Exception as e:
        logger.error(f"RAG Assistant failed: {e}")
        return ""

async def _run_graph_rag_assistant(self, query: str, context: str = "") -> str:
    """执行图RAG助手（LangChain自动调用工具）"""
    try:
        # 构建任务描述
        task = f"{query}\n\n上下文：{context}" if context else query
        
        # LangChain Agent会自动决定调用哪些工具
        result = await self.graph_rag_assistant.execute(task)
        return result
    except Exception as e:
        logger.error(f"Graph RAG Assistant failed: {e}")
        return ""
```

---

## 📋 依赖安装

```bash
pip install langchain==0.1.0
pip install langchain-community==0.0.20
pip install dashscope  # 已有
```

---

## 🎯 优势

### 1. LLM自主决策
```
用户: "推荐三清山附近的景点"
  ↓
LLM分析: 需要先找到三清山，再查附近景点
  ↓
自动调用: search_travel_knowledge("三清山")
  ↓
得到结果: {"name": "三清山", ...}
  ↓
自动调用: search_nearby_destinations("三清山")
  ↓
整合返回
```

### 2. 工具组合使用
LLM可以根据需要组合调用多个工具

### 3. 容错能力
工具调用失败时，LLM可以尝试其他策略

---

## ⚠️ 注意事项

### 1. API成本
- Function calling调用次数可能增加
- 建议设置 `max_iterations=5` 限制调用次数

### 2. 响应时间
- 工具调用是异步的，但总体可能比直接调用慢
- 建议添加超时控制

### 3. 调试
- 设置 `verbose=True` 查看工具调用日志
- 记录每次function call的参数和结果

---

## 🚀 实施步骤总结

1. [ ] 安装依赖：`langchain`, `langchain-community`
2. [ ] 创建 `rag_tools.py`（定义3个@tool函数）
3. [ ] 创建 `langchain_base.py`（LangChain Agent基类）
4. [ ] 重构 `rag_assistant.py`（继承LangChainAgent）
5. [ ] 重构 `graph_rag_assistant.py`（继承LangChainAgent）
6. [ ] 更新 `master_agent.py`（调用方式）
7. [ ] 测试工具调用
8. [ ] 验证完整流程

---

## 🎉 预期效果

**对话示例：**

```
用户: 推荐三清山的旅游攻略

RAG Assistant:
  [调用] search_travel_knowledge("三清山旅游攻略")
  [调用] search_nearby_destinations("三清山")
  
  → 返回: "三清山位于江西上饶，是道教名山...
          附近景点有：婺源、龟峰、灵山..."

用户: 三清山附近还有什么好玩的？

Graph RAG Assistant:
  [调用] search_nearby_destinations("三清山")
  [调用] search_same_city_destinations("三清山")
  
  → 返回: "附近推荐：婺源古镇、龟峰景区...
          同城推荐：上饶集中营、灵山..."
```

---

**准备开始实施吗？我可以逐步帮你完成每个文件！**
