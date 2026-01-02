# Key-Face-Frame v2.0

**视频人物关键帧提取工具** - 从视频中自动检测人物，智能提取高质量关键帧

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/MarcelLeon/key-face-frame)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6.svg)](https://www.typescriptlang.org/)

## 🎉 v2.0 完整Web应用已上线！

从命令行工具升级为**完整的Web应用**，提供现代化的用户体验。

### ✨ 核心特性

- 🎯 **智能检测**: YOLOv8人物检测，精准识别视频中的人物
- 📊 **多维评分**: 人物大小(40%) + 置信度(30%) + 居中度(20%) + 稳定性(10%)
- 🚀 **实时进度**: 动态轮询机制，实时显示处理进度和当前阶段
- 📤 **拖拽上传**: 支持拖拽和点击上传，最大500MB
- ⚙️  **灵活配置**: 3个预设模板 + 自定义参数（采样率、关键帧数、置信度）
- 🖼️ **关键帧画廊**: 响应式网格布局，支持按评分/时间排序
- 💾 **批量下载**: ZIP打包下载所有关键帧
- 🍎 **Apple Silicon**: 原生支持M系列芯片MPS加速

### 📸 界面预览

**Web界面**:
<img width="1333" height="945" alt="上传界面" src="https://github.com/user-attachments/assets/a674698b-7f1e-4000-b604-ab9fbd26cf70" />
<img width="1246" height="948" alt="结果展示" src="https://github.com/user-attachments/assets/2e1b8af3-e566-4747-93fa-72ddf87d24aa" />

**提取效果**（以《凡人重返天南16集》预告为例）:
<img width="715" height="398" alt="关键帧1" src="https://github.com/user-attachments/assets/5d3016d9-0fc8-4ae8-8893-5d89388da13f" />
<img width="712" height="398" alt="关键帧2" src="https://github.com/user-attachments/assets/b407e722-bdf1-42ad-b3f6-7c6cf3ce03f0" />
<img width="718" height="398" alt="关键帧3" src="https://github.com/user-attachments/assets/0ca4ac18-7176-47c9-813a-a6dde22c355f" />
<img width="713" height="403" alt="关键帧4" src="https://github.com/user-attachments/assets/540fb9f2-66dd-46a5-9cd1-b0dd9519d696" />

## 🚀 快速开始

> 💡 **首次使用？** 克隆项目后直接运行 `./start.sh`（Mac/Linux）或 `start.bat`（Windows），脚本会自动完成所有设置！

### 系统要求

- **Python**: 3.10+
- **Node.js**: 20+（仅前端）
- **Redis**: 5.0+（用于任务队列）
- **操作系统**: macOS（推荐M系列芯片）、Linux 或 Windows
- **内存**: 至少4GB可用内存

**Windows用户**：
- 支持Windows 10/11
- 需要安装 [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- 使用 `start.bat` 一键启动脚本

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/MarcelLeon/key-face-frame.git
cd key-face-frame
```

#### 2. 后端设置

**安装Python依赖**:
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 首次运行会自动下载YOLOv8模型（约50MB）
```

**安装并启动Redis**:
```bash
# macOS (使用Homebrew)
brew install redis
redis-server --daemonize yes

# 或使用系统服务
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis

# 验证Redis运行
redis-cli ping  # 应返回: PONG
```

#### 3. 前端设置

```bash
cd frontend
npm install
```

### 启动应用

#### 方式1：一键启动（推荐）⭐

**最简单的启动方式**，自动启动所有服务：

**Mac/Linux**:
```bash
./start.sh
```

**Windows**:
```bash
start.bat
```

**一键启动脚本功能**：
- ✅ 自动检查依赖（Python、Node.js、Redis）
- ✅ 自动安装缺失的依赖包
- ✅ YOLOv8模型下载提示（首次运行）
- ✅ 自动启动所有服务（后端、Celery、前端、Redis）
- ✅ Mac M系列芯片自动使用 `--pool=solo` 优化
- ✅ 健康检查和自动打开浏览器
- ✅ 日志输出到 `logs/` 目录

**停止服务**：

**Mac/Linux**:
```bash
./stop.sh
```

**Windows**:
```bash
stop.bat
```

**查看日志**：
```bash
# 后端日志
tail -f logs/backend.log

# Celery日志
tail -f logs/celery.log

# 前端日志
tail -f logs/frontend.log
```

---

#### 方式2：手动启动（传统方式）

**需要启动4个服务**（推荐使用4个终端窗口）:

<details>
<summary>点击展开手动启动步骤</summary>

##### 终端1: FastAPI后端
```bash
cd /path/to/key-face-frame
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

##### 终端2: Celery Worker
```bash
cd /path/to/key-face-frame
source .venv/bin/activate

# macOS M系列芯片必须使用 --pool=solo 参数
celery -A backend.workers.tasks worker --loglevel=info --pool=solo

# 其他系统可以使用默认模式
# celery -A backend.workers.tasks worker --loglevel=info
```

**重要提示（macOS M系列芯片用户）**:
- 必须使用 `--pool=solo` 参数避免MPS与prefork模式的冲突
- 详见 [FAQ.md](FAQ.md#q3-celery-worker崩溃-worker-exited-prematurely-signal-6-sigabrt)

##### 终端3: Redis（如果未使用系统服务）
```bash
redis-server
```

##### 终端4: 前端开发服务器
```bash
cd frontend
npm run dev
```

</details>

---

**访问应用**: http://localhost:3000

### 生产环境部署

```bash
# 构建前端
cd frontend
npm run build

# 启动后端（会自动服务静态文件）
cd ../
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 📖 使用指南

### Web界面使用流程

1. **选择处理模式**
   - 快速模式：采样率10，10个关键帧
   - 标准模式：采样率5，20个关键帧（推荐）
   - 高质量模式：采样率1，50个关键帧

2. **上传视频**
   - 拖拽视频到上传区域，或点击选择文件
   - 支持格式：MP4、MOV、AVI、MKV
   - 文件大小限制：500MB

3. **实时监控**
   - 自动跳转到处理页面
   - 实时显示进度（0-100%）
   - 显示当前阶段（检测中/提取中）
   - 显示元数据（总帧数、检测数、处理时间）

4. **查看结果**
   - 处理完成后自动跳转到结果页
   - 查看所有关键帧（网格布局）
   - 点击任意帧放大预览
   - 按评分或时间排序
   - 下载所有关键帧（ZIP）

### 命令行使用（Python API）

仍然支持v1.0的命令行方式：

```python
import asyncio
from pathlib import Path
from backend.core.agents.detection_agent import DetectionAgent
from backend.core.agents.keyframe_agent import KeyframeAgent
from backend.core.agents.lead_agent import LeadAgent

async def main():
    detection_agent = DetectionAgent(model_name="yolov8m.pt")
    keyframe_agent = KeyframeAgent(output_dir=Path("output"))
    lead_agent = LeadAgent(detection_agent, keyframe_agent)

    result = await lead_agent.process_video(
        video_path=Path("your_video.mp4"),
        video_id="my-video",
        config={
            "sample_rate": 5,
            "max_frames": 20,
            "confidence_threshold": 0.5
        }
    )

    print(f"提取了 {result.keyframes_extracted} 个关键帧")
    print(f"输出目录: {result.keyframe_dir}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ 技术架构

### 技术栈

**后端**:
- FastAPI 0.109.0 - Web框架
- SQLAlchemy 2.0.25 - ORM
- Celery 5.3.6 - 异步任务队列
- Redis 5.0.1 - 消息队列
- YOLOv8 8.1.18 - 人物检测
- OpenCV 4.9.0 - 图像处理
- PyTorch 2.2.0 - 深度学习框架

**前端**:
- React 18 - UI框架
- TypeScript 5 - 类型安全
- Vite 5 - 构建工具
- Ant Design 5 - UI组件库
- Zustand 4 - 状态管理
- Axios 1 - HTTP客户端
- React Router 6 - 路由管理

### 核心架构

```
Frontend (React + TS)
    ↓ HTTP
FastAPI (REST API)
    ↓
Celery Worker
    ↓
LeadAgent (协调器)
    ├─> DetectionAgent (YOLOv8)
    └─> KeyframeAgent (评分+提取)
    ↓
Output (JPEG + metadata.json)
```

## 📊 性能参考

基于Mac M4测试数据：

| 视频时长 | 分辨率 | 采样率 | 检测数 | 关键帧 | 处理时间 |
|---------|--------|--------|--------|--------|----------|
| 30秒    | 1080p  | 5      | 81     | 20     | ~3.5秒   |
| 60秒    | 1080p  | 5      | 150+   | 20     | ~7秒     |
| 120秒   | 1080p  | 10     | 200+   | 30     | ~10秒    |

## 📁 输出结构

```
output/
└── video-{video_id}/
    ├── keyframes/
    │   ├── frame_00045_t2.81s.jpg
    │   ├── frame_00135_t8.44s.jpg
    │   └── ...
    └── metadata.json
```

**metadata.json示例**:
```json
{
  "video_id": "my-video",
  "total_frames": 790,
  "total_detections": 123,
  "keyframes_extracted": 20,
  "processing_time_seconds": 7.08,
  "keyframes": [
    {
      "frame_index": 130,
      "timestamp": 5.2,
      "score": 0.880,
      "bbox": [460.99, 4.19, 1419.37, 1065.93],
      "filename": "frame_00130_t5.20s.jpg"
    }
  ]
}
```

## 🐛 故障排查

### 常见问题

遇到问题？请查看 **[FAQ.md](FAQ.md)** 获取详细的故障排查指南，包括：

- Redis和Celery安装配置问题
- macOS M芯片MPS崩溃解决方案
- 前端路由和Ant Design警告
- 视频处理问题排查
- 性能优化建议

### 查看日志

**后端日志**:
```bash
# FastAPI日志（在运行uvicorn的终端）
# Celery worker日志（在运行celery的终端）

# 或使用debug模式查看详细日志
celery -A backend.workers.tasks worker --loglevel=debug
```

**前端日志**:
- 打开浏览器开发者工具（F12）
- 查看Console标签页
- 查看Network标签页的API请求

## 🧪 测试

```bash
# 运行所有测试
./run_tests.sh

# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v -m slow

# E2E测试
pytest tests/e2e/ -v
```

## 🗺️ 路线图

### v2.1 - 功能增强
- [ ] 历史记录页面
- [ ] 批量处理多个视频
- [ ] 视频预览功能
- [ ] 关键帧编辑和标注

### v3.0 - 高级功能
- [ ] 人脸识别（区分不同人物）
- [ ] 场景检测
- [ ] 视频剪辑功能
- [ ] 用户认证和多用户支持

## 🤝 贡献指南

欢迎提Issue和PR！请确保：

1. 代码通过`black`和`isort`格式化
2. 新功能有对应的测试
3. 前端遵循TypeScript严格模式
4. 添加清晰的注释和文档

## 📄 许可证

MIT License

## 📧 联系方式

- Issues: [GitHub Issues](https://github.com/MarcelLeon/key-face-frame/issues)
- Email: wangzq0708@gmail.com

## 💖 赞助支持 / Sponsor

如果这个项目对你有帮助，欢迎赞助支持开发！🥰

<p align="center">
支付宝Alipay:<img src="docs/images/alipay.png" width="200" alt="支付宝" />
微信支付Wechat<img src="docs/images/wechat.png" width="200" alt="微信支付" />
</p>

---

**版本**: v2.0.0  
**最后更新**: 2026-01-02  
**注意**: 本项目仅用于学习和研究。处理视频时请遵守相关版权法律。
