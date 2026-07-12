# SSE事件发送顺序优化

## 修改内容

### workflow_service.py - `_send_step_event`方法

**优化目标**: 先发送实时事件给前端，再存储历史数据

**执行顺序**:
1. ✅ **先**调用`_send_sse_event` → 写入`document:event:{task_id}` (SSE轮询会立即读取)
2. ✅ **再**写入`document:events:{task_id}` (事件历史列表)
3. ✅ **最后**写入`document:progress:{task_id}` (最新进度)

**优势**:
- 前端更快收到实时更新
- 减少延迟
- 保持数据完整性

## 配合修改

### documents.py - SSE端点轮询逻辑

已修改为根据`event_type`字段发送正确的事件类型：
- `event_type: "node_start"` → `event: node_start`
- `event_type: "node_end"` → `event: node_end`
- 其他 → 根据`status`发送`progress`或`step_complete`

## 测试步骤

1. 重启后端服务
2. 上传新文档
3. 观察浏览器开发者工具的Network标签
4. 检查SSE事件是否按顺序接收：
   - node_start (minio)
   - node_end (minio)
   - node_start (parse)
   - node_end (parse)
   - ... 依此类推

## 预期结果

✅ 所有节点的node_start和node_end事件都能实时到达前端
✅ 事件顺序正确
✅ 无延迟或丢失
