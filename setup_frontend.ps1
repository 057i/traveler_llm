# 安装前端依赖
Write-Host "安装前端依赖..." -ForegroundColor Green
Set-Location frontend
npm install

# 返回项目根目录
Set-Location ..

Write-Host "前端环境配置完成！" -ForegroundColor Green
Write-Host "运行 start_frontend.ps1 启动前端服务" -ForegroundColor Yellow
