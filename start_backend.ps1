Write-Host "启动后端服务..." -ForegroundColor Green

Set-Location backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 启动 FastAPI 服务
Write-Host "正在启动 FastAPI 服务 (http://localhost:8000)..." -ForegroundColor Cyan
python main.py
