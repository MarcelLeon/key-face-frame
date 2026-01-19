# Windows 用户安装指南

## 问题说明

Windows平台可能遇到以下问题：
- NumPy等包尝试从源码编译，但缺少C编译器
- 公司内网PyPI源可能没有最新的预编译包

## 解决方案

### 方案1：使用专用安装脚本（推荐）⭐

直接运行Windows专用安装脚本：

```cmd
install_windows.bat
```

这个脚本会：
1. 创建虚拟环境
2. 升级pip
3. 从官方PyPI安装预编译包
4. 如果失败，自动切换到清华镜像源
5. 单独安装PyTorch（使用CPU版本）
6. 验证安装结果

**安装完成后**，再运行：
```cmd
start.bat
```

### 方案2：手动安装

如果自动脚本失败，手动执行以下步骤：

```cmd
# 1. 创建虚拟环境
python -m venv .venv
call .venv\Scripts\activate.bat

# 2. 升级pip
python -m pip install --upgrade pip

# 3. 安装NumPy（仅使用预编译包）
pip install --only-binary :all: numpy

# 4. 如果上面失败，使用清华镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy

# 5. 安装PyTorch（CPU版本）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 6. 安装其他依赖
pip install -r requirements.txt
```

### 方案3：配置pip使用镜像源

创建配置文件 `%APPDATA%\pip\pip.ini`：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

然后正常运行：
```cmd
start.bat
```

## 常见问题

### Q: 为什么会尝试编译NumPy？

A: 因为pip从PyPI下载了源码包（.tar.gz）而不是预编译包（.whl）。使用 `--only-binary :all:` 参数强制使用预编译包。

### Q: ModuleNotFoundError: No module named 'cv2'

A: Windows上OpenCV可能安装失败。解决方法：

```cmd
call .venv\Scripts\activate.bat

# 卸载现有的opencv-python
pip uninstall -y opencv-python opencv-python-headless

# 安装headless版本（Windows兼容性更好）
pip install --only-binary :all: opencv-python-headless

# 验证安装
python -c "import cv2; print('OpenCV:', cv2.__version__)"
```

**注意**：`install_windows.bat` 已自动使用 `opencv-python-headless`。如果之前安装失败，请删除虚拟环境重新运行脚本。

### Q: 公司内网源没有预编译包怎么办？

A: 
1. 使用 `install_windows.bat`（会自动切换到公网镜像源）
2. 或临时切换pip源：
   ```cmd
   pip install -i https://pypi.org/simple --only-binary :all: numpy torch
   ```

### Q: 已经安装失败了怎么办？

A: 删除虚拟环境重新安装：
```cmd
rmdir /s .venv
install_windows.bat
```

### Q: Celery报错 "拒绝访问" 或 "句柄无效"

A: Windows 下 Celery 需要特殊参数。请使用 `start.bat` 一键启动，或手动启动时使用:

```cmd
celery -A backend.workers.tasks worker --loglevel=info --pool=solo --without-heartbeat --without-gossip --without-mingle
```

## 验证安装

安装完成后验证：

```cmd
call .venv\Scripts\activate.bat
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
```

应该看到版本号输出，没有错误。特别注意 **OpenCV必须成功导入**，否则后端无法启动。

## 技术说明

### 为什么Windows需要特殊处理？

1. **NumPy 2.x** 需要C编译器从源码构建
2. Windows默认不包含C编译器（需要Visual Studio）
3. PyPI的预编译包（wheel）可以直接安装，无需编译

### 依赖安装顺序

```
1. numpy (预编译)
2. pillow (预编译)  
3. torch + torchvision (官方CPU版本)
4. opencv-python-headless (预编译，Windows推荐)
5. 其他纯Python包
```

按这个顺序可以避免编译问题。

**opencv-python vs opencv-python-headless:**
- `opencv-python`: 包含GUI功能（cv2.imshow等），Windows上可能依赖缺失
- `opencv-python-headless`: 无GUI依赖，服务器环境推荐，Windows兼容性更好
- 本项目只需要图像处理功能，headless版本完全满足需求
