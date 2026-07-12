# 📊 API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`

## 接口列表

### 1. RAG 推荐接口

#### 1.1 RAG 检索

**接口**: `GET /api/rag/search`

**描述**: 基于传统 RAG 向量检索推荐景点

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 用户查询 |
| budget | integer | 否 | 预算（元） |
| season | string | 否 | 季节：春季/夏季/秋季/冬季 |
| travel_type | string | 否 | 旅行类型：家庭/情侣/朋友/独自/商务 |
| duration | integer | 否 | 旅行天数 |
| interests | string | 否 | 兴趣爱好，逗号分隔 |
| top_k | integer | 否 | 返回结果数量，默认 5 |

**示例请求**:

```bash
GET /api/rag/search?query=适合家庭旅游的海边城市&budget=5000&season=夏季&travel_type=家庭&top_k=5
```

**响应示例**:

```json
{
  "status": "success",
  "results": [
    {
      "name": "三亚",
      "score": 0.92,
      "reason": "与您的需求高度匹配，评分高达4.8分",
      "destination": {
        "name": "三亚",
        "location": "海南省",
        "description": "中国最南端的热带海滨旅游城市...",
        "tags": ["海边", "热带", "度假"],
        "best_season": ["冬季", "春季"],
        "budget_range": [3000, 8000],
        "suitable_for": ["家庭", "情侣", "朋友"],
        "features": ["亚龙湾", "天涯海角"],
        "rating": 4.8
      },
      "source": "rag"
    }
  ],
  "metadata": {
    "query": "适合家庭旅游的海边城市",
    "total_results": 5,
    "method": "traditional_rag"
  }
}
```

#### 1.2 获取 RAG 统计信息

**接口**: `GET /api/rag/stats`

**响应示例**:

```json
{
  "status": "success",
  "stats": {
    "collection_name": "travel_destinations",
    "total_documents": 12,
    "persist_directory": "./data/vector_store"
  }
}
```

---

### 2. GraphRAG 推荐接口

#### 2.1 GraphRAG 检索

**接口**: `GET /api/graph_rag/search`

**描述**: 基于图结构推理推荐景点

**请求参数**: 同 RAG 检索接口

**响应示例**:

```json
{
  "status": "success",
  "results": [...],
  "graph_data": null,
  "metadata": {
    "query": "适合家庭旅游的海边城市",
    "total_results": 5,
    "method": "graph_rag"
  }
}
```

#### 2.2 获取图统计信息

**接口**: `GET /api/graph_rag/stats`

**响应示例**:

```json
{
  "status": "success",
  "stats": {
    "destinations": 12,
    "seasons": 4,
    "tags": 30,
    "relationships": 150
  }
}
```

---

### 3. RRF 融合推荐接口

#### 3.1 RRF 融合

**接口**: `POST /api/rrf/fuse`

**描述**: 融合多个模型的推荐结果

**请求体**:

```json
{
  "query": {
    "query": "适合家庭旅游的海边城市",
    "budget": 5000,
    "season": "夏季",
    "travel_type": "家庭",
    "duration": 3,
    "interests": ["自然", "摄影"]
  },
  "models": ["rag", "graph_rag"],
  "weights": {
    "rag": 0.5,
    "graph_rag": 0.5
  }
}
```

**响应示例**:

```json
{
  "status": "success",
  "results": [...],
  "individual_results": {
    "rag": [...],
    "graph_rag": [...]
  },
  "metadata": {
    "models_used": ["rag", "graph_rag"],
    "total_results": 5,
    "method": "rrf_fusion"
  }
}
```

#### 3.2 RRF 多样性融合

**接口**: `POST /api/rrf/fuse_with_diversity`

**描述**: 融合推荐结果并进行多样性优化

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| alpha | float | 否 | 相关性与多样性权衡，默认 0.7 |
| top_k | integer | 否 | 返回结果数量，默认 5 |

**响应示例**:

```json
{
  "status": "success",
  "results": [...],
  "individual_results": {...},
  "metadata": {
    "models_used": ["rag", "graph_rag"],
    "total_results": 5,
    "method": "rrf_fusion_with_diversity",
    "diversity_score": 0.75,
    "alpha": 0.7
  }
}
```

