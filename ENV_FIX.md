# ✅ MinerU环境变量配置修复

## 问题

```
ValueError: MINERU_API_TOKEN not set in environment
```

## 原因

`.env`文件中只有`MINERU_API_KEY`，但V2客户端需要`MINERU_API_TOKEN`和`MINERU_BASE_URL`。

## 解决方案

在`.env`文件中添加：

```bash
# MinerU Configuration (PDF 解析)
MINERU_API_KEY=eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ...  # 保留旧的
MINERU_API_TOKEN=eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ...  # V2需要
MINERU_BASE_URL=https://mineru.net/api/v4  # V2需要
```

## 已修复

✅ 添加了`MINERU_API_TOKEN`  
✅ 添加了`MINERU_BASE_URL`  
✅ 保留了`MINERU_API_KEY`（兼容旧代码）

## 现在重启服务

```bash
# 停止当前服务（Ctrl+C）
# 重新启动
python backend/main.py
```

## 测试

```
上传PDF文档
预期: MinerU V2正常工作，5秒完成解析
```

---

**环境变量已配置完成！重启服务即可！** ✅
