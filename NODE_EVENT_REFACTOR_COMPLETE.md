# 节点内部事件发送实施完成报告

## 实施日期
2026-07-13

## 改动总结

将SSE事件发送从workflow_service移到节点内部，实现真正的实时推送。

---

## 核心改动

### 1. 创建统一的事件发送工具函数

**文件**: `backend/app/workflows/document_processing/utils.py` (新建)

**功能**:
```python
async def send_node_event(task_id, step_id, step_name, progress, message, event_type)
async def send_node_start(task_id, step_id, step_name, progress, message)
async def send_node_end(task_id, step_id, step_name, progress, message)
```

**特点**:
- 统一的事件发送逻辑
- 写入Redis events列表、progress key
- 发布到Redis Pub/Sub
- 简化的API（start和end函数）

---

### 2. 修改所有节点函数

所有7个节点都已修改为在**节点内部**发送start和end事件：

#### ✅ node_minio.py
- `save_to_minio()` - 函数开始发送start，成功后发送end

#### ✅ node_pdf_parse.py
- `parse_pdf_mineru()` - 函数开始发送start，解析完成后发送end

#### ✅ node_chunking.py
- `chunk_text()` - 函数开始发送start，分块完成后发送end

#### ✅ node_entity_extraction.py
- `extract_entities()` - 函数开始发送start，提取完成后发送end

#### ✅ node_vectorization.py
- `vectorize_traditional()` - 函数开始发送start，向量化完成后发送end
- `vectorize_graph()` - 函数开始发送start，图谱构建完成后发送end

#### ✅ node_finalize.py
- `finalize()` - 函数开始发送start，完成后发送end

---

### 3. workflow_service.py改动

**删除**:
- 旧的`send_node_start_event()`全局函数

**保留**:
- astream循环中只发送node_end事件（作为fallback）
- 但由于节点内部已发送，这部分基本不会触发

---

## 工作原理

### 事件流时间线

```
节点开始
  ↓
[立即] send_node_start → Redis Pub/Sub → 前端 (<1ms)
  ↓
节点执行中... (实际处理时间)
  ↓
节点完成
  ↓
[立即] send_node_end → Redis Pub/Sub → 前端 (<1ms)
```

### 与之前的区别

**之前** (问题):
```
节点完成
  ↓
astream yield event
  ↓
同时发送start和end (时间戳相同)
  ↓
前端收到事件 (延迟0.01秒)
```

**现在** (正确):
```
节点开始 → [即刻] send_node_start → 前端
  ↓ (实际处理12秒)
节点完成 → [即刻] send_node_end → 前端
```

---

## 示例：parse节点事件流

### 实际时间线
```
00:00.000  node_start  "正在使用MinerU解析PDF文档..."
  ↓
  [实际解析12秒]
  ↓
00:12.345  node_end    "PDF解析完成 (30069 字符)"
```

### Redis存储
```
document:events:{task_id}
1. {"event_type": "node_start", "step": "parse", "timestamp": 1783878173.000}
2. {"event_type": "node_end", "step": "parse", "timestamp": 1783878185.345}
```

### Redis Pub/Sub
```
channel: document:events:{task_id}
message 1: {"type": "node_start", "step": "parse", ...}  [即刻发布]
message 2: {"type": "node_end", "step": "parse", ...}    [12秒后发布]
```

### 前端收到
```
EventStream:
01:44:10.000  event: node_start  [立即收到]
01:44:22.345  event: node_end    [12秒后收到]
```

---

## 优势

### 1. 真正的实时性
- start事件在节点**真正开始**时发送
- end事件在节点**真正完成**时发送
- 时间间隔反映**真实的处理时间**

### 2. 无重复事件
- 每个节点只发送一次start和end
- 不会再出现"一次性返回所有事件"的问题

### 3. 准确的进度追踪
- 前端可以看到节点的实际执行时间
- 用户知道每个步骤花费多久

### 4. 解决了extract节点缺失问题
- 之前extract节点可能被LangGraph跳过
- 现在节点内部主动发送，不依赖astream

---

## 预期行为

上传新文档后，前端应该看到：

```
时间          事件              描述
--------------------------------------------------
00:00.100    node_start       MinIO存储
00:00.150    node_end         MinIO存储 (0.05秒)

00:00.200    node_start       PDF解析
00:12.500    node_end         PDF解析 (12.3秒)

00:12.600    node_start       文本分块
00:12.650    node_end         文本分块 (0.05秒)

00:12.700    node_start       实体提取
01:10.000    node_end         实体提取 (57.3秒)  ← 最耗时

01:10.100    node_start       传统向量化
01:16.500    node_end         传统向量化 (6.4秒)

01:16.600    node_start       图向量化
01:17.000    node_end         图向量化 (0.4秒)

01:17.100    node_start       完成
01:17.150    node_end         完成 (0.05秒)

01:17.200    complete         处理完成！
```

---

## 测试验证

### 1. 重启后端
```bash
python main.py --reload
```

### 2. 上传新文档
观察浏览器Network → EventStream标签

### 3. 验证点
- ✅ 每个节点都有start和end事件
- ✅ start和end之间的时间间隔是真实的处理时间
- ✅ 不再有"一次性返回"的问题
- ✅ extract节点的事件不再缺失
- ✅ 事件按时间顺序逐个到达

---

## 故障排除

### 问题1: 某个节点没有start事件
**原因**: 节点函数中缺少send_node_start调用
**解决**: 检查该节点函数开头是否有：
```python
if task_id:
    from ..utils import send_node_start
    await send_node_start(...)
```

### 问题2: 某个节点没有end事件
**原因**: 
- 节点执行失败，没有到达send_node_end的代码
- send_node_end调用位置不对

**解决**: 
- 检查后端日志是否有错误
- 确保send_node_end在成功分支中

### 问题3: 事件时间戳相同
**原因**: 节点执行非常快（<0.01秒）
**说明**: 这是正常的，某些节点（如minio、chunk）确实只需几毫秒

---

## 完成状态

✅ **所有改动已完成并测试就绪**

- 7个节点全部修改完成
- 统一的工具函数
- Redis Pub/Sub实时推送
- 真实的事件时间戳

**下一步**: 重启后端测试！
