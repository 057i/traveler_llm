# Redis缓存系统使用指南

## ✅ 已完成的工作

### 创建的文件（4个）

1. ✅ `app/core/redis_client.py` - Redis连接管理
2. ✅ `app/services/chat_history.py` - 聊天记录服务
3. ✅ `app/services/progress_tracker.py` - 进度追踪服务
4. ✅ `app/services/__init__.py` - 服务层初始化

### 设计文档
- ✅ `REDIS_CACHE_DESIGN.md` - 完整设计方案

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install redis
```

### 2. 测试Redis连接

```python
# 测试脚本
from app.core.redis_client import get_redis

redis = get_redis()
if redis.ping():
    print("✅ Redis连接成功！")
else:
    print("❌ Redis连接失败")
```

---

## 📖 使用示例

### 1. 聊天记录管理

```python
from app.services.chat_history import get_chat_history_service

# 获取服务实例
chat_service = get_chat_history_service()

# 添加用户消息
chat_service.add_message(
    session_id="session-123",
    message_type="user",
    content="推荐一下三清山的旅游攻略"
)

# 添加AI回复
chat_service.add_message(
    session_id="session-123",
    message_type="assistant",
    content="三清山位于江西省...",
    metadata={"score": 0.88, "rerank": True}
)

# 获取历史记录
history = chat_service.get_history("session-123", limit=10)
print(f"历史消息数: {len(history)}")

# 获取对话上下文（用于查询重写）
context = chat_service.get_recent_context("session-123", max_messages=5)
print(f"对话上下文:\n{context}")

# 清除会话
chat_service.clear_session("session-123")
```

---

### 2. 进度追踪

```python
from app.services.progress_tracker import get_progress_tracker

# 获取追踪器实例
tracker = get_progress_tracker()

# 更新进度
tracker.update_progress(
    session_id="session-123",
    current_node="query_rewriter",
    progress=0.125,  # 1/8
    status="running",
    message="正在理解查询...",
    total_nodes=8
)

# 更新节点状态
tracker.update_node_status(
    session_id="session-123",
    node_name="query_rewriter",
    status="completed"
)

# 获取进度信息
progress = tracker.get_progress("session-123")
print(f"当前进度: {progress['progress']:.0%}")
print(f"当前节点: {progress['current_node']}")
print(f"已完成: {progress['nodes_completed']}/{progress['total_nodes']}")

# 标记完成
tracker.complete("session-123", success=True)

# 清除进度
tracker.clear("session-123")
```

---

## 🔌 集成到工作流

### 修改 `app/workflows/ai_recommend/service.py`

在文件开头添加导入：

```python
from app.services.chat_history import get_chat_history_service
from app.services.progress_tracker import get_progress_tracker
```

在 `__init__` 方法中初始化：

```python
class AIRecommendService:
    def __init__(self):
        self.workflow = get_ai_recommend_workflow()
        self.chat_history = get_chat_history_service()  # 新增
        self.progress_tracker = get_progress_tracker()  # 新增
```

在 `recommend_stream` 方法中使用：

```python
async def recommend_stream(self, user_query: str, session_id: str = None):
    try:
        # 1. 保存用户消息
        self.chat_history.add_message(
            session_id=session_id,
            message_type="user",
            content=user_query
        )

        # 2. 初始化进度
        self.progress_tracker.update_progress(
            session_id=session_id,
            current_node="start",
            progress=0.0,
            message="开始AI推荐..."
        )

        # 3. 执行工作流
        initial_state = {
            "user_query": user_query,
            "session_id": session_id,
            # 获取历史上下文
            "chat_history": self.chat_history.get_recent_context(session_id, max_messages=10),
            # ... 其他状态
        }

        # 4. 在每个节点完成时更新进度
        # 可以在graph_builder中的每个节点添加进度更新

        # 5. 保存AI回复
        final_response = "..."  # 从工作流获取
        self.chat_history.add_message(
            session_id=session_id,
            message_type="assistant",
            content=final_response
        )

        # 6. 标记完成
        self.progress_tracker.complete(session_id, success=True)

    except Exception as e:
        # 失败时也标记
        self.progress_tracker.complete(session_id, success=False)
        raise
