# ✅ 变量名错误修复

## 问题

```python
NameError: name 'user_query' is not defined
```

第135行使用了未定义的变量`user_query`，但实际变量名是`query`。

---

## 已修复

```python
# 修复前
history_item = {
    "query": user_query,  # ❌ 错误
    ...
}

# 修复后
history_item = {
    "query": query,  # ✅ 正确
    ...
}
```

---

## 🚀 立即测试

### **后端会自动重载（如果使用--reload）**

或者手动重启：
```bash
Ctrl+C 停止
python main.py 重启
```

### **测试查询**
```
刷新前端 Ctrl+Shift+R
输入: "推荐一下三清山的旅游攻略"
```

---

## ✅ 预期结果

**后端日志**:
```
[AIRecommend] Final answer length: 1586 chars
[AIRecommend] Sources count: 3
[AIRecommend] History saved to: ai_recommend:history:session_xxx
[SSE] [ai_recommend] complete with answer (1586 chars)
[AIRecommend] Workflow completed
```

**前端控制台**:
```
💡 Complete event contains answer: 1586 chars
```

**前端页面**:
```
三清山旅游攻略推荐

玉京峰景区是三清山的最高峰...
```

---

**现在测试！应该能正常工作了！** 🎉
