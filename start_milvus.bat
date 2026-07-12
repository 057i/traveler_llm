@echo off
REM Milvus Standalone 启动脚本

echo ========================================
echo Milvus Standalone 启动脚本
echo ========================================
echo.

REM 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo [1/4] 检查Milvus容器是否存在...
docker ps -a | findstr milvus-standalone >nul
if errorlevel 1 (
    echo [信息] Milvus容器不存在，创建新容器...
    echo.
    echo [2/4] 拉取Milvus镜像...
    docker pull milvusdb/milvus:latest

    echo.
    echo [3/4] 创建并启动Milvus容器...
    docker run -d ^
        --name milvus-standalone ^
        -p 19530:19530 ^
        -p 9091:9091 ^
        -v milvus_data:/var/lib/milvus ^
        milvusdb/milvus:latest

    if errorlevel 1 (
        echo [错误] Milvus容器创建失败
        pause
        exit /b 1
    )

    echo [成功] Milvus容器已创建
) else (
    echo [信息] Milvus容器已存在
    echo.
    echo [2/4] 启动Milvus容器...
    docker start milvus-standalone

    if errorlevel 1 (
        echo [错误] Milvus容器启动失败
        pause
        exit /b 1
    )

    echo [成功] Milvus容器已启动
)

echo.
echo [4/4] 等待Milvus服务启动 (30秒)...
timeout /t 30 /nobreak

echo.
echo ========================================
echo Milvus已启动完成
echo ========================================
echo.
echo 服务地址: localhost:19530
echo 管理端口: localhost:9091
echo.
echo 下一步:
echo   1. cd backend
echo   2. python clean_milvus.py (清空数据)
echo   3. python main.py (启动后端)
echo.
pause
