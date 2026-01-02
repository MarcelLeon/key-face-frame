@echo off
REM ==============================================================================
REM Windows 依赖安装脚本 - 解决预编译包问题
REM ==============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

echo ========================================
echo Windows 依赖安装脚本
echo ========================================
echo.

REM 激活虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

echo.
echo ========================================
echo 方案1: 使用官方PyPI（推荐）
echo ========================================
echo.

REM 尝试从官方PyPI安装（确保获取预编译包）
echo 安装核心依赖（仅使用预编译包）...
pip install --only-binary :all: numpy pillow

if errorlevel 1 (
    echo.
    echo ========================================
    echo 方案2: 使用清华镜像源
    echo ========================================
    echo.
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --only-binary :all: numpy pillow
)

REM 安装PyTorch（使用官方CPU版本）
echo.
echo 安装PyTorch（CPU版本）...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

REM 安装其他依赖
echo.
echo 安装其他依赖...
pip install fastapi[all] uvicorn[standard] pydantic pydantic-settings
pip install celery[redis] redis
pip install sqlalchemy alembic asyncpg
pip install opencv-python ultralytics
pip install python-multipart aiofiles python-dotenv

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 验证安装:
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
echo.
echo 现在可以运行 start.bat 启动项目
echo.
pause
