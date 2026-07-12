# 架构重构方案 - AI推荐系统

## 📋 重构目标

### 当前问题
- AI推荐和AI团队推荐的实现与设计目标相反
- 代码结构混乱，没有清晰的功能分离
- 共用代码重复

### 重构目标
1. **AI推荐** (`/ai-recommend`) - 使用LangGraph线性流程
   - 问题重写（LLM）
   - 多路检索（ChromaDB + Neo4j）
   - RRF融合
   - Rerank精排
   - 置信度判断
   - Tavily搜索（低置信度时）
   - LLM润色返回

2. **AI团队推荐** (`/ai-team-recommend`) - 使用create_react_agent多智能体
   - 主智能体（Orchestrator）
   - 子智能体（带tools）:
     - RAG工具智能体
     - GraphRAG工具智能体
     - 搜索工具智能体
   - 结果汇总

3. **架构规范** - 符合MVC模式
   - 清晰的文件夹结构
   - 共用功能抽离到utils
   - 职责分离

---

## 🏗️ 新的文件夹结构

```
backend/
├── app/
│   ├── api/                          # Controller层
│   │   ├── ai_recommend.py          # AI推荐API
│   │   ├── ai_team_recommend.py     # AI团队推荐API
│   │   ├── rag.py                   # RAG管理API
│   │   └── ...
│   │
│   ├── services/                     # Service层（业务逻辑）
│   │   ├── ai_recommend/            # AI推荐服务
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # 主服务类
│   │   │   ├── query_rewriter.py    # 问题重写
│   │   │   ├── retriever.py         # 多路检索
│   │   │   ├── ranker.py            # RRF+Rerank
│   │   │   ├── confidence.py        # 置信度判断
│   │   │   └── synthesizer.py       # 结果润色
│   │   │
│   │   ├── ai_team_recommend/       # AI团队推荐服务
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # 主服务类
│   │   │   ├── orchestrator.py      # 主智能体
│   │   │   ├── agents/              # 子智能体
│   │   │   │   ├── rag_agent.py
│   │   │   │   ├── graph_rag_agent.py
│   │   │   │   └── search_agent.py
│   │   │   └── tools/               # 智能体工具
│   │   │       ├── rag_tools.py
│   │   │       ├── graph_tools.py
│   │   │       └── search_tools.py
│   │   │
│   │   └── base_service.py          # 基础服务类
│   │
│   ├── workflows/                    # Workflow层（LangGraph工作流）
│   │   ├── ai_recommend/
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py     # 图构建器
│   │   │   ├── nodes.py             # 节点定义
│   │   │   └── state.py             # 状态定义
│   │   │
│   │   └── ai_team_recommend/
│   │       ├── __init__.py
│   │       └── multi_agent.py       # 多智能体编排
│   │
│   ├── core/                         # 核心引擎（Model层）
│   │   ├── rag_engine.py            # RAG引擎
│   │   ├── graph_engine.py          # Graph引擎
│   │   ├── llm_engine.py            # LLM引擎
│   │   └── health_check.py          # 健康检查
│   │
│   ├── utils/                        # 工具函数（共用）
│   │   ├── __init__.py
│   │   ├── retrieval/               # 检索相关
│   │   │   ├── chromadb_client.py
│   │   │   ├── neo4j_client.py
│   │   │   └── tavily_client.py
│   │   ├── ranking/                 # 排序相关
│   │   │   ├── rrf_fusion.py
│   │   │   └── rerank.py
│   │   ├── llm/                     # LLM相关
│   │   │   ├── qwen_client.py
│   │   │   └── prompt_templates.py
│   │   └── text/                    # 文本处理
│   │       ├── cleaner.py
│   │       └── splitter.py
│   │
│   └── models/                       # 数据模型
│       ├── schemas.py               # API模型
│       └── domain.py                # 领域模型
│
├── config/
│   └── settings.py                  # 配置
│
└── main.py                          # 应用入口
```

---

## 🔄 重构步骤

### Phase 1: 创建新架构（不破坏现有功能）
1. ✅ 创建新的文件夹结构
2. ✅ 实现AI推荐的LangGraph线性流程
3. ✅ 实现AI团队推荐的多智能体模式
4. ✅ 抽离共用功能到utils

### Phase 2: 迁移和测试
5. ✅ 更新API路由指向新服务
6. ✅ 测试两个功能
7. ✅ 清理旧代码

### Phase 3: 优化和文档
8. ✅ 代码优化
9. ✅ 添加日志
10. ✅ 更新文档

---

## 📝 详细设计

### 1. AI推荐 - LangGraph线性流程

