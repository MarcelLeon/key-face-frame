@echo off
REM ==============================================================================
REM Key-Face-Frame - 一键启动脚本 (Windows)
REM ==============================================================================
REM 功能：
REM - 检查依赖（Python、Node、Redis）
REM - 自动启动Redis（如未运行）
REM - 后台启动FastAPI后端
REM - 后台启动Celery worker
REM - 启动前端开发服务器
REM - 自动打开浏览器
REM - 日志输出到logs\目录
REM ==============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

REM 启用Windows虚拟终端ANSI转义序列支持（Windows 10+）
REM 这将使ANSI颜色代码正常工作
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "ESC=%%b"
)
REM 启用虚拟终端处理
echo [?25l[?25h>nul

REM 颜色定义（Windows 10+支持ANSI颜色）
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 横幅
echo %BLUE%
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║          Key-Face-Frame Pro - 一键启动脚本               ║
echo ║          AI视频关键帧提取工具                             ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo %NC%

REM 获取项目根目录
cd /d "%~dp0"
echo %BLUE%[INFO]%NC% 项目目录: %CD%

REM 创建日志目录
if not exist logs mkdir logs

REM ==============================================================================
REM 1. 检查依赖
REM ==============================================================================
echo %BLUE%[INFO]%NC% 检查系统依赖...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Python 未安装！请先安装Python 3.9+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%[SUCCESS]%NC% Python版本: %PYTHON_VERSION%

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Node.js 未安装！请先安装Node.js 18+
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo %GREEN%[SUCCESS]%NC% Node.js版本: %NODE_VERSION%

REM 检查Redis
redis-server --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARN]%NC% Redis 未安装！
    echo %YELLOW%[WARN]%NC% 请从以下地址下载并安装Redis for Windows:
    echo %YELLOW%[WARN]%NC% https://github.com/microsoftarchive/redis/releases
    pause
    exit /b 1
)
echo %GREEN%[SUCCESS]%NC% Redis 已安装

REM ==============================================================================
REM 2. 检查虚拟环境
REM ==============================================================================
echo %BLUE%[INFO]%NC% 检查Python虚拟环境...

if not exist ".venv" (
    echo %YELLOW%[WARN]%NC% 虚拟环境不存在，正在创建...
    python -m venv .venv
    echo %GREEN%[SUCCESS]%NC% 虚拟环境创建成功
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat
echo %GREEN%[SUCCESS]%NC% 虚拟环境已激活

REM 检查依赖
if not exist ".venv\Scripts\uvicorn.exe" (
    echo %YELLOW%[WARN]%NC% 后端依赖未安装，正在安装...
    pip install -r requirements.txt
    echo %GREEN%[SUCCESS]%NC% 后端依赖安装完成
)

REM ==============================================================================
REM 3. 检查前端依赖
REM ==============================================================================
echo %BLUE%[INFO]%NC% 检查前端依赖...

cd frontend
if not exist "node_modules" (
    echo %YELLOW%[WARN]%NC% 前端依赖未安装，正在安装...
    call npm install
    echo %GREEN%[SUCCESS]%NC% 前端依赖安装完成
)
cd ..

REM ==============================================================================
REM 4. 启动Redis
REM ==============================================================================
echo %BLUE%[INFO]%NC% 检查Redis服务...

redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo %BLUE%[INFO]%NC% 启动Redis服务...
    start /B redis-server --port 6379
    timeout /t 2 /nobreak >nul
    redis-cli ping >nul 2>&1
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% Redis启动失败！
        pause
        exit /b 1
    )
    echo %GREEN%[SUCCESS]%NC% Redis启动成功
) else (
    echo %GREEN%[SUCCESS]%NC% Redis已运行
)

REM ==============================================================================
REM 5. 清理旧进程
REM ==============================================================================
echo %BLUE%[INFO]%NC% 清理旧进程...

REM 清理端口8000（FastAPI）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo %YELLOW%[WARN]%NC% 端口8000被占用，正在清理...
    taskkill /F /PID %%a >nul 2>&1
)

REM 清理端口3000（前端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo %YELLOW%[WARN]%NC% 端口3000被占用，正在清理...
    taskkill /F /PID %%a >nul 2>&1
)

REM 清理Celery进程
taskkill /F /IM celery.exe >nul 2>&1

timeout /t 1 /nobreak >nul
echo %GREEN%[SUCCESS]%NC% 旧进程清理完成

