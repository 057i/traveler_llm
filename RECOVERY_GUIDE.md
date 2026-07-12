# AI推荐和文档处理功能恢复指南

## 问题描述

在编码清理过程中，以下两个功能受到影响：

1. **AI推荐页面** - 连接服务器失败，节点执行日志未显示
2. **文档处理进度** - 前端进度展示和后端节点日志丢失

## 已完成的修复

### 1. AI推荐 API 重建
✅ 文件：`backend/app/api/ai_recommend.py`
- 集成了 LangGraph workflow
- 实时节点执行追踪
- SSE 流式响应
- Redis 历史记录保存

### 2. 文档进度服务创建
✅ 文件：`backend/app/services/document_progress.py`
- 实时进度推送
- 节点日志记录
- Redis 状态管理
- SSE 事件格式化

## 需要完成的步骤

### 步骤 1: 集成文档进度服务到 workflow

需要修改文档处理 workflow 以使用新的进度服务：

**文件：** `backend/app/workflows/document_processing/graph_builder.py`

```python
# 在每个节点中添加进度回调
from app.services.document_progress import get_document_progress_service

async def process_with_progress(task_id: str, file_path: str):
    progress_service = get_document_progress_service()
    
    # 开始
    await progress_service.send_start(task_id, filename)
    
    # 步骤 1: MinIO (0-15%)
    await progress_service.send_progress(task_id, 0, 5, "Saving to MinIO", "Uploading file")
    # ... 执行节点
    await progress_service.send_progress(task_id, 0, 15, "MinIO saved", "File uploaded")
    
    # 步骤 2: PDF Parse (15-35%)
    await progress_service.send_progress(task_id, 1, 20, "Parsing PDF", "Using MinerU")
    # ... 执行节点
    await progress_service.send_progress(task_id, 1, 35, "PDF parsed", f"{pages} pages")
    
    # 步骤 3: Chunking (35-50%)
    await progress_service.send_progress(task_id, 2, 40, "Chunking text", "Splitting into chunks")
    # ... 执行节点
    await progress_service.send_progress(task_id, 2, 50, "Chunking complete", f"{len(chunks)} chunks")
    
    # 步骤 4: Entity Extraction (50-70%)
    await progress_service.send_progress(task_id, 3, 55, "Extracting entities", "Using Qwen")
    # ... 执行节点
    await progress_service.send_progress(task_id, 3, 70, "Entities extracted", f"{len(entities)} destinations")
    
    # 步骤 5: Vectorization (70-85%)
    await progress_service.send_progress(task_id, 4, 75, "Vectorizing", "Storing in ChromaDB")
    # ... 执行节点
    await progress_service.send_progress(task_id, 4, 85, "Vectorization complete", "Data indexed")
    
    # 步骤 6: Graph (85-100%)
    await progress_service.send_progress(task_id, 5, 90, "Building graph", "Storing in Neo4j")
    # ... 执行节点
    await progress_service.send_progress(task_id, 5, 95, "Graph complete", "Relationships created")
    
    # 完成
    await progress_service.send_complete(task_id, len(destinations), "Processing complete")
```

### 步骤 2: 更新文档上传 API

**文件：** `backend/app/api/documents.py`

在 `upload_document` 函数中调用 workflow：

```python
from app.workflows.document_processing.graph_builder import build_document_processing_workflow
from app.services.document_progress import get_document_progress_service

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # ... 文件保存逻辑 ...
    
    # 启动后台处理任务
    asyncio.create_task(process_document_async(task_id, file.filename, temp_file_path))
    
    return {"task_id": task_id, "status": "processing"}

async def process_document_async(task_id: str, filename: str, file_path: str):
    """异步处理文档"""
    try:
        progress_service = get_document_progress_service()
        await progress_service.send_start(task_id, filename)
        
        # 调用 workflow
        workflow = build_document_processing_workflow()
        result = await workflow.process(task_id, file_path)
        
        await progress_service.send_complete(task_id, result['destinations_count'])
        
    except Exception as e:
        await progress_service.send_error(task_id, str(e))
```

### 步骤 3: 前端AI推荐页面修复

**文件：** `frontend/src/views/AIRecommend.vue`

确保 SSE 连接正确：

```javascript
// 修改 EventSource URL
const eventSource = new EventSource(
  `http://localhost:8000/api/ai-recommend/stream`,
  { withCredentials: false }
);

// 使用 POST 请求发送数据
const response = await fetch('http://localhost:8000/api/ai-recommend/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: userQuery,
    session_id: sessionId
  })
});

// 读取 SSE 流
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));
      handleProgressUpdate(data);
    }
  }
}
```

### 步骤 4: 前端文档进度显示

**文件：** `frontend/src/components/ProcessingProgress.vue`

已经实现，确保连接正确的 API：

```javascript
const eventSource = new EventSource(
  `http://localhost:8000/api/documents/progress/${props.taskId}`
);
```

## 测试检查清单

### AI推荐测试
- [ ] 访问 http://localhost:5173/ai_recommend
- [ ] 输入查询："推荐三清山旅游攻略"
- [ ] 验证实时节点日志显示
- [ ] 验证最终答案和来源展示
- [ ] 检查后端日志输出

### 文档处理测试
- [ ] 访问 http://localhost:5173/documents
- [ ] 上传PDF文件
- [ ] 验证进度条实时更新
- [ ] 验证6个步骤的状态显示
- [ ] 检查后端节点日志输出
- [ ] 验证处理完成后的统计数据

## 后端日志验证

启动后端后，应该看到以下日志：

```
[MinIO] Saving file to local storage
[MinIO] Saved to local: /path/to/file.pdf
[PDF] Starting PDF parse with MinerU
[PDF] Parsing completed in 5.2s
[Chunk] Chunking text with RecursiveCharacterTextSplitter
[Chunk] Created 15 chunks
[Extract] Extracting entities with Qwen
[Extract] Extracted 8 destinations
[Vector] Traditional vectorization with Milvus
[Vector] Milvus vectorization: 8 destinations added
[Vector] Graph vectorization with Neo4j
[Vector] Graph vectorization completed with 8 entities
[Finalize] Completing workflow
[Workflow] Completed: 8 destinations
```

## 快速修复脚本

如果需要快速验证，可以运行：

```bash
# 测试AI推荐 API
curl -X POST http://localhost:8000/api/ai-recommend/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"推荐三清山","session_id":"test"}'

# 测试文档上传
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf"
```

## 状态总结

| 功能 | 状态 | 备注 |
|------|------|------|
| AI推荐 API | ✅ 已修复 | 需要集成到前端 |
| 文档进度服务 | ✅ 已创建 | 需要集成到 workflow |
| 文档处理 workflow | ⚠️ 需要更新 | 添加进度回调 |
| 前端AI推荐 | ⚠️ 需要测试 | SSE连接验证 |
| 前端文档进度 | ✅ 已实现 | 需要测试 |
| 后端节点日志 | ✅ 正常 | 所有logger调用保留 |

## 下一步行动

1. **立即行动**：集成文档进度服务到 workflow
2. **前端调试**：测试 SSE 连接和数据接收
3. **端到端测试**：完整流程验证
4. **性能优化**：Redis连接池和缓存策略

---

**创建时间**: 2026-07-12  
**状态**: 恢复指南 - 等待实施
