# Redis缓存系统设计方案

## 📋 需求分析

从截图和代码看，需要缓存：
1. **聊天记录**: 用户查询和AI回复
2. **进度信息**: LangGraph工作流的实时进度
3. **会话状态**: session_id对应的上下文
4. **推荐历史**: 快速推荐建议（如"推荐一下三清山的旅游攻略"）

---

## 🏗️ 项目结构建议

```
backend/app/
├── core/
│   ├── redis_client.py          # Redis连接管理（新增）
│   ├── cache_manager.py         # 统一缓存管理（新增）
│   └── ...
├── services/
│   ├── chat_history.py          # 聊天记录服务（新增）
│   ├── progress_tracker.py      # 进度追踪服务（新增）
│   └── ...
├── workflows/
│   └── ai_recommend/
│       ├── service.py           # 修改：集成缓存
│       └── ...
└── api/
    └── ai_recommend.py          # 修改：添加历史记录接口
```

---

## 🎯 Redis数据结构设计

### 1. 聊天记录（Chat History）

**数据结构**: List + Hash

```redis
# 会话消息列表（有序）
chat:session:{session_id}:messages  → List
  [message_id_1, message_id_2, ...]

# 消息详情（Hash）
chat:message:{message_id}  → Hash
  {
    "session_id": "session-xxx",
    "type": "user" | "assistant",
    "content": "推荐一下三清山",
    "timestamp": "2026-07-12 12:00:00",
    "metadata": "{...}"  # JSON字符串
  }

# 会话元信息
chat:session:{session_id}:meta  → Hash
  {
    "created_at": "2026-07-12 12:00:00",
    "updated_at": "2026-07-12 12:05:00",
    "message_count": "10",
    "user_id": "user_123"  # 可选
  }
```

**过期策略**:
- 聊天记录: 7天（可配置）
- 活跃会话: 24小时无操作后过期

---

### 2. 进度追踪（Progress Tracking）

**数据结构**: Hash + PubSub

```redis
# 工作流进度（Hash）
progress:{session_id}  → Hash
  {
    "status": "running" | "completed" | "failed",
    "current_node": "query_rewriter",
    "progress": "0.3",  # 30%
    "started_at": "2026-07-12 12:00:00",
    "updated_at": "2026-07-12 12:00:05",
    "nodes_completed": "2",
    "total_nodes": "8",
    "message": "正在查询理解..."
  }

# 节点进度详情
progress:{session_id}:nodes  → Hash
  {
    "query_rewriter": "completed",
    "parallel_retrieval": "running",
    "rrf_fusion": "pending",
    ...
  }

# 实时进度推送（PubSub）
PUBLISH progress:{session_id} '{"node": "query_rewriter", "status": "completed"}'
```

**过期策略**:
- 进度信息: 1小时后自动过期
- 完成后立即清理（可选保留5分钟用于回溯）

---

### 3. 推荐建议缓存（Quick Suggestions）

**数据结构**: Set

```redis
# 热门推荐建议
suggestions:hot  → ZSet (按点击次数排序)
  {
    "推荐一下三清山的旅游攻略": 156,
    "去哪里看雪比较好": 89,
    ...
  }

# 最近推荐建议
suggestions:recent:{session_id}  → List
  ["推荐一下三清山", "南昌有什么好玩的", ...]
```

**过期策略**:
- 热门建议: 永久（定期更新）
- 最近建议: 24小时

---

### 4. 结果缓存（Result Cache）

**数据结构**: String (JSON)

```redis
# 查询结果缓存
cache:query:{query_hash}  → String (JSON)
  {
    "query": "推荐一下三清山",
    "results": [...],
    "cached_at": "2026-07-12 12:00:00",
    "ttl": 3600
  }
```

**过期策略**:
- 查询结果: 1小时（避免过期数据）

---

## 💻 实现代码

### 1. Redis连接管理

**文件**: `app/core/redis_client.py`

```python
"""
Redis客户端管理
"""
import redis
from redis.connection import ConnectionPool
from loguru import logger
from config.settings import settings


class RedisClient:
    """Redis客户端单例"""

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._init_pool()

    def _init_pool(self):
        """初始化连接池"""
        try:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,  # 自动解码为字符串
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            logger.success(f"✅ Redis连接池初始化成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis连接池初始化失败: {e}")
            raise

    def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        return redis.Redis(connection_pool=self._pool)

    def ping(self) -> bool:
        """健康检查"""
        try:
            client = self.get_client()
            return client.ping()
        except Exception as e:
            logger.error(f"❌ Redis健康检查失败: {e}")
            return False


# 全局实例
_redis_client = RedisClient()


def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return _redis_client.get_client()
```

---

### 2. 聊天记录服务

**文件**: `app/services/chat_history.py`

