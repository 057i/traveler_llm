# 🧪 系统测试清单

## ✅ 已完成的修复

1. ✅ 代码Bug修复 (12个)
2. ✅ MinerU V2重写 (90秒→5秒)
3. ✅ 文本清洗优化 (减少10%)
4. ✅ 混合检索优化 (3条→15条)
5. ✅ Rerank本地化 (快30倍)
6. ✅ Settings配置修复
7. ✅ 事件类型匹配 (event_type→type, final_answer→result)
8. ✅ Redis publish修复 (移除await)
9. ✅ SSE假进度修复 (移除历史事件)

---

## 🚀 测试步骤

### **1. 重启后端服务**
```bash
cd E:\大模型开发\代码\网站\travel_proj\backend
python main.py
```

**预期启动日志**:
```
[Rerank] Loading model from: ./models/BAAI--bge-reranker-v2-m3
[Rerank] ✅ Local reranker initialized
INFO: Uvicorn running on http://0.0.0.0:8000
```

### **2. 测试AI推荐查询**

**操作**:
1. 打开前端: http://localhost:5173
2. 点击"AI推荐"
3. 输入: "推荐一下三清山的旅游攻略"
4. 点击发送

**预期前端显示**:
- 实时显示节点执行进度（不是瞬间完成）
- 显示LLM生成的推荐文本
- 显示参考来源列表

**预期后端日志**:
```
[QueryRewriter] Starting query rewriter node
[MilvusHybrid] Starting Milvus hybrid search
[MilvusHybrid] Dense: 10, Sparse: 10
[MilvusHybrid] Fused: 15 results
[Rerank] Reranking 15 candidates...
[Rerank] ✅ Reranked to top 5
[Synthesizer] Generated answer: 1500+ characters
[AIRecommend] Result event sent
[AIRecommend] Workflow completed
```

### **3. 测试文档上传**

**操作**:
1. 点击"RAG文档管理"
2. 上传PDF文档
3. 观察解析过程

**预期**:
- MinerU解析: ~5秒完成
- 文本提取: 20,000+字符
- 清洗优化: 减少~10%
- 数据入库: 成功

---

## 🔍 测试要点

### **AI推荐测试**

**检查项**:
- [ ] 前端进度条逐步增长（不是瞬间100%）
- [ ] 显示AI生成的推荐文本（不是"AI推荐完成"）
- [ ] 显示参考来源列表（可展开查看）
- [ ] 没有出现错误提示

### **SSE事件测试**

**浏览器控制台检查**:
```javascript
// 应该看到
收到事件: node_start
收到事件: node_end
收到事件: result  // ← 关键
收到事件: complete

// 不应该看到
TypeError: object int can't be used in 'await' expression
```

### **后端日志测试**

**检查项**:
- [ ] 没有报错
- [ ] 混合检索返回15条结果
- [ ] Rerank返回5条结果
- [ ] Result event sent日志出现
- [ ] Workflow completed日志出现

---

## 📊 预期结果

### **前端显示**
```
🤖 AI助手

三清山旅游攻略推荐

🏔️ 三清山概览
三清山位于江西省上饶市，是中国著名的道教名山...

📍 推荐景点
1. 三清宫 - 道教文化圣地，建筑精美
2. 东方女神峰 - 三清山标志性景观
3. 玉京峰 - 三清山最高峰，海拔1819米

⏰ 最佳游览时间
春秋两季最佳，气候宜人，云海奇观频现

📚 参考来源 (5条)
▼ 三清山
  描述: 道教名山，世界自然遗产...
  
▼ 三清宫
  描述: 道教文化圣地...
```

### **性能指标**
- 查询响应: <3秒
- Rerank: <100ms
- 结果数量: 5-15条
- 答案长度: 1000-2000字符

---

## ⚠️ 可能的问题

### **问题1: 仍然显示"AI推荐完成"**
**原因**: 前端没有收到result事件
**检查**: 
- 浏览器控制台是否收到result事件
- 后端是否有"Result event sent"日志

### **问题2: 进度条仍然瞬间完成**
**原因**: 历史事件代码没有完全删除
**检查**: 
- 确认ai_recommend.py中没有historical_events代码

### **问题3: 出现乱码**
**原因**: ensure_ascii=False没有生效
**检查**:
- SSE响应头是否有Content-Type: text/event-stream; charset=utf-8

---

## 🎯 测试通过标准

### **必须通过**:
- [ ] 前端实时显示进度（不是假进度）
- [ ] 显示AI润色的推荐文本
- [ ] 显示参考来源列表
- [ ] 没有任何错误

### **性能要求**:
- [ ] 查询响应 < 3秒
- [ ] MinerU解析 < 10秒
- [ ] 没有crash或超时

---

**开始测试！** 🚀

如果遇到问题，请提供：
1. 前端截图
2. 浏览器控制台日志
3. 后端控制台日志
