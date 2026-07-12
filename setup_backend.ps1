# 创建虚拟环境
Write-Host "创建 Python 虚拟环境..." -ForegroundColor Green
Set-Location backend
python -m venv venv

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# 安装依赖
Write-Host "安装 Python 依赖..." -ForegroundColor Green
pip install -r requirements.txt

# 返回项目根目录
Set-Location ..

Write-Host "后端环境配置完成！" -ForegroundColor Green
Write-Host "请配置 backend/.env 文件后运行 start_backend.ps1" -ForegroundColor Yellow
