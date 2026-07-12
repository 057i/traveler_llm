# MinerU 线上API配置

## ✅ 使用线上版本（无需本地部署）

### 1. 获取API密钥

访问MinerU官网获取API密钥：
- 官网：https://mineru.com （示例地址）
- 注册账号
- 获取API Key

### 2. 配置.env

```env
# MinerU线上API
MINERU_API_URL=https://api.mineru.com/v1/parse
MINERU_API_KEY=your_actual_api_key_here
MINERU_TIMEOUT=300
```

### 3. API说明

**端点：** `POST https://api.mineru.com/v1/parse`

**请求头：**
```
Authorization: Bearer your_api_key
Content-Type: multipart/form-data
```

**请求体：**
```
file: [PDF文件]
```

**响应示例：**
```json
{
  "markdown": "# 文档内容\n\n段落内容...",
  "pages": 10,
  "status": "success"
}
```

### 4. 优势

✅ 无需本地部署
✅ 高性能云端处理
✅ 自动更新
✅ 稳定可靠
✅ 按量付费

### 5. 使用流程

```
用户上传PDF
    ↓
后端读取文件
    ↓
上传到MinerU云端API
    ↓
等待处理（1-30秒）
    ↓
获取Markdown结果
    ↓
继续后续处理
```

### 6. 错误处理

代码已包含完整的错误处理：
- API密钥无效
- 网络连接失败
- 请求超时
- 文件格式错误
- 配额不足

所有错误都会记录并显示给用户。

### 7. 测试

配置完成后，上传PDF文件测试：

1. 启动后端：`python main.py`
2. 访问：http://localhost:5173/documents
3. 上传PDF文件
4. 观察日志：

成功：
```
[PDF] Starting PDF parse with MinerU API
[PDF] MinerU API: https://api.mineru.com/v1/parse
[PDF] Uploading to MinerU API...
[PDF] MinerU API解析成功: 10 页, 5234 字符
```

失败：
```
[PDF] MinerU API returned status 401
[PDF] 请检查API密钥是否正确配置
```

---

**注意：请替换为实际的MinerU API地址和密钥**

如果MinerU官方API地址不同，请在.env中修改`MINERU_API_URL`