REM ==============================================================================
REM 6. 启动后端服务
REM ==============================================================================
echo %BLUE%[INFO]%NC% 启动FastAPI后端服务...

call .venv\Scripts\activate.bat
start /B cmd /c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs\backend.log 2>&1"

timeout /t 2 /nobreak >nul
netstat -ano | findstr :8000 | findstr LISTENING >nul
if errorlevel 1 (
    echo %RED%[ERROR]%NC% 后端服务启动失败！查看日志: type logs\backend.log
    pause
    exit /b 1
)
echo %GREEN%[SUCCESS]%NC% 后端服务已启动

REM ==============================================================================
REM 7. 启动Celery Worker
REM ==============================================================================
echo %BLUE%[INFO]%NC% 启动Celery任务处理器...

start /B cmd /c "celery -A backend.workers.tasks worker --loglevel=info --pool=solo --without-heartbeat --without-gossip --without-mingle > logs\celery.log 2>&1"

timeout /t 2 /nobreak >nul
echo %GREEN%[SUCCESS]%NC% Celery Worker已启动

REM ==============================================================================
REM 8. 启动前端服务
REM ==============================================================================
echo %BLUE%[INFO]%NC% 启动前端开发服务器...

cd frontend
start /B cmd /c "npm run dev > ..\logs\frontend.log 2>&1"
cd ..

timeout /t 3 /nobreak >nul
echo %GREEN%[SUCCESS]%NC% 前端服务已启动

REM ==============================================================================
REM 9. 等待服务完全启动
REM ==============================================================================
echo %BLUE%[INFO]%NC% 等待服务完全启动...

set RETRY_COUNT=0
set MAX_RETRIES=30
:CHECK_BACKEND
curl -s http://localhost:8000/docs >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! LSS %MAX_RETRIES% (
        echo | set /p=.
        timeout /t 2 /nobreak >nul
        goto CHECK_BACKEND
    ) else (
        echo.
        echo %RED%[ERROR]%NC% 后端服务未能正常启动（等待60秒后超时）
        echo.
        echo %YELLOW%[诊断信息]%NC%
        echo   1. 检查端口8000占用情况:
        netstat -ano | findstr :8000
        echo.
        echo   2. 检查后端进程状态:
        tasklist | findstr python
        echo.
        echo   3. 查看后端日志:
        echo      %YELLOW%type logs\backend.log%NC%
        echo.
        echo %YELLOW%[可能原因]%NC%
        echo   - 后端服务启动较慢，需要更多时间
        echo   - 依赖包安装不完整
        echo   - 端口8000被其他程序占用
        echo   - Python环境配置问题
        echo.
        pause
        exit /b 1
    )
)
echo.
echo %GREEN%[SUCCESS]%NC% 后端服务健康检查通过

REM ==============================================================================
REM 10. 打开浏览器
REM ==============================================================================
echo %BLUE%[INFO]%NC% 自动打开浏览器...

timeout /t 1 /nobreak >nul
start http://localhost:3000

REM ==============================================================================
REM 11. 显示启动信息
REM ==============================================================================
echo.
echo %GREEN%╔══════════════════════════════════════════════════════════╗%NC%
echo %GREEN%║                                                          ║%NC%
echo %GREEN%║              ✅ 服务启动成功！                            ║%NC%
echo %GREEN%║                                                          ║%NC%
echo %GREEN%╚══════════════════════════════════════════════════════════╝%NC%
echo.
echo %BLUE%📊 服务状态:%NC%
echo   %GREEN%✓%NC% 前端:   http://localhost:3000
echo   %GREEN%✓%NC% 后端:   http://localhost:8000
echo   %GREEN%✓%NC% API文档: http://localhost:8000/docs
echo   %GREEN%✓%NC% Redis:  已运行
echo   %GREEN%✓%NC% Celery: 已运行
echo.
echo %BLUE%📁 日志文件:%NC%
echo   - 后端日志:  logs\backend.log
echo   - Celery日志: logs\celery.log
echo   - 前端日志:  logs\frontend.log
echo.
echo %BLUE%🛑 停止服务:%NC%
echo   运行: %YELLOW%stop.bat%NC%
echo.
echo %YELLOW%💡 提示: 关闭此窗口不会停止后台服务，请使用 stop.bat%NC%
echo.
echo %BLUE%[INFO]%NC% 所有服务已在后台运行
echo %BLUE%[INFO]%NC% 查看实时日志: type logs\backend.log
echo.
pause
