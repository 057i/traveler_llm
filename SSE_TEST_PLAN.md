# SSE实时进度完整测试方案

## 测试步骤

### 1. 后端测试
创建测试脚本验证事件发送逻辑

### 2. 前端测试
- 上传新文档
- 观察Network标签的SSE连接
- 验证收到的事件顺序和数量

### 3. 刷新测试
- 在处理过程中刷新页面
- 验证历史事件是否正确回放

## 预期结果

每个节点应该收到2个事件：
1. node_start - 节点开始
2. node_end - 节点完成

总共14个事件（7个节点 × 2）：
1. node_start - minio
2. node_end - minio
3. node_start - parse
4. node_end - parse
5. node_start - chunk
6. node_end - chunk
7. node_start - extract
8. node_end - extract
9. node_start - vectorize_traditional
10. node_end - vectorize_traditional
11. node_start - vectorize_graph
12. node_end - vectorize_graph
13. node_start - finalize
14. node_end - finalize
15. complete事件

## 测试要点

- [ ] 事件无重复
- [ ] 事件顺序正确
- [ ] 实时性好（<200ms延迟）
- [ ] 刷新后能恢复进度
- [ ] 前端UI正确更新
