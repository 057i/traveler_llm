# 使用 UV 启动项目

## 后端启动

### 方式一：使用 PowerShell 脚本（推荐）

直接运行启动脚本：
```powershell
.\start_backend.ps1
```

### 方式二：使用 uv run 命令

```powershell
cd backend
uv run python main.py
```

或者从项目根目录：
```powershell
uv run --directory backend python main.py
```

### 方式三：激活虚拟环境后运行

```powershell
# 激活虚拟环境
.venv\Scripts\activate

# 启动后端
cd backend
python main.py
```

## 前端启动

### 方式一：使用 PowerShell 脚本（推荐）

直接运行启动脚本：
```powershell
.\start_frontend.ps1
```

### 方式二：使用 npm

```powershell
cd frontend
npm run dev
```

## 一键启动所有服务

### 使用主启动脚本

```powershell
.\main.py
```

这会同时启动后端和前端服务。

## 安装依赖

### 后端依赖

```powershell
# 确保 UV_LINK_MODE 环境变量已设置
$env:UV_LINK_MODE = "copy"

# 安装后端依赖
uv pip install -r backend/requirements.txt

# 升级到兼容版本
uv pip install "pydantic>=2.0,<3.0" "langchain>=0.3.0" "langchain-core>=0.3.0" "langchain-community>=0.3.0" "sentence-transformers>=3.0.0"
```

### 前端依赖

```powershell
cd frontend
npm install
```

## 常见问题

### 1. 虚拟环境损坏

如果虚拟环境出现问题，重新创建：

```powershell
# 停止所有Python进程
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*travel_proj*" } | Stop-Process -Force

# 重新创建虚拟环境
uv venv --clear

# 重新安装依赖
uv pip install -r backend/requirements.txt
```

### 2. 端口被占用

检查并停止占用端口的进程：

```powershell
# 检查8000端口（后端）
netstat -ano | findstr :8000

# 检查5174端口（前端）
netstat -ano | findstr :5174

# 停止进程（替换 <PID> 为实际进程ID）
Stop-Process -Id <PID> -Force
```

### 3. 依赖版本冲突

确保使用兼容的版本：

```powershell
uv pip install --upgrade "sentence-transformers>=3.0.0" "huggingface-hub>=0.20.0"
```

## 服务地址

- **后端服务**: http://localhost:8000
- **后端API文档**: http://localhost:8000/docs
- **前端服务**: http://localhost:5174
- **健康检查**: http://localhost:8000/health

## 开发建议

1. **使用 uv 管理依赖**: 速度更快，更可靠
2. **定期更新依赖**: `uv pip list --outdated`
3. **使用虚拟环境**: 隔离项目依赖
4. **查看日志**: 使用 `loguru` 的日志输出诊断问题
