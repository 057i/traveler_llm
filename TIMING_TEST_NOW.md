# ⏱️ SSE时序测试 - 立即执行

## ✅ 已完成的准备工作

### **后端 (已添加)**
- ✅ 发送时间戳日志: `⏱️ SEND at xxx.xxx`
- ✅ 发布确认日志: `✅ PUBLISHED`

### **前端 (已添加)**
- ✅ 接收时间戳日志: `⏱️ [RECEIVE] xxx at xxx.xxx | Delay: Xms`
- ✅ 所有事件类型: node_start, node_end, result, complete

---

## 🚀 立即测试

### **步骤1: 重启后端**
```bash
cd backend
python main.py
```

### **步骤2: 重启前端**
```bash
cd frontend
npm run dev
```

### **步骤3: 刷新浏览器**
```
Ctrl+Shift+R (强制刷新)
```

### **步骤4: 打开控制台**
```
F12 → Console标签
清空控制台 (右键 → Clear console)
```

### **步骤5: 发起测试**
```
输入: "推荐一下三清山的旅游攻略"
点击发送
```

---

## 📊 预期结果

### **后端日志示例**
```
[SSE] ⏱️ SEND at 1783920456.123 | node_start - 查询分析
[SSE] ✅ PUBLISHED | node_start - 查询分析
[SSE] ⏱️ SEND at 1783920457.456 | node_end - 查询分析
[SSE] ✅ PUBLISHED | node_end - 查询分析
[SSE] ⏱️ SEND at 1783920457.567 | node_start - 混合检索
[SSE] ✅ PUBLISHED | node_start - 混合检索
...
[AIRecommend] Result event sent
[SSE] ⏱️ SEND at 1783920465.789 | complete
[SSE] ✅ PUBLISHED | complete
```

### **前端控制台示例**
```
连接SSE事件流: /api/ai-recommend/events/session_xxx
SSE连接已建立
⏱️ [RECEIVE] node_start at 1783920456.156 | 查询分析 | Delay: 33ms
⏱️ [RECEIVE] node_end at 1783920457.489 | 查询分析 | Delay: 33ms
⏱️ [RECEIVE] node_start at 1783920457.600 | 混合检索 | Delay: 33ms
⏱️ [RECEIVE] node_end at 1783920458.100 | 混合检索 | Delay: 533ms
...
⏱️ [RECEIVE] result at 1783920465.823 | Answer: 1586 chars | Delay: 34ms
⏱️ [RECEIVE] complete at 1783920465.856 | Delay: 67ms
📊 [SUMMARY] Workflow completed
推荐完成
```

---

## 🎯 分析指标

### **延迟分析**

| 指标 | 正常范围 | 异常范围 |
|------|---------|---------|
| 网络延迟 | 10-50ms | >200ms |
| 节点执行 | 50-2000ms | >5000ms |
| 总流程 | 5-10秒 | >20秒 |

### **事件顺序**

**正确顺序**:
```
1. node_start (查询分析)
2. node_end (查询分析)
3. node_start (混合检索)
4. node_end (混合检索)
...
N-1. result (答案)
N. complete (完成)
```

### **时间间隔**

**关键间隔**:
- node_start → node_end: 节点执行时间
- node_end → node_start: 节点间隔（应该很短）
- 最后node_end → result: LLM生成时间
- result → complete: 清理时间（~100ms）

---

## 📝 记录模板

### **测试数据记录**

| 事件 | 后端时间 | 前端时间 | 延迟 | 备注 |
|------|---------|---------|------|------|
| node_start (查询分析) | | | | |
| node_end (查询分析) | | | | |
| node_start (混合检索) | | | | |
| node_end (混合检索) | | | | |
| node_start (附近检索) | | | | |
| node_end (附近检索) | | | | |
| node_start (置信度检查) | | | | |
| node_end (置信度检查) | | | | |
| node_start (网络搜索) | | | | |
| node_end (网络搜索) | | | | |
| node_start (结果融合) | | | | |
| node_end (结果融合) | | | | |
| node_start (智能重排) | | | | |
| node_end (智能重排) | | | | |
| node_start (答案生成) | | | | |
| node_end (答案生成) | | | | |
| result | | | | |
| complete | | | | |

### **统计分析**

```
总事件数: ___
平均延迟: ___ ms
最大延迟: ___ ms
最小延迟: ___ ms
总执行时间: ___ 秒
```

---

## 🔍 问题诊断

### **问题1: 延迟过大 (>500ms)**

**检查**:
- Redis性能
- 网络状况
- 服务器负载

### **问题2: 事件乱序**

**检查**:
- 时间戳是否正确
- 是否有并发请求
- Redis Pub/Sub是否正常

### **问题3: 事件丢失**

**检查**:
- SSE连接是否稳定
- Redis是否丢消息
- 前端是否正确监听

### **问题4: 前端收不到result**

**检查**:
- 后端是否发送了result事件
- 事件类型是否匹配
- 前端监听器是否正确

---

## ✅ 验证清单

测试完成后，确认以下各项：

- [ ] 后端所有日志都有时间戳
- [ ] 前端所有事件都有延迟显示
- [ ] 事件顺序正确
- [ ] 延迟在正常范围内 (<200ms)
- [ ] result事件正确接收
- [ ] 前端显示完整答案
- [ ] 工作流程节点保留显示
- [ ] 参考来源正确显示

---

**现在立即重启服务并测试！记录所有时间数据！** ⏱️
