# 🚀 部署文档

## 部署架构

本项目支持多种部署方式：

1. **本地开发部署**
2. **Docker 容器化部署**
3. **生产环境部署**

---

## 1. 本地开发部署

### 环境准备

- Python 3.9+
- Node.js 16+
- Neo4j 5.0+
- Redis (可选)

### 部署步骤

参考 [QUICKSTART.md](../QUICKSTART.md) 进行快速部署。

---

## 2. Docker 容器化部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 构建镜像

**后端 Dockerfile**:

在 `backend/` 目录创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
```

**前端 Dockerfile**:

在 `frontend/` 目录创建 `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5173

# 启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 使用 Docker Compose 部署

```powershell
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build
```

### 访问服务

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **Neo4j 浏览器**: http://localhost:7474

---

## 3. 生产环境部署

### 3.1 后端部署

#### 使用 Gunicorn + Uvicorn

**安装依赖**:

```bash
pip install gunicorn
```

**创建启动脚本** `start_production.sh`:

```bash
#!/bin/bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

**启动服务**:

```bash
chmod +x start_production.sh
./start_production.sh
```

#### 使用 Systemd 管理服务

创建服务文件 `/etc/systemd/system/travel-backend.service`:

```ini
[Unit]
Description=Travel Recommendation Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/travel_proj/backend
Environment="PATH=/var/www/travel_proj/backend/venv/bin"
ExecStart=/var/www/travel_proj/backend/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

**启动服务**:

```bash
sudo systemctl daemon-reload
sudo systemctl start travel-backend
sudo systemctl enable travel-backend
sudo systemctl status travel-backend
```

### 3.2 前端部署

#### 构建生产版本

```bash
cd frontend
npm run build
```

生成的静态文件在 `frontend/dist/` 目录。

#### 使用 Nginx 部署

**Nginx 配置** `/etc/nginx/sites-available/travel`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/travel_proj/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE 支持
    location /api/sse/ {
        proxy_pass http://localhost:8000/api/sse/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**启用配置**:

```bash
sudo ln -s /etc/nginx/sites-available/travel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.3 配置 HTTPS

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3.4 数据库部署

#### Neo4j 生产配置

编辑 `/etc/neo4j/neo4j.conf`:

```conf
# 监听地址
dbms.default_listen_address=0.0.0.0

# 内存配置
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g

# 安全配置
dbms.security.auth_enabled=true
```

#### Redis 生产配置

编辑 `/etc/redis/redis.conf`:

```conf
# 绑定地址
bind 127.0.0.1

# 密码保护
requirepass your_strong_password

# 持久化
save 900 1
save 300 10
save 60 10000
```

---

## 4. 性能优化

### 4.1 后端优化

**使用连接池**:

```python
# 在配置中设置
POOL_SIZE = 20
MAX_OVERFLOW = 10
```

**启用缓存**:

```python
# Redis 缓存推荐结果
CACHE_TTL = 3600  # 1 小时
```

**异步处理**:

```python
# 使用 Celery 进行后台任务处理
```

### 4.2 前端优化

**代码分割**:

```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['element-plus']
        }
      }
    }
  }
})
```

**CDN 加速**:

```html
<!-- 使用 CDN 加载大型库 -->
<script src="https://cdn.jsdelivr.net/npm/vue@3"></script>
```

### 4.3 数据库优化

**Neo4j 索引**:

```cypher
// 创建索引加速查询
CREATE INDEX destination_name FOR (d:Destination) ON (d.name);
CREATE INDEX season_name FOR (s:Season) ON (s.name);
```

**ChromaDB 优化**:

```python
# 使用批量插入
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)
```

---

## 5. 监控和日志

### 5.1 日志配置

**后端日志**:

```python
# 使用 Loguru
logger.add(
    "logs/app_{time}.log",
    rotation="500 MB",
    retention="30 days",
    level="INFO"
)
```

**Nginx 访问日志**:

```nginx
access_log /var/log/nginx/travel_access.log;
error_log /var/log/nginx/travel_error.log;
```

### 5.2 性能监控

**使用 Prometheus + Grafana**:

```python
# 添加 Prometheus 中间件
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

---

## 6. 备份策略

### 6.1 Neo4j 备份

```bash
# 创建备份
neo4j-admin dump --database=neo4j --to=/backup/neo4j-backup.dump

# 恢复备份
neo4j-admin load --from=/backup/neo4j-backup.dump --database=neo4j --force
```

### 6.2 ChromaDB 备份

```bash
# 备份向量存储目录
tar -czf chromadb-backup.tar.gz backend/data/vector_store/
```

---

## 7. 安全配置

### 7.1 环境变量保护

```bash
# 设置文件权限
chmod 600 backend/.env
```

### 7.2 API 访问控制

```python
# 添加 API Key 认证
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")
```

### 7.3 防火墙规则

```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 8. 故障恢复

### 8.1 服务健康检查

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

### 8.2 自动重启

使用 Systemd 的 `Restart=always` 配置。

---

## 9. 部署清单

- [ ] 配置环境变量
- [ ] 安装依赖
- [ ] 配置数据库
- [ ] 初始化数据
- [ ] 配置 Nginx
- [ ] 配置 HTTPS
- [ ] 配置日志
- [ ] 设置备份
- [ ] 配置监控
- [ ] 性能测试

---

## 10. 联系方式

如需部署支持，请联系项目维护者。