---

### 4. Rerank 重排序接口

#### 4.1 基础重排序

**接口**: `POST /api/rerank/rerank`

**描述**: 使用 LLM 对候选结果进行智能重排序

**请求体**:

```json
{
  "query": {
    "query": "适合家庭旅游的海边城市",
    "budget": 5000,
    "season": "夏季",
    "travel_type": "家庭"
  },
  "candidates": [...],
  "top_n": 3
}
```

**响应示例**:

```json
{
  "status": "success",
  "results": [...],
  "metadata": {
    "query": "适合家庭旅游的海边城市",
    "total_results": 3,
    "method": "llm_rerank"
  }
}
```

#### 4.2 重排序（带详细解释）

**接口**: `POST /api/rerank/rerank_with_explanation`

**描述**: 重排序并生成详细推荐理由

**请求体**: 同基础重排序

**响应示例**:

```json
{
  "status": "success",
  "results": [
    {
      "name": "三亚",
      "score": 1.0,
      "reason": "三亚最适合家庭旅游，拥有优质海滩和完善的亲子设施，夏季可以享受清凉的海水...",
      "destination": {...},
      "source": "rrf(rag, graph_rag)+rerank"
    }
  ],
  "metadata": {...}
}
```

---

### 5. SSE 实时推荐接口

#### 5.1 SSE 推荐流

**接口**: `GET /api/sse/recommend`

**描述**: 通过 Server-Sent Events 实时推送推荐进度

**请求参数**: 同 RAG 检索接口

**响应格式**: `text/event-stream`

**事件类型**:

1. **start** - 推荐开始
2. **progress** - 处理进度
3. **step_complete** - 步骤完成
4. **recommendation** - 推荐结果
5. **complete** - 推荐完成
6. **error** - 错误信息

**示例事件流**:

```
data: {"type":"start","message":"开始推荐流程"}

data: {"type":"progress","step":"rag","message":"正在进行传统 RAG 检索..."}

data: {"type":"step_complete","step":"rag","count":5}

data: {"type":"recommendation","index":1,"total":5,"name":"三亚",...}

data: {"type":"complete","message":"推荐完成，共找到 5 个景点"}
```

---

### 6. WebSocket 对话接口

#### 6.1 WebSocket 连接

**接口**: `ws://localhost:8000/ws/chat`

**描述**: 建立 WebSocket 连接进行多轮对话推荐

**发送消息格式**:

```json
{
  "message": "推荐适合家庭旅游的海边城市",
  "preferences": {
    "budget": 5000,
    "season": "夏季",
    "travel_type": "家庭"
  }
}
```

**接收消息类型**:

1. **system** - 系统消息
2. **status** - 状态更新
3. **progress** - 处理进度
4. **result** - 推荐结果
5. **suggestion** - 建议问题
6. **error** - 错误信息

**示例接收消息**:

```json
{
  "type": "result",
  "message": "为您找到 5 个推荐景点",
  "recommendations": [...],
  "metadata": {
    "rag_count": 5,
    "graph_rag_count": 4,
    "fused_count": 6
  }
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 使用示例

### Python 示例

```python
import requests

# RAG 检索
response = requests.get(
    "http://localhost:8000/api/rag/search",
    params={
        "query": "适合家庭旅游的海边城市",
        "budget": 5000,
        "season": "夏季",
        "top_k": 5
    }
)
print(response.json())

# RRF 融合
response = requests.post(
    "http://localhost:8000/api/rrf/fuse",
    json={
        "query": {
            "query": "适合家庭旅游的海边城市",
            "budget": 5000
        },
        "models": ["rag", "graph_rag"]
    }
)
print(response.json())
```

### JavaScript 示例

```javascript
// RAG 检索
const response = await fetch(
  'http://localhost:8000/api/rag/search?query=适合家庭旅游的海边城市&budget=5000'
);
const data = await response.json();
console.log(data);

// SSE 连接
const eventSource = new EventSource(
  'http://localhost:8000/api/sse/recommend?query=适合家庭旅游的海边城市'
);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

// WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/ws/chat');
ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "推荐适合家庭旅游的海边城市"
  }));
};
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

更多详细信息请访问 Swagger UI: http://localhost:8000/docs
