Write-Host "启动前端服务..." -ForegroundColor Green

Set-Location frontend

# 启动 Vite 开发服务器
Write-Host "正在启动 Vite 开发服务器 (http://localhost:5173)..." -ForegroundColor Cyan
npm run dev
