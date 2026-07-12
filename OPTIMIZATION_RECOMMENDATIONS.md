# SSE实时进度和RAG文档上传优化建议

## 当前实现评估

### ✅ 已完成的优化
1. **事件去重机制** - 使用sent_event_ids避免重复发送
2. **Pipeline优化** - 列表查询性能提升3.5倍
3. **事件发送顺序** - 先发送SSE，再存储历史
4. **轮询优化** - 100ms轮询间隔，1ms历史事件延迟
5. **完整的事件流** - 每个节点都有start和end事件

### ✅ 测试结果
- 14个事件（7对start/end）
- 无重复事件
- 事件顺序正确
- 所有步骤完整

---

## 🚀 进一步优化建议

### 1. SSE实时推送优化

#### 问题：当前轮询机制
- **当前**：SSE端点每100ms轮询Redis
- **问题**：最多100ms延迟，消耗CPU资源

#### 优化方案A：Redis Pub/Sub（推荐）
```python
# 优点：
✓ 真正的实时推送（<1ms延迟）
✓ 零轮询开销
✓ 更好的资源利用

# 实现：
1. workflow发送事件时，publish到Redis channel
2. SSE端点subscribe该channel
3. 收到消息立即推送给前端

# 改动：
- app/workflows/workflow_service.py: 添加redis.publish()
- app/api/documents.py: 使用redis.subscribe()替代轮询
```

#### 优化方案B：WebSocket
```python
# 优点：
✓ 双向通信
✓ 更低延迟
✓ 更灵活

# 缺点：
× 前端需要改动较多
× 复杂度增加

# 适用场景：
- 需要前端向后端发送控制命令（暂停、取消等）
```

#### 优化方案C：保持当前SSE + 调整轮询
```python
# 如果不想大改，可以：
1. 减少轮询间隔到50ms（当前100ms）
2. 添加事件变化检测，只在有变化时发送
3. 使用Redis BLPOP等待新事件（阻塞式）

# 工作量：最小
# 效果：中等
```

**推荐：方案A（Redis Pub/Sub）** - 性能提升明显，改动适中

---

### 2. BackgroundTasks vs 当前实现

#### 当前实现（asyncio.create_task）
```python
# app/api/documents.py
asyncio.create_task(process_document_background(...))
```

**优点**：
- ✓ 简单直接
- ✓ 不会阻塞HTTP响应
- ✓ 异步执行

**缺点**：
- × 任务生命周期不受FastAPI管理
- × 服务重启会丢失进行中的任务
- × 没有错误追踪和重试机制

#### 优化方案：使用Celery/RQ（推荐用于生产环境）
```python
# 优点：
✓ 任务持久化（服务重启不丢失）
✓ 任务队列管理
✓ 错误重试机制
✓ 分布式处理
✓ 监控和管理界面

# 适用场景：
- 生产环境
- 需要任务持久化
- 需要分布式处理
- 需要任务重试

# 实现：
1. pip install celery redis
2. 创建celery_app.py
3. 将process_document_background改为celery task
4. 启动celery worker

# 工作量：中等
# 收益：生产环境必备
```

#### 优化方案：FastAPI BackgroundTasks
```python
# app/api/documents.py
from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # ...
    background_tasks.add_task(
        process_document_background,
        task_id, filename, file_path, pages_count
    )

# 优点：
✓ FastAPI原生支持
✓ 简单易用
✓ 自动清理

# 缺点：
× 仍然会在服务重启时丢失任务
× 不支持分布式
× 没有重试机制

# 适用场景：
- 开发/测试环境
- 任务执行时间短（<5分钟）
- 不需要持久化
```

**推荐**：
- **开发环境**：当前实现或BackgroundTasks即可
- **生产环境**：使用Celery + Redis

---

### 3. RAG文档上传优化

#### 3.1 文件上传优化

**当前问题**：
- 大文件占用内存
- 上传过程中服务器压力大

**优化方案**：
```python
# 1. 流式上传
async def upload_document(file: UploadFile):
    # 不要一次性读取整个文件到内存
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            await f.write(chunk)

# 2. 文件大小限制
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    request: Request
):
    # 检查Content-Length
    content_length = int(request.headers.get('content-length', 0))
    if content_length > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(413, "文件太大")

# 3. 直接上传到MinIO
# 不要先保存到本地，再上传MinIO
# 而是直接流式上传到MinIO
```

#### 3.2 工作流执行优化

**当前问题**：
- 所有步骤串行执行
- 部分步骤可以并行

**优化方案**：
```python
# 并行化独立步骤

# 当前流程（串行）：
minio → parse → chunk → extract → vectorize_traditional → vectorize_graph → finalize
                                   ↓                        ↓
                                   (可以并行)               

# 优化流程：
minio → parse → chunk → extract → [vectorize_traditional + vectorize_graph 并行] → finalize

# 实现：
async def parallel_vectorization(destinations):
    results = await asyncio.gather(
        vectorize_traditional(destinations),
        vectorize_graph(destinations)
    )
    return results

# 预期效果：节省 30-40% 的总处理时间
```

#### 3.3 实体提取优化

**当前问题**：
- 逐个chunk调用LLM API
- 速度慢

