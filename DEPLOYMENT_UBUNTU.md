# Ubuntu + 宝塔 部署指南

## 🖥️ 服务器环境

- **操作系统**: Ubuntu Server
- **面板**: 宝塔Linux面板
- **NAT转发**: 外网通过NAT访问内网服务
- **外网IP**: `103.236.98.149`

---

## 📋 系统架构

```
外网访问 (103.236.98.149)
    ↓ (NAT转发)
内网服务器 (Ubuntu)
    ├── Nginx (端口80) → 转发到后端 (端口8000)
    ├── FastAPI后端 (端口8000)
    ├── MinIO (端口9000)
    ├── Redis (端口6379)
    ├── Milvus (端口19530)
    └── Neo4j (端口7687)
```

---

## 🔧 NAT端口映射配置

### 路由器NAT转发规则

| 外网端口 | 内网IP | 内网端口 | 服务 |
|---------|-------|---------|------|
| 8856 | 服务器内网IP | 80 | Nginx (前端+API) |
| 26766 | 服务器内网IP | 9000 | MinIO |

**重要：** 确保路由器已配置这些端口转发规则。

---

## 🚀 部署步骤

### 一、安装依赖服务

#### 1. 安装宝塔面板

```bash
# Ubuntu安装宝塔
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
sudo bash install.sh
```

#### 2. 安装Redis

```bash
# 宝塔面板 → 软件商店 → Redis → 安装
# 或命令行安装
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### 3. 安装MinIO

```bash
# 下载MinIO
cd /opt
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio

# 创建数据目录
mkdir -p /data/minio

# 创建systemd服务
sudo nano /etc/systemd/system/minio.service
```

**minio.service 内容：**
```ini
[Unit]
Description=MinIO
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/opt/minio

[Service]
WorkingDirectory=/opt
User=root
Group=root

Environment="MINIO_ROOT_USER=minioadmin"
Environment="MINIO_ROOT_PASSWORD=minioadmin"

ExecStart=/opt/minio server /data/minio --console-address ":9001" --address ":9000"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动MinIO
sudo systemctl daemon-reload
sudo systemctl start minio
sudo systemctl enable minio

# 检查状态
sudo systemctl status minio
```

---

### 二、后端部署

#### 1. 上传代码到服务器

```bash
# 使用宝塔文件管理器或命令行上传
# 项目路径建议: /www/wwwroot/travel_proj
```

#### 2. 安装Python和依赖

```bash
# 宝塔面板安装Python 3.10
# 软件商店 → Python版本管理器 → 安装 Python 3.10

# 创建虚拟环境
cd /www/wwwroot/travel_proj
python3.10 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

#### 3. 配置环境变量

编辑 `backend/.env`：

```env
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False

# Qwen API
DASHSCOPE_API_KEY=sk-7923b6854f394d699bff143ddf219bd8
QWEN_MODEL=qwen-turbo

# MinerU API
MINERU_API_TOKEN=eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ...
MINERU_BASE_URL=https://mineru.net/api/v4

# MinIO - 使用内网地址连接
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=travel-documents
MINIO_SECURE=false

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

**注意：** 
- 后端使用 `localhost:9000` 连接MinIO（内网）
- 前端view_url使用外网地址 `103.236.98.149:26766`

#### 4. 配置Python项目管理器

**宝塔面板操作：**
1. 打开 **Python项目管理器**
2. 添加项目：
   - 项目名: `travel_backend`
   - 路径: `/www/wwwroot/travel_proj/backend`
   - Python解释器: `/www/wwwroot/travel_proj/.venv/bin/python3`
   - 启动方式: `命令行`
   - 启动命令: 
     ```bash
     /www/wwwroot/travel_proj/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
     ```
   - 端口: `8000`
3. 点击**启动**

#### 5. 验证后端

```bash
# 检查进程
ps aux | grep uvicorn

# 测试接口
curl http://localhost:8000/docs

# 查看日志
tail -f /www/wwwroot/travel_proj/backend/logs/app.log
```

---

### 三、前端部署

#### 1. 本地构建

在开发机器上构建：

```bash
cd frontend

# 配置生产环境变量
nano .env.production
```

**.env.production 内容：**
```env
# 使用外网地址
VITE_API_BASE_URL=http://103.236.98.149:8856
VITE_WS_BASE_URL=ws://103.236.98.149:8856
```

```bash
# 构建
npm install
npm run build

# 打包dist文件夹
tar -czf dist.tar.gz dist/
```

#### 2. 上传到服务器

```bash
# 使用宝塔文件管理器上传 dist.tar.gz 到服务器

