# 前端SSE立即连接优化完成

## 修改日期
2026-07-13

## 问题
- 前端在上传成功后延迟连接SSE
- 导致错过快速执行节点的事件（如chunk、extract）

## 解决方案

### 后端修改
✅ **移除500ms延迟** - 恢复最佳性能

### 前端修改
✅ **立即连接SSE** - DocumentManager.vue

---

## 核心改动

### handleUploadSuccess 函数重构

**修改前**:
```javascript
const handleUploadSuccess = (response, file) => {
  ElMessage.success(`${file.name} 上传成功！`)
  uploadDialogVisible.value = false
  
  // 延迟100ms后刷新列表
  setTimeout(async () => {
    await fetchDocuments()
    // 此时才展开文档，WorkflowProgress才开始连接SSE
  }, 100)
}
```

**修改后**:
```javascript
const handleUploadSuccess = (response, file) => {
  ElMessage.success(`${file.name} 上传成功！`)
  uploadDialogVisible.value = false
  
  // 立即创建临时文档对象
  const taskId = response.task_id
  if (taskId) {
    const tempDoc = {
      task_id: taskId,
      filename: file.name,
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString(),
      // ... 其他字段
    }
    
    // 立即添加到列表并展开
    documents.value.unshift(tempDoc)
    expandedRows.value = [taskId]  // 触发WorkflowProgress挂载
  }
  
  // 延迟1秒后刷新完整数据
  setTimeout(async () => {
    await fetchDocuments()
    await fetchStatistics()
  }, 1000)
}
```

---

## 工作流程

### 修改前（有问题）
```
00:00.000  上传成功
00:00.100  开始刷新列表
00:00.200  列表刷新完成
00:00.250  WorkflowProgress挂载
00:00.300  SSE连接建立
00:00.310  后端已执行到chunk ← SSE错过了minio和parse
```

### 修改后（正确）
```
00:00.000  上传成功
00:00.001  创建临时文档对象
00:00.002  添加到列表顶部
00:00.003  设置expandedRows
00:00.004  WorkflowProgress立即挂载
00:00.005  SSE立即连接
00:00.010  后端开始处理
00:00.011  minio node_start ← SSE能收到！
00:00.020  minio node_end
...
01:00.000  刷新列表，更新完整数据
```

---

## 技术细节

### 临时文档对象
创建临时对象是为了：
1. 立即显示在列表中
2. 触发expandedRows更新
3. 导致WorkflowProgress组件挂载
4. WorkflowProgress的onMounted触发connectSSE()

### 为什么延迟1秒刷新
- 给工作流一些执行时间
- 避免频繁刷新列表
- 1秒后获取更完整的数据（如destinations_count）

### expandedRows的关键作用
```vue
<el-table
  :expand-row-keys="expandedRows"
  :row-key="(row) => row.task_id"
>
```

当`expandedRows = [taskId]`时：
1. el-table自动展开该行
2. expand插槽内容渲染
3. WorkflowProgress组件挂载
4. onMounted执行connectSSE()

---

## 预期效果

### 时间线
```
上传点击
  ↓ 0ms
上传完成，返回task_id
  ↓ 5ms
创建临时文档，展开行
  ↓ 10ms
WorkflowProgress挂载，SSE连接
  ↓ 15ms
后端开始处理
  ↓ 20ms
minio node_start → 前端立即收到
  ↓ 30ms
minio node_end → 前端立即收到
  ↓ 40ms
parse node_start → 前端立即收到
  ↓ 12秒
parse node_end → 前端立即收到
  ↓ 12.01秒
chunk node_start → 前端能收到！
  ↓ 12.02秒
chunk node_end → 前端能收到！
```

### 用户体验
1. 上传成功后**立即**看到文档出现在列表顶部
2. 自动展开，显示WorkflowProgress组件
3. **立即**看到"MinIO存储"步骤开始
4. 实时看到每个步骤的进度
5. 不会错过任何事件

---

## 测试验证

### 步骤
1. 启动前端和后端
2. 上传新PDF文档
3. 观察浏览器Network → EventStream

### 验证点
- ✅ 文档立即出现在列表顶部
- ✅ 自动展开显示进度
- ✅ EventStream收到所有事件（包括minio、parse、chunk、extract）
- ✅ 事件时间戳间隔反映真实处理时间
- ✅ 无"一次性返回"现象
- ✅ 1秒后列表数据更新

### 预期EventStream
```
event: node_start
data: {"step": "minio", ...}

event: node_end
data: {"step": "minio", ...}

event: node_start
data: {"step": "parse", ...}

event: node_end
data: {"step": "parse", ...}

event: node_start
data: {"step": "chunk", ...}  ← 能收到了！

event: node_end
data: {"step": "chunk", ...}

event: node_start
data: {"step": "extract", ...}

... (约50秒后)

event: node_end
data: {"step": "extract", ...}

event: node_start
data: {"step": "vectorize_traditional", ...}

event: node_end
data: {"step": "vectorize_traditional", ...}

event: node_start
data: {"step": "vectorize_graph", ...}

event: node_end
data: {"step": "vectorize_graph", ...}

event: node_start
data: {"step": "finalize", ...}

event: node_end
data: {"step": "finalize", ...}

event: complete
data: {"message": "处理完成: 提取了 XX 个景点"}
```

---

## 优势

### 性能
- ✅ 后端无延迟，全速执行
- ✅ 前端立即响应，无等待

### 用户体验
- ✅ 上传后立即看到反馈
- ✅ 实时进度更新
- ✅ 不会错过任何步骤

### 架构
- ✅ 前后端分离清晰
- ✅ SSE连接生命周期正确
- ✅ 数据最终一致性（临时对象→真实数据）

---

## 注意事项

### 临时对象的字段
确保临时对象包含所有必要字段：
- task_id（必须）
- filename
- status
- progress
- created_at
- destinations_count
- pages_count
- province
- city

缺少字段可能导致UI显示错误。

### expandedRows更新
使用赋值而不是push：
```javascript
expandedRows.value = [taskId]  // ✅ 正确，触发响应式更新
// expandedRows.value.push(taskId)  // ❌ 可能不触发重新渲染
```

### 刷新时机
1秒后刷新是合理的：
- 不会太快（避免与临时对象冲突）
- 不会太慢（用户能看到更新）

---

## 完成状态

✅ **所有修改已完成**

- 后端：移除延迟
- 前端：立即连接SSE
- 清理：删除旧代码残留

**下一步**：测试验证实时性！
