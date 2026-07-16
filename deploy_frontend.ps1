# 前端构建和部署脚本

## 步骤1：构建前端
Write-Host "开始构建前端..." -ForegroundColor Green
cd E:\大模型开发\代码\网站\travel_proj\frontend
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "构建失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 前端构建完成！" -ForegroundColor Green

## 步骤2：显示下一步操作
Write-Host ""
Write-Host "==================== 下一步操作 ====================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 上传 dist 文件夹到服务器："
Write-Host "   本地路径: E:\大模型开发\代码\网站\travel_proj\frontend\dist"
Write-Host "   服务器路径: /www/wwwroot/traveler_llm/dist/"
Write-Host ""
Write-Host "2. 配置Nginx（已生成配置文件）："
Write-Host "   查看: E:\大模型开发\代码\网站\travel_proj\nginx_frontend_config.txt"
Write-Host ""
Write-Host "3. 重启Nginx："
Write-Host "   nginx -s reload"
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
