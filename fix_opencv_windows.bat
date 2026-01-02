@echo off
REM ==============================================================================
REM Windows OpenCV 快速修复脚本
REM ==============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

echo ========================================
echo OpenCV 快速修复脚本 (Windows)
echo ========================================
echo.
echo 此脚本将修复 "ModuleNotFoundError: No module named 'cv2'" 问题
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境！
    echo 请先运行 install_windows.bat 创建虚拟环境
    pause
    exit /b 1
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

echo [1/3] 卸载现有的OpenCV...
pip uninstall -y opencv-python opencv-python-headless 2>nul

echo.
echo [2/3] 安装OpenCV headless版本（Windows推荐）...
pip install --only-binary :all: opencv-python-headless

if errorlevel 1 (
    echo.
    echo [警告] headless版本安装失败，尝试标准版本...
    pip install opencv-python
    
    if errorlevel 1 (
        echo.
        echo [错误] OpenCV安装失败！
        echo.
        echo 请尝试：
        echo 1. 使用清华镜像源：
        echo    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-python-headless
        echo.
        echo 2. 或访问官网下载对应版本的wheel文件手动安装：
        echo    https://pypi.org/project/opencv-python-headless/#files
        pause
        exit /b 1
    )
)

echo.
echo [3/3] 验证安装...
python -c "import cv2; print('✓ OpenCV 安装成功，版本:', cv2.__version__)"

if errorlevel 1 (
    echo.
    echo [错误] OpenCV导入失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ OpenCV 修复完成！
echo ========================================
echo.
echo 现在可以运行 start.bat 启动项目
echo.
pause