```python
"""
聊天记录服务 - 基于Redis
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

from app.core.redis_client import get_redis


class ChatHistoryService:
    """聊天记录服务"""

    def __init__(self):
        self.redis = get_redis()
        self.ttl = 7 * 24 * 3600  # 7天

    def add_message(
        self,
        session_id: str,
        message_type: str,  # "user" | "assistant"
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        添加消息到聊天记录

        Args:
            session_id: 会话ID
            message_type: 消息类型
            content: 消息内容
            metadata: 元数据

        Returns:
            message_id: 消息ID
        """
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        timestamp = datetime.now().isoformat()

        # 1. 保存消息详情
        message_key = f"chat:message:{message_id}"
        self.redis.hset(message_key, mapping={
            "session_id": session_id,
            "type": message_type,
            "content": content,
            "timestamp": timestamp,
            "metadata": json.dumps(metadata or {})
        })
        self.redis.expire(message_key, self.ttl)

        # 2. 添加到会话消息列表
        list_key = f"chat:session:{session_id}:messages"
        self.redis.rpush(list_key, message_id)
        self.redis.expire(list_key, self.ttl)

        # 3. 更新会话元信息
        meta_key = f"chat:session:{session_id}:meta"
        if not self.redis.exists(meta_key):
            self.redis.hset(meta_key, "created_at", timestamp)

        self.redis.hset(meta_key, mapping={
            "updated_at": timestamp,
            "message_count": str(self.redis.llen(list_key))
        })
        self.redis.expire(meta_key, self.ttl)

        logger.info(f"💬 添加消息: session={session_id}, type={message_type}, id={message_id}")

        return message_id

    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取会话历史记录

        Args:
            session_id: 会话ID
            limit: 返回消息数量
            offset: 偏移量

        Returns:
            消息列表
        """
        list_key = f"chat:session:{session_id}:messages"

        # 获取消息ID列表
        message_ids = self.redis.lrange(list_key, offset, offset + limit - 1)

        if not message_ids:
            return []

        # 批量获取消息详情
        messages = []
        for message_id in message_ids:
            message_key = f"chat:message:{message_id}"
            message_data = self.redis.hgetall(message_key)

            if message_data:
                messages.append({
                    "id": message_id,
                    "session_id": message_data.get("session_id"),
                    "type": message_data.get("type"),
                    "content": message_data.get("content"),
                    "timestamp": message_data.get("timestamp"),
                    "metadata": json.loads(message_data.get("metadata", "{}"))
                })

        logger.info(f"📜 获取历史: session={session_id}, count={len(messages)}")

        return messages

    def get_recent_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> str:
        """
        获取最近的对话上下文（用于查询重写）

        Args:
            session_id: 会话ID
            max_messages: 最大消息数

        Returns:
            格式化的对话上下文
        """
        messages = self.get_history(session_id, limit=max_messages)

        if not messages:
            return ""

        # 格式化为对话文本
        context_lines = []
        for msg in messages[-max_messages:]:  # 取最后N条
            role = "用户" if msg["type"] == "user" else "助手"
            context_lines.append(f"{role}: {msg['content']}")

        context = "\n".join(context_lines)
        logger.info(f"📝 获取上下文: session={session_id}, messages={len(messages)}")

        return context

    def clear_session(self, session_id: str):
        """清除会话记录"""
        list_key = f"chat:session:{session_id}:messages"
        message_ids = self.redis.lrange(list_key, 0, -1)

        # 删除所有消息
        for message_id in message_ids:
            self.redis.delete(f"chat:message:{message_id}")

        # 删除会话相关键
        self.redis.delete(list_key)
        self.redis.delete(f"chat:session:{session_id}:meta")

        logger.info(f"🗑️ 清除会话: session={session_id}")


# 全局实例
_chat_history_service = None


def get_chat_history_service() -> ChatHistoryService:
    """获取聊天记录服务实例"""
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service
```

---

### 3. 进度追踪服务

**文件**: `app/services/progress_tracker.py`

