# ⏱️ SSE时序测试方案

## 目标

测试前后端SSE事件的时间延迟，判断：
1. 后端发送事件的时间点
2. 前端接收事件的时间点
3. 延迟时间（毫秒）

---

## 后端时间戳（已添加）

### **修改：sse_utils.py**

```python
# 发送前记录时间
send_time = time.time()
logger.info(f"[SSE] ⏱️ SEND at {send_time:.3f} | {event_type} - {step_name}")

# 发送到Redis
redis_client.publish(...)

# 发送后确认
logger.info(f"[SSE] ✅ PUBLISHED | {event_type} - {step_name}")
```

**预期日志**:
```
[SSE] ⏱️ SEND at 1783920456.123 | node_start - 查询分析
[SSE] ✅ PUBLISHED | node_start - 查询分析
```

---

## 前端时间戳（需要添加）

### **修改：AIRecommend.vue**

在每个事件监听器中添加时间戳：

```javascript
// 监听node_start事件
eventSource.addEventListener('node_start', (event) => {
  const receiveTime = Date.now() / 1000  // 转换为秒
  const data = JSON.parse(event.data)
  const sendTime = data.timestamp || 0
  const delay = ((receiveTime - sendTime) * 1000).toFixed(0)  // 毫秒
  
  console.log(`⏱️ [RECEIVE] node_start at ${receiveTime.toFixed(3)} | ${data.step_name} | Delay: ${delay}ms`)
  
  executedNodes.value.push({
    name: data.step_name || data.step,
    status: 'primary',
    icon: 'Loading',
    color: '#409eff',
    message: data.message || ''
  })
  scrollToBottom()
})

// 监听node_end事件
eventSource.addEventListener('node_end', (event) => {
  const receiveTime = Date.now() / 1000
  const data = JSON.parse(event.data)
  const sendTime = data.timestamp || 0
  const delay = ((receiveTime - sendTime) * 1000).toFixed(0)
  
  console.log(`⏱️ [RECEIVE] node_end at ${receiveTime.toFixed(3)} | ${data.step_name} | Delay: ${delay}ms`)
  
  const lastNode = executedNodes.value[executedNodes.value.length - 1]
  if (lastNode) {
    lastNode.status = 'success'
    lastNode.icon = 'Check'
    lastNode.color = '#67c23a'
    lastNode.message = data.message || ''
  }
  scrollToBottom()
})

// 监听result事件
eventSource.addEventListener('result', (event) => {
  const receiveTime = Date.now() / 1000
  const data = JSON.parse(event.data)
  const sendTime = data.timestamp || 0
  const delay = ((receiveTime - sendTime) * 1000).toFixed(0)
  
  console.log(`⏱️ [RECEIVE] result at ${receiveTime.toFixed(3)} | Answer: ${data.answer?.length} chars | Delay: ${delay}ms`)
  
  messages.value.push({
    type: 'assistant',
    message: data.answer || '生成答案失败',
    sources: data.sources || [],
    nodes: [...executedNodes.value]
  })
  scrollToBottom()
})

// 监听complete事件
eventSource.addEventListener('complete', (event) => {
  const receiveTime = Date.now() / 1000
  const data = JSON.parse(event.data)
  const sendTime = data.timestamp || 0
  const delay = ((receiveTime - sendTime) * 1000).toFixed(0)
  
  console.log(`⏱️ [RECEIVE] complete at ${receiveTime.toFixed(3)} | Delay: ${delay}ms`)
  console.log(`📊 [SUMMARY] Total events received`)
  
  isLoading.value = false
  
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  
  ElMessage.success('推荐完成')
})
```

---

## 预期测试结果

### **后端日志**
```
[SSE] ⏱️ SEND at 1783920456.123 | node_start - 查询分析
[SSE] ✅ PUBLISHED | node_start - 查询分析
[SSE] ⏱️ SEND at 1783920456.145 | node_end - 查询分析
[SSE] ✅ PUBLISHED | node_end - 查询分析
[SSE] ⏱️ SEND at 1783920456.234 | node_start - 混合检索
[SSE] ✅ PUBLISHED | node_start - 混合检索
...
[AIRecommend] Result event sent
[SSE] ⏱️ SEND at 1783920465.789 | result
[SSE] ✅ PUBLISHED | result
```

### **前端控制台**
```
⏱️ [RECEIVE] node_start at 1783920456.156 | 查询分析 | Delay: 33ms
⏱️ [RECEIVE] node_end at 1783920456.178 | 查询分析 | Delay: 33ms
⏱️ [RECEIVE] node_start at 1783920456.267 | 混合检索 | Delay: 33ms
⏱️ [RECEIVE] node_end at 1783920456.423 | 混合检索 | Delay: 189ms
...
⏱️ [RECEIVE] result at 1783920465.823 | Answer: 1586 chars | Delay: 34ms
⏱️ [RECEIVE] complete at 1783920465.856 | Delay: 33ms
📊 [SUMMARY] Total events received
```

---

## 分析指标

### **正常延迟范围**
- **本地开发**: 10-50ms
- **生产环境**: 50-200ms
- **网络问题**: >500ms

### **异常情况**
- **延迟>1秒**: 网络问题或服务器负载高
- **延迟<0**: 时钟不同步
- **事件丢失**: Redis或SSE连接问题

---

## 测试步骤

### **1. 添加前端时间戳代码**

复制上面的代码到 `AIRecommend.vue` 的事件监听器中。

### **2. 重启服务**

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
npm run dev
```

### **3. 执行测试**

```
1. Ctrl+Shift+R 刷新前端
2. F12 打开控制台
3. 输入查询: "推荐一下三清山的旅游攻略"
4. 观察控制台和后端日志
```

### **4. 记录数据**

创建表格记录：

| 事件类型 | 后端发送时间 | 前端接收时间 | 延迟(ms) |
|---------|------------|------------|---------|
| node_start (查询分析) | xxx.123 | xxx.156 | 33 |
| node_end (查询分析) | xxx.145 | xxx.178 | 33 |
| ... | ... | ... | ... |
| result | xxx.789 | xxx.823 | 34 |
| complete | xxx.823 | xxx.856 | 33 |

### **5. 计算平均延迟**

```
平均延迟 = (所有延迟之和) / 事件数量
```

---

## 诊断建议

### **延迟过大 (>200ms)**

**可能原因**:
1. Redis性能问题
2. 网络延迟
3. 前端事件处理阻塞

**解决方案**:
1. 检查Redis连接
2. 优化事件处理逻辑
3. 减少日志输出

### **事件顺序错乱**

**可能原因**:
1. 异步处理不当
2. 多个workflow并发

**解决方案**:
1. 使用session_id隔离
2. 确保事件串行发送

### **事件丢失**

**可能原因**:
1. Redis连接断开
2. SSE连接中断
3. 事件过期

**解决方案**:
1. 增加Redis超时时间
2. 添加重连机制
3. 增加历史事件保留时间

---

**现在添加前端时间戳代码并测试！** ⏱️
