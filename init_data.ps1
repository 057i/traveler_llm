Write-Host "初始化数据..." -ForegroundColor Green

Set-Location backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行数据初始化脚本
Write-Host "正在加载景点数据到向量数据库和图数据库..." -ForegroundColor Cyan
python init_data.py

Write-Host "数据初始化完成！" -ForegroundColor Green