```

---

## 🌐 添加API接口

### 修改 `app/api/ai_recommend.py`

添加以下接口：

```python
@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = Query(50, description="返回消息数量")
):
    """获取聊天历史记录"""
    from app.services.chat_history import get_chat_history_service

    service = get_chat_history_service()
    history = service.get_history(session_id, limit=limit)

    return {
        "session_id": session_id,
        "messages": history,
        "count": len(history)
    }


@router.get("/progress/{session_id}")
async def get_progress(session_id: str):
    """获取实时进度"""
    from app.services.progress_tracker import get_progress_tracker

    tracker = get_progress_tracker()
    progress = tracker.get_progress(session_id)

    if not progress:
        return {"error": "进度信息不存在"}

    return progress


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """清除聊天历史"""
    from app.services.chat_history import get_chat_history_service

    service = get_chat_history_service()
    service.clear_session(session_id)

    return {"message": "会话已清除", "session_id": session_id}
```

---

## 🎯 Redis数据结构

### 聊天记录

```
chat:session:{session_id}:messages     # List: 消息ID列表
chat:message:{message_id}              # Hash: 消息详情
chat:session:{session_id}:meta         # Hash: 会话元信息
```

### 进度信息

```
progress:{session_id}                  # Hash: 进度信息
progress:{session_id}:nodes            # Hash: 节点状态
```

### 查看数据

```bash
# Redis CLI 命令
redis-cli

# 查看所有会话
KEYS chat:session:*:messages

# 查看消息列表
LRANGE chat:session:session-123:messages 0 -1

# 查看消息详情
HGETALL chat:message:msg_abc123

# 查看进度
HGETALL progress:session-123

# 查看节点状态
HGETALL progress:session-123:nodes
```

---

## 📊 前端调用示例

### JavaScript

```javascript
// 获取聊天历史
async function getChatHistory(sessionId) {
    const response = await fetch(`/api/ai-recommend/history/${sessionId}`);
    const data = await response.json();
    console.log(`历史消息数: ${data.count}`);
    return data.messages;
}

// 轮询进度
async function pollProgress(sessionId) {
    const response = await fetch(`/api/ai-recommend/progress/${sessionId}`);
    const progress = await response.json();
    
    console.log(`进度: ${(progress.progress * 100).toFixed(0)}%`);
    console.log(`当前节点: ${progress.current_node}`);
    console.log(`消息: ${progress.message}`);
    
    return progress;
}

// 使用EventSource监听进度（需要后端支持SSE）
const eventSource = new EventSource(`/api/ai-recommend/stream?query=三清山&session_id=${sessionId}`);

eventSource.addEventListener('progress', (event) => {
    const data = JSON.parse(event.data);
    console.log(`进度更新: ${data.node} - ${data.message}`);
});
```

---

## ⚙️ 配置说明

Redis配置在 `config/settings.py` 中：

```python
# Redis 配置
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0
REDIS_PASSWORD: str = ""  # 如果有密码
```

### 过期策略

- **聊天记录**: 7天自动过期
- **进度信息**: 1小时自动过期
- **完成后**: 5分钟自动清理

---

## 🔧 故障排查

### 1. Redis连接失败

```python
# 检查Redis是否运行
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # 应该返回True
```

### 2. 查看日志

```python
from loguru import logger

# Redis客户端会自动输出日志
# 成功: ✅ Redis连接池初始化成功
# 失败: ❌ Redis连接池初始化失败
```

### 3. 清空所有数据（慎用）

```bash
redis-cli FLUSHDB  # 清空当前数据库
redis-cli FLUSHALL # 清空所有数据库
```

---

## 🎉 完成状态

- ✅ Redis连接管理
- ✅ 聊天记录服务
- ✅ 进度追踪服务
- ✅ API接口设计
- ✅ 使用文档完善
- ⏳ 等待集成到工作流

---

## 🚀 下一步

1. **安装依赖**: `pip install redis`
2. **测试连接**: 运行测试脚本
3. **集成到工作流**: 修改 `service.py`
4. **添加API**: 修改 `ai_recommend.py`
5. **前端调用**: 集成历史记录和进度显示

需要我帮你集成到工作流中吗？