```python
"""
进度追踪服务 - 基于Redis
"""
import json
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from app.core.redis_client import get_redis


class ProgressTracker:
    """进度追踪器"""

    def __init__(self):
        self.redis = get_redis()
        self.ttl = 3600  # 1小时

    def update_progress(
        self,
        session_id: str,
        current_node: str,
        progress: float,
        status: str = "running",
        message: Optional[str] = None,
        total_nodes: int = 8
    ):
        """
        更新工作流进度

        Args:
            session_id: 会话ID
            current_node: 当前节点名称
            progress: 进度（0.0-1.0）
            status: 状态
            message: 进度消息
            total_nodes: 总节点数
        """
        progress_key = f"progress:{session_id}"
        timestamp = datetime.now().isoformat()

        # 更新进度信息
        progress_data = {
            "status": status,
            "current_node": current_node,
            "progress": str(progress),
            "updated_at": timestamp,
            "total_nodes": str(total_nodes),
        }

        if message:
            progress_data["message"] = message

        # 首次创建时设置started_at
        if not self.redis.exists(progress_key):
            progress_data["started_at"] = timestamp

        self.redis.hset(progress_key, mapping=progress_data)
        self.redis.expire(progress_key, self.ttl)

        # 发布进度更新事件（用于实时推送）
        self.redis.publish(
            f"progress:{session_id}",
            json.dumps({
                "node": current_node,
                "status": status,
                "progress": progress,
                "message": message
            })
        )

        logger.info(f"📊 更新进度: session={session_id}, node={current_node}, progress={progress:.1%}")

    def update_node_status(
        self,
        session_id: str,
        node_name: str,
        status: str  # "pending" | "running" | "completed" | "failed"
    ):
        """
        更新节点状态

        Args:
            session_id: 会话ID
            node_name: 节点名称
            status: 节点状态
        """
        nodes_key = f"progress:{session_id}:nodes"

        self.redis.hset(nodes_key, node_name, status)
        self.redis.expire(nodes_key, self.ttl)

        logger.debug(f"🔄 节点状态: {node_name} → {status}")

    def get_progress(self, session_id: str) -> Optional[Dict]:
        """
        获取进度信息

        Args:
            session_id: 会话ID

        Returns:
            进度信息字典
        """
        progress_key = f"progress:{session_id}"
        nodes_key = f"progress:{session_id}:nodes"

        progress_data = self.redis.hgetall(progress_key)
        if not progress_data:
            return None

        # 获取节点状态
        nodes_data = self.redis.hgetall(nodes_key)

        # 计算已完成节点数
        nodes_completed = sum(1 for status in nodes_data.values() if status == "completed")

        return {
            "status": progress_data.get("status"),
            "current_node": progress_data.get("current_node"),
            "progress": float(progress_data.get("progress", 0)),
            "message": progress_data.get("message"),
            "started_at": progress_data.get("started_at"),
            "updated_at": progress_data.get("updated_at"),
            "nodes_completed": nodes_completed,
            "total_nodes": int(progress_data.get("total_nodes", 8)),
            "nodes": nodes_data
        }

    def complete(self, session_id: str, success: bool = True):
        """
        标记工作流完成

        Args:
            session_id: 会话ID
            success: 是否成功
        """
        progress_key = f"progress:{session_id}"

        self.redis.hset(progress_key, mapping={
            "status": "completed" if success else "failed",
            "progress": "1.0",
            "updated_at": datetime.now().isoformat()
        })

        # 完成后5分钟过期
        self.redis.expire(progress_key, 300)

        logger.success(f"✅ 工作流{'成功' if success else '失败'}: session={session_id}")

    def clear(self, session_id: str):
        """清除进度信息"""
        self.redis.delete(f"progress:{session_id}")
        self.redis.delete(f"progress:{session_id}:nodes")

        logger.info(f"🗑️ 清除进度: session={session_id}")


# 全局实例
_progress_tracker = None


def get_progress_tracker() -> ProgressTracker:
    """获取进度追踪器实例"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
```

---

## 🔌 集成到工作流

### 修改 `app/workflows/ai_recommend/service.py`

```python
# 在文件开头添加导入
from app.services.chat_history import get_chat_history_service
from app.services.progress_tracker import get_progress_tracker

class AIRecommendService:
    def __init__(self):
        self.workflow = get_ai_recommend_workflow()
        self.chat_history = get_chat_history_service()  # 新增
        self.progress_tracker = get_progress_tracker()  # 新增

    async def recommend_stream(self, user_query: str, session_id: str = None):
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

        # 3. 执行工作流（在每个节点完成后更新进度）
        # ... 现有代码 ...

        # 4. 保存AI回复
        self.chat_history.add_message(
            session_id=session_id,
            message_type="assistant",
            content=final_response
        )

        # 5. 标记完成
        self.progress_tracker.complete(session_id, success=True)
```

---

## 🚀 使用方式

### 1. 添加历史记录API

**文件**: `app/api/ai_recommend.py`

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
```

---

## 📊 Redis键命名规范总结

```
# 聊天记录
chat:session:{session_id}:messages    # List
chat:message:{message_id}             # Hash
chat:session:{session_id}:meta        # Hash

# 进度追踪
progress:{session_id}                 # Hash
progress:{session_id}:nodes           # Hash

# 推荐建议
suggestions:hot                       # ZSet
suggestions:recent:{session_id}       # List

# 结果缓存
cache:query:{query_hash}              # String (JSON)
```

---

需要我继续实现前端集成部分吗？
