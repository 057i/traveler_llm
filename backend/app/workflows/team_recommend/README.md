# AI团队推荐 - 多智能体协作系统

## 🎯 系统概述

AI团队推荐是一个基于多智能体协作的智能旅游推荐系统。通过**1个主智能体**协调**6个专业子智能体**，提供全面、专业的旅游规划服务。

---

## 🤖 智能体架构

### 主智能体（协调者）
- **名称**: MasterAgent
- **职责**: 协调所有子智能体，不负责具体逻辑
- **功能**:
  1. 判断是否是旅游相关问题
  2. 决定调用哪些子智能体
  3. 整合所有子智能体的结果
  4. 生成最终答案

### 子智能体（6个专业助手）

#### 1. RAG知识库助手
- **文件**: `subagents/rag_assistant.py`
- **职责**: 从Milvus向量数据库检索景点信息
- **返回**: 景点列表、相关度分数、是否需要规划

#### 2. 图RAG知识库助手
- **文件**: `subagents/graph_rag_assistant.py`
- **职责**: 从Neo4j图数据库检索附近景点和关联信息
- **返回**: 附近景点、关系类型、距离信息

#### 3. 行程规划师
- **文件**: `subagents/itinerary_planner.py`
- **职责**: 制定详细的旅游行程计划
- **返回**: 每日行程、时间分配、游玩建议

#### 4. 省钱达人
- **文件**: `subagents/budget_expert.py`
- **职责**: 提供预算规划和省钱建议
- **返回**: 费用估算、省钱技巧、避坑提醒

#### 5. 交通助手
- **文件**: `subagents/transport_assistant.py`
- **职责**: 规划城际和市内交通方案
- **返回**: 交通方式、路线规划、费用估算

#### 6. 美食助手
- **文件**: `subagents/food_assistant.py`
- **职责**: 推荐当地特色美食和餐厅
- **返回**: 美食清单、餐厅推荐、用餐建议

---

## 🔄 工作流程

```
用户查询 + 历史对话
    ↓
[主智能体] 判断是否旅游相关？
    ├─ 否 → 返回提示信息 ❌
    └─ 是 → 继续 ✅
    ↓
[步骤1] 调用RAG知识库助手
    ↓
[判断] 检索结果是否充足？
    ├─ 是（score >= 0.7）→ 调用图RAG助手 → 生成答案 ✅
    └─ 否（score < 0.5）→ 继续
    ↓
[步骤2] 调用行程规划师
    ↓
[步骤3] 调用交通助手
    ↓
[步骤4] 调用美食助手
    ↓
[步骤5] 整合所有结果 → 生成最终答案 ✅
```

---

## 📁 目录结构

```
app/workflows/team_recommend/
├── __init__.py
├── master_agent.py              # 主智能体（协调者）
├── team_manager.py              # 团队管理器
├── service.py                   # 服务入口
├── schemas.py                   # 数据模型
├── README.md                    # 文档
└── subagents/                   # 子智能体目录
    ├── __init__.py
    ├── base.py                  # 基础智能体类
    ├── rag_assistant.py         # RAG知识库助手
    ├── graph_rag_assistant.py   # 图RAG知识库助手
    ├── itinerary_planner.py     # 行程规划师
    ├── budget_expert.py         # 省钱达人
    ├── transport_assistant.py   # 交通助手
    └── food_assistant.py        # 美食助手
```

---

## 🚀 API使用

### 1. 非流式请求

**端点**: `POST /team-recommend/`

**请求体**:
```json
{
  "query": "推荐三清山3天旅游攻略",
  "session_id": "optional-session-id",
  "chat_history": [
    {
      "role": "user",
      "content": "我想去江西旅游"
    },
    {
      "role": "assistant",
      "content": "江西有很多著名景点..."
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "answer": "# 三清山3天旅游攻略\n\n一、行程概述...",
  "sources": [
    {
      "name": "三清山",
      "location": "江西省上饶市",
      "description": "...",
      "score": 0.85
    }
  ],
  "metadata": {
    "workflow": "full_planning",
    "agents_used": ["RAG助手", "行程规划师", "交通助手", "美食助手"]
  }
}
```

### 2. 流式请求（SSE）

**端点**: `POST /team-recommend/stream`

