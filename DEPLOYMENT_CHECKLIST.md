# 最终部署检查清单 - Ubuntu + NAT

## ✅ 所有修复已完成

### 1. MinIO地址配置
- ✅ 后端连接：`localhost:9000` (内网)
- ✅ view_url使用：`http://103.236.98.149:26766` (外网NAT)

### 2. 核心代码修改
- ✅ `node_minio_upload_after_parse.py` - 硬编码外网地址
- ✅ 删除 `MINIO_PUBLIC_ENDPOINT` 配置
- ✅ 实体提取模型配置 `QWEN_MODEL=qwen-turbo`

---

## 🚀 立即执行的部署步骤

### 步骤1：上传代码到Ubuntu服务器

使用宝塔文件管理器或SCP上传：
```bash
# 上传整个项目到服务器
/www/wwwroot/travel_proj/
```

### 步骤2：配置后端.env

确认 `backend/.env` 配置：
```env
# MinIO - 内网连接
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=travel-documents
MINIO_SECURE=false

# Qwen API
QWEN_MODEL=qwen-turbo
DASHSCOPE_API_KEY=sk-7923b6854f394d699bff143ddf219bd8
```

**注意：** view_url已硬编码为 `http://103.236.98.149:26766`

### 步骤3：启动MinIO服务

```bash
# 在Ubuntu服务器上执行
sudo systemctl start minio
sudo systemctl status minio
```

### 步骤4：设置MinIO公共访问

```bash
cd /www/wwwroot/travel_proj/backend
source ../.venv/bin/activate
python scripts/set_minio_public.py
```

### 步骤5：启动后端服务

**宝塔面板操作：**
1. Python项目管理器 → travel_backend
2. 点击"重启"或"启动"

**验证日志：**
```
[MinIO] Connected to localhost:9000
[SYSTEM] 智能旅行推荐系统启动完成
```

### 步骤6：部署前端

```bash
# 本地构建
cd frontend
npm run build

# 上传dist文件到服务器
# 宝塔文件管理器 → /www/wwwroot/travel_frontend/
```

### 步骤7：配置Nginx

宝塔面板 → 网站 → 配置文件，确认反向代理配置：
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    ...
}
```

### 步骤8：检查NAT转发

确认路由器NAT配置：
- 外网端口 `8856` → 内网服务器:80
- 外网端口 `26766` → 内网服务器:9000

---

## 🎯 测试验证

### 测试1：访问前端
```
http://103.236.98.149:8856
```

### 测试2：访问MinIO测试文件
```
http://103.236.98.149:26766/travel-documents/test-upload.txt
```

应该能看到文本内容。

### 测试3：上传并查看PDF
1. 上传新PDF文档
2. 等待处理完成
3. 点击"查看"按钮
4. 检查浏览器地址栏URL：
   ```
   http://103.236.98.149:26766/travel-documents/文档名/文档名_origin.pdf
   ```
5. PDF应该能正常预览

---

## 📊 预期日志

### 后端日志
```
[MinIO] Connected to localhost:9000, bucket: travel-documents
[UploadMinIO] MinIO公共URL: http://103.236.98.149:26766
[UploadMinIO] 生成的查看URL: http://103.236.98.149:26766/travel-documents/.../_origin.pdf
[Extract] Total extracted: 5 destinations
[Workflow] 6-step workflow completed
```

### Redis数据
```bash
python check_view_url.py
```

应该看到：
```
view_url: http://103.236.98.149:26766/travel-documents/文档名/文档名_origin.pdf
```

---

## 🔍 故障排查

### 如果PDF还是无法查看

**检查1：MinIO是否可外网访问**
```bash
curl http://103.236.98.149:26766/travel-documents/test-upload.txt
```

**检查2：NAT端口转发**
- 路由器配置：外网26766 → 内网9000
- 防火墙：开放9000端口

**检查3：MinIO公共策略**
```bash
python scripts/set_minio_public.py
```

**检查4：view_url格式**
- 必须是：`http://103.236.98.149:26766/...`
- 不能是：`http://localhost:9000/...`

**检查5：浏览器控制台**
- F12 → Console，查看错误信息
- F12 → Network，查看请求的URL

---

## 📋 关键配置文件

### backend/.env
```env
MINIO_ENDPOINT=localhost:9000          # 后端内网连接
QWEN_MODEL=qwen-turbo                  # 实体提取模型
DASHSCOPE_API_KEY=sk-...               # Qwen API密钥
```

### frontend/.env.production
```env
VITE_API_BASE_URL=http://103.236.98.149:8856    # 外网地址
VITE_WS_BASE_URL=ws://103.236.98.149:8856
```

### node_minio_upload_after_parse.py (第171行)
```python
minio_public_url = "http://103.236.98.149:26766"  # 外网NAT地址
```

---

## ✅ 部署完成标志

- [ ] 后端启动成功，日志无错误
- [ ] MinIO外网可访问：`http://103.236.98.149:26766`
- [ ] 前端可访问：`http://103.236.98.149:8856`
- [ ] 上传文档成功
- [ ] 实体提取成功（> 0个景点）
- [ ] 点击"查看"能预览PDF
- [ ] view_url格式正确（包含外网地址）

---

**所有修改已完成，请按步骤部署到Ubuntu服务器并测试！**