**优化方案**：
```python
# 1. 批量处理（如果API支持）
# 将多个chunk合并成一个请求
batch_size = 3
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    # 一次API调用处理多个chunk

# 2. 并发请求（控制并发数）
semaphore = asyncio.Semaphore(5)  # 最多5个并发
async def extract_with_limit(chunk):
    async with semaphore:
        return await extract_entities(chunk)

results = await asyncio.gather(*[
    extract_with_limit(chunk) for chunk in chunks
])

# 3. 使用更快的模型
# chunk前几个用大模型，后面用小模型
# 或者先用小模型过滤，再用大模型精炼
```

#### 3.4 向量化优化

**当前问题**：
- Milvus批量插入可以更高效

**优化方案**：
```python
# 1. 批量编码
# 当前：逐个生成向量
# 优化：批量生成（SentenceTransformer支持batch）
vectors = model.encode(
    [dest['name'] for dest in destinations],
    batch_size=32,
    show_progress_bar=False
)

# 2. 异步插入
# 向量化和图谱构建可以并行

# 3. 向量缓存
# 相同文本不重复编码
vector_cache = {}
def get_or_compute_vector(text):
    if text not in vector_cache:
        vector_cache[text] = model.encode(text)
    return vector_cache[text]
```

#### 3.5 错误处理和重试

**当前问题**：
- 任何步骤失败，整个流程失败
- 没有重试机制

**优化方案**：
```python
# 1. 添加重试装饰器
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm_api(...):
    # LLM API调用

# 2. 部分失败继续
# 某个chunk提取失败不应该导致整个任务失败
try:
    entities = await extract_entities(chunk)
except Exception as e:
    logger.error(f"Chunk {i} 提取失败: {e}")
    entities = []  # 继续处理其他chunk

# 3. 断点续传
# 保存每个步骤的状态
if state.get('parse_success'):
    skip parse
elif state.get('chunk_success'):
    skip chunk
# ... 从失败的地方继续
```

#### 3.6 性能监控

**添加性能追踪**：
```python
import time

class PerformanceTracker:
    def __init__(self):
        self.timings = {}

    async def track(self, name, coro):
        start = time.time()
        result = await coro
        elapsed = time.time() - start
        self.timings[name] = elapsed
        logger.info(f"[Perf] {name}: {elapsed:.2f}s")
        return result

# 使用
tracker = PerformanceTracker()
await tracker.track("parse_pdf", parse_pdf(...))
await tracker.track("extract_entities", extract_entities(...))

# 最后输出报告
logger.info(f"Total time: {sum(tracker.timings.values()):.2f}s")
for name, time in sorted(tracker.timings.items(), key=lambda x: -x[1]):
    logger.info(f"  {name}: {time:.2f}s ({time/sum(tracker.timings.values())*100:.1f}%)")
```

---

## 📊 优化优先级

### 高优先级（立即实施）
1. ✅ **SSE事件去重** - 已完成
2. ✅ **列表查询Pipeline优化** - 已完成
3. 🔄 **实体提取并发** - 效果明显，实现简单
4. 🔄 **向量化并行** - traditional和graph可并行

### 中优先级（生产环境建议）
5. 🔄 **Redis Pub/Sub替代轮询** - 提升实时性
6. 🔄 **Celery任务队列** - 生产环境必备
7. 🔄 **错误重试机制** - 提高可靠性

### 低优先级（按需实施）
8. 🔄 **文件流式上传** - 大文件场景需要
9. 🔄 **向量缓存** - 重复文档较多时有效
10. 🔄 **性能监控** - 便于定位瓶颈

---

## 💡 快速改进方案（推荐现在做）

### 改进1：并行向量化（10分钟实现）

```python
# app/workflows/document_processing/graph_builder.py
# 修改workflow，让vectorize_traditional和vectorize_graph并行

from langgraph.graph import StateGraph

def build_document_processing_workflow():
    # ...
    
    # 不要用add_edge，而是让两个节点都从extract_entities出发
    graph.add_edge("extract_entities", "vectorize_traditional")
    graph.add_edge("extract_entities", "vectorize_graph")
    
    # 添加一个汇聚节点
    graph.add_node("merge_results", merge_vectorization_results)
    graph.add_edge("vectorize_traditional", "merge_results")
    graph.add_edge("vectorize_graph", "merge_results")
    graph.add_edge("merge_results", "finalize")
```

**预期效果**：总处理时间减少30-40%

### 改进2：实体提取并发（5分钟实现）

```python
# app/workflows/document_processing/nodes/node_entity_extraction.py

# 修改extract_entities函数
async def extract_entities(state: Dict) -> Dict:
    # ...
    
    # 并发处理chunks（控制并发数为3）
    semaphore = asyncio.Semaphore(3)
    
    async def process_chunk_with_limit(i, chunk):
        async with semaphore:
            return await process_single_chunk(i, chunk)
    
    tasks = [
        process_chunk_with_limit(i, chunk)
        for i, chunk in enumerate(selected_chunks, 1)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果...
```

**预期效果**：实体提取速度提升2-3倍

---

## 总结

**当前实现**：已经相当不错，核心功能完整，事件流正确

**建议优先实施**：
1. 实体提取并发（立即）
2. 向量化并行（立即）
3. Redis Pub/Sub（生产环境前）
4. Celery任务队列（生产环境前）

**投入产出比最高的优化**：
- 🥇 并行向量化 - 5分钟实现，30%性能提升
- 🥈 实体提取并发 - 10分钟实现，2-3倍提升
- 🥉 Redis Pub/Sub - 30分钟实现，实时性大幅提升