**SSE事件流**:
```
data: {"type": "start", "message": "🤖 AI团队启动中..."}

data: {"type": "progress", "message": "🔍 主智能体正在协调子智能体..."}

data: {"type": "answer", "answer": "...", "sources": [...]}

data: {"type": "complete", "message": "✅ 团队推荐完成"}
```

---

## 💡 核心特性

### 1. 智能判断
- ✅ 自动判断是否旅游相关问题
- ✅ 支持历史对话理解
- ✅ 非旅游问题友好提示

### 2. 分数阈值策略
- ✅ **高分（≥0.7）**: 只用知识库，快速返回
- ✅ **中低分（<0.5）**: 调用规划师，完整规划
- ✅ 动态决策，节省成本

### 3. 专业分工
- ✅ 每个子智能体专注自己的领域
- ✅ 主智能体只负责协调
- ✅ 结果整合统一输出

### 4. 历史对话支持
- ✅ 支持多轮对话
- ✅ 上下文理解
- ✅ 指代词消解

---

## 🎯 两种工作模式

### 模式1: 知识库模式（快速）
**触发条件**: RAG检索分数 ≥ 0.7

**流程**:
```
RAG助手 → 图RAG助手 → 生成答案
```

**特点**:
- ⚡ 快速（约5秒）
- 💰 成本低（2个子智能体）
- 📊 适合常见景点查询

### 模式2: 完整规划模式（全面）
**触发条件**: RAG检索分数 < 0.5

**流程**:
```
RAG助手 → 行程规划师 → 交通助手 → 美食助手 → 整合
```

**特点**:
- 🔍 全面（4个专业子智能体）
- 📝 详细（行程、交通、美食）
- 🎯 适合复杂规划需求

---

## 📊 与单智能体对比

| 特性 | AI推荐（LangGraph） | AI团队推荐（多智能体） |
|------|-------------------|---------------------|
| 智能体数量 | 1个 | 1主 + 6子 |
| 协作方式 | 工作流编排 | 主智能体协调 |
| 专业度 | 基础 | 专业分工 |
| 规划深度 | 中等 | 深度规划 |
| 响应时间 | 快（5-8秒） | 中等（5-15秒） |
| 适用场景 | 快速推荐 | 详细规划 |
| 历史对话 | ✅ 支持 | ✅ 支持 |
| 知识库 | Milvus | Milvus + Neo4j |

---

## 🧪 测试示例

### Python测试
```python
import requests

# 非流式请求
response = requests.post(
    "http://localhost:8000/team-recommend/",
    json={
        "query": "推荐三清山3天旅游攻略",
        "chat_history": [
            {"role": "user", "content": "我想去江西旅游"},
            {"role": "assistant", "content": "江西有很多著名景点..."}
        ]
    }
)

result = response.json()
print(result['answer'])
```

### 流式测试
```python
import requests

with requests.post(
    "http://localhost:8000/team-recommend/stream",
    json={"query": "推荐三清山旅游攻略"},
    stream=True
) as response:
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
```

---

## ⚙️ 配置

所有智能体使用统一的LLM配置（从`settings.py`读取）：
- **模型**: `QWEN_MODEL_NAME`
- **API Key**: `DASHSCOPE_API_KEY`

---

## 🎯 优势总结

1. ✅ **专业分工** - 6个子智能体各司其职
2. ✅ **智能协调** - 主智能体动态决策
3. ✅ **分数阈值** - 快速/详细两种模式
4. ✅ **历史支持** - 多轮对话理解
5. ✅ **全面规划** - 行程、交通、美食一站式
6. ✅ **知识库优先** - 充分利用已有数据
7. ✅ **易于扩展** - 新增子智能体简单

---

## 📝 开发者注意

### 添加新的子智能体
1. 在 `subagents/` 下创建新文件
2. 继承 `BaseSubAgent` 类
3. 实现 `execute()` 方法
4. 在 `master_agent.py` 中初始化和调用

### 修改协调逻辑
在 `master_agent.py` 的 `coordinate()` 方法中修改

### 调整分数阈值
在 `master_agent.py` 中修改：
- 高分阈值: `max_score >= 0.7`
- 低分阈值: `max_score < 0.5`

---

**创建时间**: 2026-07-11  
**版本**: 2.0.0（多智能体协作版）  
**状态**: ✅ 已完成
