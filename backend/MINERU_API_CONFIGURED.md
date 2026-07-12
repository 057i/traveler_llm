# MinerU API配置完成

## ✅ 已配置

### 1. 环境变量配置

在 `.env` 文件中添加：

```env
# MinerU PDF解析API
MINERU_API_URL=http://localhost:8080/api/parse
MINERU_API_KEY=your_api_key_here  # 如果需要
MINERU_TIMEOUT=300
```

### 2. Settings配置

已在 `config/settings.py` 添加：
- `MINERU_API_URL` - API地址
- `MINERU_API_KEY` - API密钥（可选）
- `MINERU_TIMEOUT` - 超时时间（默认300秒）

### 3. PDF解析节点实现

`node_pdf_parse.py` 现在会：
1. 读取PDF文件
2. 上传到MinerU API
3. 接收Markdown格式结果
4. 处理错误（超时、连接失败等）

## 🔧 MinerU API要求

### 请求格式

```http
POST /api/parse HTTP/1.1
Host: localhost:8080
Content-Type: multipart/form-data
Authorization: Bearer your_api_key_here

file: [PDF文件]
```

### 响应格式

```json
{
  "markdown": "# 文档标题\n\n内容...",
  "pages": 10,
  "status": "success"
}
```

或者：

```json
{
  "content": "# 文档标题\n\n内容...",
  "pages": 10
}
```

或者：

```json
{
  "text": "# 文档标题\n\n内容...",
  "page_count": 10
}
```

**注意：** 代码会自动尝试多个字段名（markdown/content/text）

## 🚀 使用步骤

### 1. 启动MinerU服务

确保MinerU API服务运行在配置的地址上：

```bash
# 示例（根据实际情况调整）
docker run -p 8080:8080 mineru/api
# 或
python mineru_server.py
```

### 2. 配置.env

```bash
cd backend
cp .env.example .env
# 编辑.env，设置MINERU_API_URL
```

### 3. 启动后端

```bash
python main.py
```

### 4. 测试上传

访问 http://localhost:5173/documents 并上传PDF

## 📊 错误处理

代码会处理以下错误：
- ✓ API连接失败
- ✓ 请求超时
- ✓ HTTP错误状态
- ✓ 空响应
- ✓ 文件不存在

所有错误都会记录到日志并显示给用户。

## 🧪 测试API

测试MinerU API是否正常：

```bash
curl -X POST http://localhost:8080/api/parse \
  -F "file=@test.pdf" \
  -H "Authorization: Bearer your_key"
```

## 📝 日志示例

成功时：
```
[PDF] Starting PDF parse with MinerU API
[PDF] Parsing file: 三清山攻略.pdf
[PDF] MinerU API: http://localhost:8080/api/parse
[PDF] Uploading to MinerU API...
[PDF] MinerU API解析成功: 10 页, 5234 字符
```

失败时：
```
[PDF] 无法连接到MinerU API，请检查服务是否启动
[PDF] API地址: http://localhost:8080/api/parse
```

## ✅ 完成清单

- [x] .env配置添加
- [x] settings.py配置
- [x] node_pdf_parse.py实现
- [x] 错误处理
- [x] 日志输出
- [ ] 启动MinerU服务
- [ ] 配置实际的API地址
- [ ] 测试上传PDF

---

**下一步：启动MinerU服务并配置实际的API地址**
