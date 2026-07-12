# SSE实时事件问题诊断和解决方案

## 问题现象

从浏览器EventStream可以看到：
1. ❌ **chunk的node_start缺失** - 只收到node_end
2. ❌ **extract的start和end几乎同时到达** - 应该间隔50+秒

## 根本原因

### 时序问题

```
00:00.000  后端开始处理文档
00:00.010  minio node_start → Pub/Sub
00:00.020  minio node_end → Pub/Sub
00:00.030  parse node_start → Pub/Sub
00:12.000  parse node_end → Pub/Sub
00:12.010  chunk node_start → Pub/Sub  ← SSE客户端还没连接！
00:12.020  chunk node_end → Pub/Sub
00:12.030  extract node_start → Pub/Sub
...
00:12.100  前端才连接SSE  ← 太晚了！
```

### 前端连接延迟

**DocumentManager.vue 第406行**:
```javascript
setTimeout(async () => {
    await fetchDocuments()  // 等待100ms后才刷新列表
    // WorkflowProgress组件此时才挂载和连接SSE
}, 100)
```

**问题**:
1. 上传成功后等待100ms
2. fetchDocuments查询API
3. 文档列表更新，expandedRows触发
4. WorkflowProgress组件挂载
5. onMounted中connectSSE()
6. 此时chunk甚至extract可能已经开始了

---

## 解决方案

### 方案A：立即连接SSE（推荐）⭐⭐⭐

**思路**: 上传成功后立即连接SSE，不等待列表刷新

```javascript
// DocumentManager.vue
const handleUploadSuccess = (response, file) => {
    console.log('[Upload] Response:', response)
    ElMessage.success(`${file.name} 上传成功！`)
    
    uploading.value = false
    uploadDialogVisible.value = false
    clearFiles()
    
    // 立即连接SSE（不等待）
    const taskId = response.task_id
    if (taskId) {
        // 立即展开这个任务
        expandedRows.value.push(taskId)
    }
    
    // 然后再刷新列表
    fetchDocuments()
}
```

**优点**:
- 不会错过任何事件
- 简单直接

**缺点**:
- 需要修改前端代码

---

### 方案B：增加历史事件保留时间（临时方案）

**思路**: 确保所有历史事件都被保留并发送

**当前**: Redis Pub/Sub是实时的，没有订阅者就丢失消息

**改进**: 依赖Redis events列表（已经在做），确保SSE连接时发送所有历史事件

**问题**: 当前代码已经这么做了，但如果前端连接太晚，历史事件回放也无法解决"一次性返回"的用户体验问题

---

### 方案C：延迟工作流开始（不推荐）

**思路**: 上传成功后等待1秒再开始处理

**问题**:
- 人为降低性能
- 治标不治本

---

## 推荐实施：方案A + 优化

### 修改前端代码

```javascript
// DocumentManager.vue
const handleUploadSuccess = (response, file) => {
    ElMessage.success(`${file.name} 上传成功！`)
    
    uploading.value = false
    uploadDialogVisible.value = false
    clearFiles()
    
    // 立即展开任务（触发WorkflowProgress挂载）
    const taskId = response.task_id
    if (taskId) {
        // 创建临时文档对象，立即显示进度
        const tempDoc = {
            task_id: taskId,
            filename: file.name,
            status: 'processing',
            progress: 0,
            created_at: new Date().toISOString()
        }
        
        // 添加到列表顶部
        documents.value.unshift(tempDoc)
        
        // 立即展开
        expandedRows.value = [taskId]
    }
    
    // 延迟刷新列表（更新完整数据）
    setTimeout(fetchDocuments, 500)
}
```

---

## 为什么历史事件回放不够

即使SSE连接时立即发送所有历史事件，如果chunk在0.01秒内完成：

```
历史事件列表:
1. minio start
2. minio end
3. parse start
4. parse end
5. chunk start
6. chunk end     ← 全部一起发送
7. extract start
8. extract end
...
```

前端会在几毫秒内收到所有这些事件，看起来还是"一次性返回"。

**真正的实时推送**需要：
- SSE客户端在第1个事件发送**前**就已经连接
- 这样才能逐个接收事件

---

## 测试验证

### 当前日志应该显示

后端日志应该有：
```
[Pub/Sub] Published node_start for chunk
[Pub/Sub] Published node_end for chunk
```

如果有这些日志，说明后端正确发送了，是前端连接太晚。

### 临时验证方法

手动测试：
1. 上传文档
2. 立即打开Network → EventStream
3. 应该能看到从minio开始的所有事件

如果看到minio start但没有chunk start，说明确实是时序问题。

---

## 当前状态

✅ 后端实现正确
- 节点内部发送start和end
- Redis Pub/Sub实时推送
- 历史事件正确保存

❌ 前端连接时机问题
- 上传成功后延迟100ms
- fetchDocuments需要时间
- WorkflowProgress才开始连接
- 错过了快速执行的节点

---

## 建议行动

**立即可做**（前端修改）:
1. handleUploadSuccess中立即创建临时文档对象
2. 立即展开expandedRows
3. 触发WorkflowProgress立即挂载和连接SSE

**可选**（如果仍有问题）:
1. 在upload API返回前添加100ms延迟（后端）
2. 或者在workflow开始前添加延迟

**最佳方案**:
修改前端，让SSE连接在上传成功的瞬间建立，而不是等待列表刷新。