```python
# app/workflows/ai_recommend/graph_builder.py

from langgraph.graph import StateGraph, END

class AIRecommendGraph:
    """AI推荐工作流图"""
    
    def __init__(self):
        self.graph = StateGraph(AIRecommendState)
    
    def build(self):
        """构建线性工作流"""
        # 添加节点
        self.graph.add_node("query_rewriter", query_rewriter_node)
        self.graph.add_node("retriever", retriever_node)
        self.graph.add_node("rrf_fusion", rrf_fusion_node)
        self.graph.add_node("rerank", rerank_node)
        self.graph.add_node("confidence_check", confidence_check_node)
        self.graph.add_node("tavily_search", tavily_search_node)
        self.graph.add_node("synthesizer", synthesizer_node)
        
        # 设置入口
        self.graph.set_entry_point("query_rewriter")
        
        # 线性流程
        self.graph.add_edge("query_rewriter", "retriever")
        self.graph.add_edge("retriever", "rrf_fusion")
        self.graph.add_edge("rrf_fusion", "rerank")
        self.graph.add_edge("rerank", "confidence_check")
        
        # 条件分支：置信度判断
        self.graph.add_conditional_edges(
            "confidence_check",
            self._route_by_confidence,
            {
                "high": "synthesizer",      # 高置信度直接润色
                "low": "tavily_search"      # 低置信度补充搜索
            }
        )
        
        self.graph.add_edge("tavily_search", "synthesizer")
        self.graph.add_edge("synthesizer", END)
        
        return self.graph.compile()
```

#### 节点功能：

1. **query_rewriter_node**: 使用LLM重写问题
2. **retriever_node**: 并行检索ChromaDB和Neo4j
3. **rrf_fusion_node**: RRF算法融合结果
4. **rerank_node**: Rerank模型精排
5. **confidence_check_node**: 判断结果置信度
6. **tavily_search_node**: Tavily补充搜索（低置信度时）
7. **synthesizer_node**: LLM润色最终结果

---

### 2. AI团队推荐 - create_react_agent多智能体

```python
# app/workflows/ai_team_recommend/multi_agent.py

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

class AITeamRecommendWorkflow:
    """AI团队推荐 - 多智能体工作流"""
    
    def __init__(self):
        self.llm = get_llm()
        self.tools = self._create_tools()
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            state_modifier=self._get_system_prompt()
        )
    
    def _create_tools(self):
        """创建工具"""
        return [
            rag_search_tool,
            graph_rag_search_tool,
            tavily_search_tool,
            trip_planner_tool,
            budget_advisor_tool
        ]
    
    def _get_system_prompt(self):
        """系统提示词"""
        return """你是一个旅行推荐助手团队的协调者。
        
你可以调用以下工具：
- rag_search_tool: 从向量数据库检索相关信息
- graph_rag_search_tool: 从知识图谱检索关系信息
- tavily_search_tool: 从互联网搜索最新信息
- trip_planner_tool: 规划详细行程
- budget_advisor_tool: 提供预算建议

请根据用户问题，智能地选择和组合这些工具来提供最佳推荐。"""
```

#### 工具定义：

```python
@tool
def rag_search_tool(query: str) -> str:
    """从向量数据库检索旅游信息"""
    results = chroma_client.search(query)
    return format_results(results)

@tool
def graph_rag_search_tool(query: str) -> str:
    """从知识图谱检索相关实体和关系"""
    results = neo4j_client.search(query)
    return format_graph_results(results)

@tool
def tavily_search_tool(query: str) -> str:
    """从互联网搜索最新旅游信息"""
    results = tavily_client.search(query)
    return format_search_results(results)
```

---

### 3. 共用功能抽离

#### utils/retrieval/chromadb_client.py
```python
class ChromaDBClient:
    """ChromaDB客户端（单例）"""
    
    def search(self, query: str, top_k: int = 10):
        """检索"""
        pass
```

#### utils/ranking/rrf_fusion.py
```python
def rrf_fusion(results_list: List[List], k: int = 60):
    """RRF融合算法"""
    pass
```

#### utils/ranking/rerank.py
```python
def rerank(query: str, documents: List[str], top_k: int = 5):
    """Rerank精排"""
    pass
```

---

## 🎯 实现优先级

1. **Phase 1** (高优先级)
   - 创建文件夹结构
   - 实现AI推荐的LangGraph线性流程
   - 测试AI推荐功能

2. **Phase 2** (中优先级)
   - 实现AI团队推荐的多智能体模式
   - 测试AI团队推荐功能

3. **Phase 3** (低优先级)
   - 抽离共用代码
   - 清理旧代码
   - 优化性能

---

## ✅ 验收标准

### AI推荐验收
- [ ] 问题能被LLM正确重写
- [ ] ChromaDB和Neo4j并行检索
- [ ] RRF正确融合结果
- [ ] Rerank正确精排
- [ ] 置信度判断准确
- [ ] 低置信度时调用Tavily
- [ ] 最终结果经过LLM润色
- [ ] SSE流式返回

### AI团队推荐验收
- [ ] 使用create_react_agent
- [ ] 主智能体能正确分析需求
- [ ] 能调用RAG工具
- [ ] 能调用GraphRAG工具
- [ ] 能调用搜索工具
- [ ] 工具调用结果正确汇总
- [ ] WebSocket正常返回

---

开始重构？
