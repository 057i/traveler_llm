# 后端架构说明

## 📁 目录结构（优化后）

```
backend/
├── app/
│   ├── api/                    # API路由层（按前端页面组织）
│   │   ├── sse.py             # AI推荐 - SSE接口（对应前端 /chat）
│   │   ├── websocket.py       # AI团队推荐 - WebSocket接口（对应前端 /websocket）
│   │   ├── rrf.py             # RRF融合推荐（对应前端 /rrf）
│   │   ├── documents.py       # 文档管理（对应前端 /documents）
│   │   └── ...
│   │
│   ├── services/              # 业务逻辑层（新增）
│   │   ├── base_service.py              # 基础服务类 - 提供公共方法
│   │   ├── ai_recommend_service.py      # AI推荐服务 - 多智能体工作流
│   │   ├── ai_team_recommend_service.py # AI团队推荐服务 - 传统RAG流程
│   │   ├── rrf_recommend_service.py     # RRF融合推荐服务
│   │   └── __init__.py
│   │
│   ├── core/                  # 核心引擎层
│   │   ├── rag_engine.py      # RAG检索引擎
│   │   ├── graph_engine.py    # GraphRAG引擎
│   │   ├── rrf_engine.py      # RRF融合引擎
│   │   ├── rerank_engine.py   # Rerank重排序引擎
│   │   └── ...
│   │
│   ├── agents/                # 多智能体系统
│   │   ├── roles/             # 智能体角色
│   │   ├── tools/             # 智能体工具
│   │   ├── state.py           # 状态定义
│   │   └── graph_builder.py   # 工作流图构建器
│   │
│   ├── workflows/             # 工作流编排
│   │   ├── multi_agent_sse.py        # SSE多智能体工作流
│   │   ├── multi_agent_websocket.py  # WebSocket多智能体工作流
│   │   └── document_processing/      # 文档处理工作流
│   │
│   ├── models/                # 数据模型
│   │   └── schemas.py
│   │
│   └── utils/                 # 工具函数
│
├── config/                    # 配置
└── main.py                    # 应用入口
```

## 🎯 架构设计原则

### 1. 按前端页面组织
后端服务层按照前端页面功能进行组织，清晰对应：
- `/chat` → `AIRecommendService` (多智能体工作流)
- `/websocket` → `AITeamRecommendService` (传统RAG)
- `/rrf` → `RRFRecommendService` (RRF融合)
- `/documents` → 文档处理服务

### 2. 三层架构

#### API层 (`app/api/`)
- 处理HTTP请求/WebSocket连接
- 参数验证
- 响应格式化
- 调用服务层

#### 服务层 (`app/services/`) **[新增]**
- 业务逻辑封装
- 编排核心引擎
- 流程控制
- 公共方法抽离

#### 核心层 (`app/core/`)
- RAG检索
- 图谱查询
- 结果融合
- 重排序等底层能力

### 3. 公共方法抽离

#### BaseRecommendService (基础服务类)
提供所有推荐服务的公共方法：
- `build_query_text()` - 构建查询文本
- `search_rag()` - RAG检索
- `search_graph_rag()` - GraphRAG检索
- `fuse_results()` - RRF融合
- `rerank_results()` - Rerank重排序
- `traditional_rag_pipeline()` - 完整RAG流程

#### StreamMessageBuilder (流式消息构建器)
统一的流式消息格式：
- `build_start_message()` - 开始消息
- `build_progress_message()` - 进度消息
- `build_agent_start_message()` - 智能体开始
- `build_stream_message()` - 流式内容
- `build_complete_message()` - 完成消息
- `build_error_message()` - 错误消息

## 📊 服务对应关系

| 前端页面 | 路由 | 服务类 | 技术方案 |
|---------|------|--------|----------|
| AI推荐 | `/chat` | `AIRecommendService` | LangGraph多智能体工作流 |
| AI团队推荐 | `/websocket` | `AITeamRecommendService` | RAG→GraphRAG→RRF→Rerank |
| RRF融合推荐 | `/rrf` | `RRFRecommendService` | RRF融合+详细信息 |
| 文档管理 | `/documents` | 文档处理工作流 | PDF处理+向量化 |

## 🔄 调用流程示例

### AI推荐（多智能体）
```
前端 /chat → API /api/sse/recommend → AIRecommendService
                                         ↓
                                    MultiAgentSSEWorkflow
                                         ↓
                                    LangGraph智能体图
```

### AI团队推荐（传统RAG）
```
前端 /websocket → API /ws/chat → AITeamRecommendService
                                      ↓
                                  BaseRecommendService
                                      ↓
                        RAG → GraphRAG → RRF → Rerank
```

## ✨ 优化效果

### 1. 代码复用
- 公共方法只需维护一份
- 所有服务继承自`BaseRecommendService`
- 统一的消息格式构建

### 2. 易于维护
- 按功能模块清晰分层
- 服务层与核心层解耦
- 单一职责原则

### 3. 易于扩展
- 新增推荐服务只需继承基类
- 新增API端点调用对应服务即可
- 核心引擎独立升级

### 4. 清晰的对应关系
- 前端页面 → 后端服务 一一对应
- 便于理解和协作开发

## 🚀 使用示例

### 创建新的推荐服务
```python
from app.services.base_service import BaseRecommendService

class MyRecommendService(BaseRecommendService):
    """自定义推荐服务"""
    
    async def recommend(self, query_request):
        # 使用基类提供的公共方法
        rag_results = await self.search_rag(query_request)
        graph_results = await self.search_graph_rag(query_request)
        
        # 自定义业务逻辑
        ...
        
        return results
```

### 在API中使用服务
```python
from app.services import AIRecommendService

@router.post("/recommend")
async def recommend(query_request: QueryRequest):
    service = AIRecommendService()
    return await service.recommend_stream(query_request)
```