# 解压
cd /www/wwwroot
mkdir travel_frontend
cd travel_frontend
tar -xzf ../dist.tar.gz --strip-components=1
```

#### 3. 配置Nginx

**创建站点配置：**

宝塔面板 → 网站 → 添加站点
- 域名: `103.236.98.149` 或你的域名
- 根目录: `/www/wwwroot/travel_frontend`
- PHP: 纯静态

**编辑Nginx配置：**

宝塔面板 → 网站 → 设置 → 配置文件

```nginx
server {
    listen 80;
    server_name 103.236.98.149;
    
    # 前端静态文件
    root /www/wwwroot/travel_frontend;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API反向代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # SSE事件流 (文档处理进度)
    location /api/documents/events/ {
        proxy_pass http://127.0.0.1:8000/api/documents/events/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

**重启Nginx：**
```bash
sudo systemctl restart nginx
# 或宝塔面板 → 软件商店 → Nginx → 重启
```

---

### 四、MinIO配置

#### 1. 创建存储桶

```bash
cd /www/wwwroot/travel_proj/backend
source ../.venv/bin/activate
python scripts/create_minio_bucket.py
```

#### 2. 设置公共访问策略

```bash
python scripts/set_minio_public.py
```

#### 3. 验证MinIO

```bash
# 内网访问
curl http://localhost:9000

# 外网访问 (通过NAT)
curl http://103.236.98.149:26766
```

---

### 五、修复view_url生成逻辑

**问题：** 后端连接内网MinIO，但view_url需要使用外网地址。

**解决方案：** 在生成view_url时，使用外网地址和端口。

编辑 `backend/app/workflows/document_processing/nodes/node_minio_upload_after_parse.py`：

```python
# 第168行附近
# 构建view_url时使用外网地址
view_url = f"http://103.236.98.149:26766/{bucket}/{folder}{filename}_origin.pdf"
```

或者更灵活的方式，添加环境变量：

编辑 `backend/.env`：
```env
# MinIO内网地址（后端连接用）
MINIO_ENDPOINT=localhost:9000

# MinIO外网地址（生成view_url用）
MINIO_PUBLIC_URL=http://103.236.98.149:26766
```

修改代码：
```python
from config.settings import settings

# 生成view_url时使用公共URL
minio_public_url = os.getenv("MINIO_PUBLIC_URL", f"http://{settings.MINIO_ENDPOINT}")
view_url = f"{minio_public_url}/{bucket}/{folder}{filename}_origin.pdf"
```

---

## ✅ 部署验证

### 1. 检查服务状态

```bash
# Redis
sudo systemctl status redis

# MinIO
sudo systemctl status minio

# Nginx
sudo systemctl status nginx

# 后端
# 宝塔面板 → Python项目 → travel_backend → 查看状态
```

### 2. 端口检查

```bash
# 检查端口监听
sudo netstat -tulpn | grep -E '80|8000|9000|6379'
```

应该看到：
```
tcp    0.0.0.0:80      # Nginx
tcp    0.0.0.0:8000    # 后端
tcp    0.0.0.0:9000    # MinIO
tcp    127.0.0.1:6379  # Redis
```

### 3. NAT转发验证

```bash
# 在外网测试访问
curl http://103.236.98.149:8856
curl http://103.236.98.149:26766
```

### 4. 完整测试流程

1. 访问 `http://103.236.98.149:8856`
2. 上传PDF文档
3. 等待处理完成
4. 点击"查看"按钮
5. PDF应该正常预览

---

## 🔍 排查NAT转发问题

### 检查1：路由器NAT配置

确认路由器已正确配置端口转发：
- 外网端口 `8856` → 内网服务器IP:80
- 外网端口 `26766` → 内网服务器IP:9000

### 检查2：防火墙

```bash
# Ubuntu防火墙
sudo ufw status

# 如果启用，需要开放端口
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp
```

### 检查3：宝塔安全规则

宝塔面板 → 安全 → 放行端口：
- `80` (Nginx)
- `8000` (后端)
- `9000` (MinIO)

---

## 📝 文件权限

```bash
# 确保目录权限正确
sudo chown -R www:www /www/wwwroot/travel_frontend
sudo chown -R root:root /www/wwwroot/travel_proj
sudo chmod -R 755 /www/wwwroot/travel_frontend
sudo chmod -R 755 /www/wwwroot/travel_proj

# MinIO数据目录
sudo chown -R root:root /data/minio
sudo chmod -R 755 /data/minio
```

---

## 🔧 常见问题

### 问题1：外网无法访问

**原因：** NAT转发未配置或防火墙阻止

**解决：**
1. 检查路由器NAT配置
2. 检查服务器防火墙
3. 检查宝塔安全规则

### 问题2：PDF无法查看

**原因：** view_url使用了内网地址

**解决：**
确保view_url使用外网地址：
```
http://103.236.98.149:26766/travel-documents/...
```

### 问题3：API请求失败

**原因：** Nginx反向代理配置错误

**解决：**
检查Nginx配置中的 `proxy_pass` 是否正确指向 `http://127.0.0.1:8000`

---

**部署完成后，所有外网访问都通过 `103.236.98.149` 进行！**
