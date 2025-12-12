@echo off
REM ==============================================================================
REM Key-Face-Frame - 一键停止脚本 (Windows)
REM ==============================================================================
REM 功能：
REM - 优雅关闭所有服务
REM - 清理进程
REM - 可选：关闭Redis
REM ==============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

REM 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 横幅
echo %BLUE%
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║          Key-Face-Frame - 停止服务                       ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo %NC%

REM 获取项目根目录
cd /d "%~dp0"

REM ==============================================================================
REM 1. 停止前端服务（端口3000）
REM ==============================================================================
echo %BLUE%[INFO]%NC% 停止前端服务...

set FRONTEND_STOPPED=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo %GREEN%[SUCCESS]%NC% 前端服务已停止 (PID: %%a)
        set FRONTEND_STOPPED=1
    )
)

if !FRONTEND_STOPPED!==0 (
    echo %YELLOW%[WARN]%NC% 前端服务未运行
)

REM ==============================================================================
REM 2. 停止Celery Worker
REM ==============================================================================
echo %BLUE%[INFO]%NC% 停止Celery Worker...

tasklist | findstr celery.exe >nul 2>&1
if not errorlevel 1 (
    taskkill /F /IM celery.exe >nul 2>&1
    echo %GREEN%[SUCCESS]%NC% Celery Worker已停止
) else (
    echo %YELLOW%[WARN]%NC% Celery Worker未运行
)

REM 同时尝试通过进程名停止Python celery进程
for /f "tokens=2" %%a in ('tasklist ^| findstr /I "python.*celery"') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul

REM ==============================================================================
REM 3. 停止后端服务（端口8000）
REM ==============================================================================
echo %BLUE%[INFO]%NC% 停止后端服务...

set BACKEND_STOPPED=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo %GREEN%[SUCCESS]%NC% 后端服务已停止 (PID: %%a)
        set BACKEND_STOPPED=1
    )
)

if !BACKEND_STOPPED!==0 (
    echo %YELLOW%[WARN]%NC% 后端服务未运行
)

REM ==============================================================================
REM 4. 询问是否关闭Redis
REM ==============================================================================
echo.
set /p CLOSE_REDIS="是否关闭Redis服务? (y/N): "

if /i "%CLOSE_REDIS%"=="y" (
    echo %BLUE%[INFO]%NC% 关闭Redis服务...
    redis-cli ping >nul 2>&1
    if not errorlevel 1 (
        redis-cli shutdown >nul 2>&1
        timeout /t 1 /nobreak >nul
        echo %GREEN%[SUCCESS]%NC% Redis服务已关闭
    ) else (
        echo %YELLOW%[WARN]%NC% Redis服务未运行
    )
) else (
    echo %BLUE%[INFO]%NC% 保持Redis运行
)

REM ==============================================================================
REM 5. 清理可能遗留的Node进程
REM ==============================================================================
echo %BLUE%[INFO]%NC% 清理遗留进程...

REM 清理Node进程（前端Vite服务器）
for /f "tokens=2" %%a in ('tasklist ^| findstr /I "node.exe"') do (
    REM 检查是否是占用3000端口的进程
    netstat -ano | findstr :3000 | findstr %%a >nul 2>&1
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM 清理Python进程（uvicorn）
for /f "tokens=2" %%a in ('tasklist ^| findstr /I "python.exe"') do (
    REM 检查是否是占用8000端口的进程
    netstat -ano | findstr :8000 | findstr %%a >nul 2>&1
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo %GREEN%[SUCCESS]%NC% 清理完成

REM ==============================================================================
REM 6. 显示停止信息
REM ==============================================================================
echo.
echo %GREEN%╔══════════════════════════════════════════════════════════╗%NC%
echo %GREEN%║                                                          ║%NC%
echo %GREEN%║              ✅ 所有服务已停止！                          ║%NC%
echo %GREEN%║                                                          ║%NC%
echo %GREEN%╚══════════════════════════════════════════════════════════╝%NC%
echo.
echo %BLUE%[INFO]%NC% 下次启动请运行: start.bat
echo.
pause
