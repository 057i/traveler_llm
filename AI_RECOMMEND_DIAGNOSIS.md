# 🔍 AI推荐前后端问题诊断报告

## 🎯 核心问题发现

### **问题1: 使用了错误的API端点**

前端可能在使用**旧的**`/api/ai-recommend/recommend`端点，而不是**新的**`/api/ai-recommend/query` + `/api/ai-recommend/events`组合。

---

## 📊 API架构分析

### **发现：有3个不同的推荐端点**

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/recommend` (旧) | POST+SSE | 旧版同步流式 | 🟡 可能过时 |
| `/query` (新) | POST | 启动工作流 | ✅ 推荐使用 |
| `/events/{session_id}` (新) | GET+SSE | 订阅事件流 | ✅ 推荐使用 |

---

## 🔄 两种架构对比

### **架构A: 旧版 (单一端点)**

```
前端 → POST /recommend
  ↓
后端: service.process_stream()
  ↓ (同步流式返回)
前端接收SSE事件
```

**特点**:
- 单一请求
- 同步流式
- 简单但可能阻塞

### **架构B: 新版 (分离端点)** ✅ 推荐

```
前端 → POST /query (启动工作流)
  ↓
后端: service.process_query_async()
  ↓ (后台异步执行)
  ↓ (通过Redis Pub/Sub发送事件)
  
前端 → GET /events/{session_id} (订阅事件)
  ↓
后端: 从Redis订阅事件
  ↓
前端接收SSE事件
```

**特点**:
- 异步非阻塞
- 更好的性能
- 分离关注点

---

## 🐛 发现的具体问题

### **1. service.py发送了final_answer事件，但process_stream没有处理**

**修改位置**: `service.py`的`process_query_async()`
```python
# 发送final_answer事件
await redis_client.publish(
    f"ai_recommend:{session_id}",
    json.dumps({
        "event_type": "final_answer",  # ← 使用event_type
        "answer": final_answer,
        "sources": sources
    })
)
```

**问题**: 
- 如果前端使用`/recommend`端点，这个事件不会被处理！
- `process_stream()`方法没有final_answer的处理逻辑

### **2. 事件字段名不一致**

**SSE工具发送**: `event_type`
```python
# app/utils/sse_utils.py
{
    "event_type": "node_start",
    "step": "rewrite",
    ...
}
```

**前端期望**: `type`
```javascript
// frontend
case 'final_answer':
  // 处理
```

---

## ✅ 解决方案

### **方案1: 确保前端使用新架构** (推荐)

#### **前端代码应该是**:

```javascript
// 1. 发起查询请求
const response = await axios.post('/api/ai-recommend/query', {
  query: userInput,
  session_id: sessionId
})

// 2. 订阅事件流
const eventSource = new EventSource(`/api/ai-recommend/events/${sessionId}`)

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data)
  
  // 处理不同事件
  switch (data.event_type) {
    case 'node_start':
      // 显示节点开始
      break
    case 'node_end':
      // 显示节点完成
      break
    case 'final_answer':
      // 显示LLM生成的答案
      displayAnswer(data.answer, data.sources)
      break
    case 'complete':
      // 完成
      break
  }
})
```

### **方案2: 统一事件字段名**

修改SSE工具，使用`type`而不是`event_type`:

```python
# app/utils/sse_utils.py

# 修改前
{
    "event_type": "node_start",
    ...
}

# 修改后
{
    "type": "node_start",  # ← 改为type
    ...
}
```

### **方案3: 在/events端点转换字段名**

```python
# app/api/ai_recommend.py的/events端点

async def event_generator():
    async with pubsub.subscribe(channel) as subscriber:
        async for message in subscriber:
            data = json.loads(message)
            
            # 转换event_type → type
            if 'event_type' in data:
                data['type'] = data.pop('event_type')
            
            yield f"data: {json.dumps(data)}\n\n"
```

---

## 🔧 推荐修复步骤

### **步骤1: 检查前端使用的端点**

```bash
# 在前端代码中搜索
grep -r "ai-recommend" frontend/src/
```

**查找**:
- 是否使用`/recommend`? → 需要改为`/query` + `/events`
- 是否使用`/query` + `/events`? → 正确

### **步骤2: 统一事件字段名为type**

修改`app/utils/sse_utils.py`:

```python
def send_node_start(...):
    data = {
        "type": "node_start",  # ← 使用type
        "step": step_id,
        ...
    }

def send_node_end(...):
    data = {
        "type": "node_end",  # ← 使用type
        ...
    }

# 等等...
```

### **步骤3: 修改/events端点确保发送final_answer**

在`ai_recommend.py`的`/events`端点中添加日志：

```python
@router.get("/events/{session_id}")
async def ai_recommend_events(session_id: str):
    async def event_generator():
        async for message in subscriber:
            data = json.loads(message)
            logger.info(f"[Events] Sending event: {data.get('event_type')}")  # 添加日志
            
            # 转换字段名
            if 'event_type' in data:
                data['type'] = data.pop('event_type')
            
            yield f"event: message\ndata: {json.dumps(data)}\n\n"
```

---

## 🧪 测试检查清单

### **后端测试**

```bash
# 1. 启动后端
python main.py

# 2. 测试query端点
curl -X POST http://localhost:8000/api/ai-recommend/query \
  -H "Content-Type: application/json" \
  -d '{"query": "推荐三清山", "session_id": "test123"}'

# 应该返回:
{
  "status": "started",
  "session_id": "test123",
  "message": "AI推荐工作流已启动"
}

# 3. 测试events端点
curl http://localhost:8000/api/ai-recommend/events/test123

# 应该接收到SSE事件流
```

### **前端测试**

1. 打开浏览器控制台
2. 查看Network标签
3. 发起查询
4. 检查：
   - 是否有POST到`/query`?
   - 是否有GET到`/events/{session_id}`?
   - Events标签下是否收到SSE事件?
   - 是否收到`final_answer`事件?

---

## 📋 检查要点

### **必须检查**:

1. ✅ 前端使用哪个API端点？
   - `/recommend` (旧) → 需要升级
   - `/query` + `/events` (新) → 正确

2. ✅ 事件字段名是否一致？
   - 后端发送: `event_type`
   - 前端期望: `type`
   - 需要统一或转换

3. ✅ final_answer事件是否发送？
   - 在`process_query_async()`中已添加
   - 需要确保通过`/events`端点正确转发

4. ✅ 前端是否正确处理final_answer？
   - 已有处理代码
   - 需要确保接收到事件

---

## 🎯 最可能的问题

**根据你的截图，最可能的问题是**:

1. **前端使用了旧的`/recommend`端点**
   - 这个端点使用`process_stream()`
   - 而我们修改的是`process_query_async()`
   - 所以final_answer事件没有发送

2. **事件字段名不匹配**
   - 后端: `event_type`
   - 前端: `type`
   - 导致前端无法识别事件

---

## 🚀 立即行动

1. 检查前端使用的API端点
2. 统一事件字段名
3. 确保/events端点正确转发所有事件
4. 测试完整流程

---

**下一步: 请告诉我前端使用的是哪个API端点？** 🔍

可以在前端代码中搜索: `ai-recommend/recommend` 或 `ai-recommend/query`
