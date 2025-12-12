# Key-Face-Frame - 商业版 / Commercial Edition

感谢您购买 Key-Face-Frame 商业版！/ Thank you for purchasing Key-Face-Frame Commercial Edition!

这份文档将帮助您快速开始使用商业版本。/ This guide will help you get started with the commercial version.

---

## 📦 快速开始 / Quick Start

### 1. 系统要求 / System Requirements

- **Python**: 3.9+
- **Node.js**: 18+
- **Redis**: 6.0+
- **操作系统 / OS**: macOS, Linux, Windows 10+

### 2. 安装依赖 / Install Dependencies

#### 后端 / Backend
```bash
# 创建虚拟环境 / Create virtual environment
python3 -m venv .venv

# 激活虚拟环境 / Activate virtual environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# 安装依赖 / Install dependencies
pip install -r requirements.txt
```

#### 前端 / Frontend
```bash
cd frontend
npm install
cd ..
```

### 3. 激活许可证 / Activate License

1. 将您购买的许可证密钥复制到 `license.key.example` 文件 / Copy your purchased license key to `license.key.example`
2. 重命名文件为 `license.key` / Rename the file to `license.key`
3. 确保密钥格式为 `KEY-XXXX-XXXX-XXXX` / Ensure the key format is `KEY-XXXX-XXXX-XXXX`

```bash
# 示例 / Example:
echo "KEY-ABCD-1234-EFGH" > license.key
```

**重要提示 / Important:**
- ⚠️ 请勿将 `license.key` 文件提交到 Git / DO NOT commit `license.key` to Git
- 🔒 请妥善保管您的许可证密钥 / Keep your license key safe
- 📧 如需帮助，请联系支持 / For support, please contact us

### 4. 启动服务 / Start Services

#### 使用一键启动脚本 / Using Quick Start Scripts

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

这将自动启动所有服务：/ This will automatically start all services:
- ✅ Redis (如未运行 / if not running)
- ✅ FastAPI 后端 / Backend (端口 8000)
- ✅ Celery Worker (异步任务处理 / async task processing)
- ✅ 前端开发服务器 / Frontend dev server (端口 3000)
- ✅ 自动打开浏览器 / Auto-open browser

#### 手动启动 / Manual Start

如果您需要手动启动各个服务：/ If you need to start services manually:

```bash
# 1. 启动 Redis / Start Redis
redis-server --daemonize yes  # Mac/Linux
redis-server                  # Windows (separate terminal)

# 2. 启动后端 / Start Backend
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 3. 启动 Celery Worker (新终端 / new terminal)
source .venv/bin/activate
celery -A backend.workers.tasks worker --loglevel=info --pool=solo

# 4. 启动前端 (新终端 / new terminal)
cd frontend
npm run dev
```

### 5. 访问应用 / Access Application

- 🌐 **前端 / Frontend**: http://localhost:3000
- 📡 **后端 API / Backend API**: http://localhost:8000
- 📚 **API 文档 / API Docs**: http://localhost:8000/docs

### 6. 停止服务 / Stop Services

**Mac/Linux:**
```bash
./stop.sh
```

**Windows:**
```cmd
stop.bat
```

---

## 🔑 许可证管理 / License Management

### 检查许可证状态 / Check License Status

访问以下端点查看许可证状态：/ Visit the following endpoint to check license status:

```bash
curl http://localhost:8000/api/license
```

**响应示例 / Response Examples:**

**有效许可证 / Valid License:**
```json
{
  "status": "valid",
  "message": "商业版本 (Commercial Edition)",
  "key": "KEY-ABCD-****-****"
}
```

**无效许可证 / Invalid License:**
```json
{
  "status": "invalid",
  "message": "许可证格式无效 (Invalid license format)",
  "help": "请从 Gumroad 获取有效的许可证密钥",
  "purchase_url": "https://gumroad.com/your-product"
}
```

**开源模式 / Open Source Mode:**
```json
{
  "status": "opensource",
  "message": "开源版本 (Open Source Edition)"
}
```

### 许可证验证规则 / License Validation Rules

- ✅ 本地验证，无需网络连接 / Local validation, no network required
- ✅ 格式：`KEY-XXXX-XXXX-XXXX` (大写字母和数字 / uppercase letters and numbers)
- ✅ 如果没有 `license.key` 文件，系统将以开源版本运行 / Without `license.key`, runs as open-source
- ✅ 启动时在日志中显示许可证状态 / License status shown in startup logs

---

## 📖 使用指南 / Usage Guide

### 基本工作流程 / Basic Workflow

1. **上传视频 / Upload Video**
   - 支持格式 / Supported formats: MP4, MOV, AVI, MKV
   - 最大文件大小 / Max file size: 2GB

2. **配置参数 / Configure Parameters**
   - `sample_rate`: 采样率 (每N帧采样一次 / sample every N frames)
   - `max_frames`: 最大关键帧数 / max keyframes
   - `confidence_threshold`: 置信度阈值 / confidence threshold (0.0-1.0)

3. **处理视频 / Process Video**
   - 系统自动检测人脸 / Auto face detection
   - 提取关键帧 / Extract keyframes
   - 实时进度更新 / Real-time progress updates

4. **查看结果 / View Results**
   - 在线浏览关键帧 / Browse keyframes online
   - 下载关键帧图片 / Download keyframe images
   - 查看元数据 (JSON) / View metadata (JSON)

### 高级功能 / Advanced Features

#### 自定义检测配置 / Custom Detection Config

编辑 `backend/core/config.py` 自定义默认参数：/ Edit `backend/core/config.py` to customize defaults:

```python
default_sample_rate: int = 1
default_max_frames: int = 100
default_confidence_threshold: float = 0.5
```

#### 使用不同的 YOLO 模型 / Using Different YOLO Models

```python
# 在 .env 文件中设置 / Set in .env file
YOLO_MODEL=yolov8m.pt  # 可选 / options: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
```

模型越大，准确度越高，但速度越慢 / Larger models = higher accuracy but slower speed

---

## 🚀 部署指南 / Deployment Guide

### 生产环境部署 / Production Deployment

#### 方案 1: Docker (推荐 / Recommended)

```bash
# TODO: Docker 配置将在后续版本中提供 / Docker config coming in future release
```

#### 方案 2: 手动部署 / Manual Deployment

1. **环境配置 / Environment Setup**
```bash
# .env 文件 / .env file
DATABASE_URL=postgresql://user:password@localhost/keyframe
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

2. **使用生产级服务器 / Use Production Server**
```bash
# 使用 gunicorn / Using gunicorn
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用 supervisor 管理进程 / Using supervisor for process management
# TODO: supervisor 配置示例 / supervisor config example
```

3. **前端构建 / Frontend Build**
```bash
cd frontend
npm run build
# 使用 nginx 或其他 web 服务器提供静态文件 / Serve with nginx or other web server
```

---

## 🛠 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. Redis 连接失败 / Redis Connection Failed
```bash
# 检查 Redis 是否运行 / Check if Redis is running
redis-cli ping
# 应返回 PONG / Should return PONG

# 启动 Redis / Start Redis
redis-server --daemonize yes  # Mac/Linux
redis-server                  # Windows
```

#### 2. 端口被占用 / Port Already in Use
```bash
# 查找占用端口的进程 / Find process using port
lsof -ti:8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# 终止进程 / Kill process
kill -9 <PID>  # Mac/Linux
taskkill /F /PID <PID>  # Windows
```

#### 3. 许可证无效 / Invalid License
- 检查 `license.key` 文件是否存在 / Check if `license.key` file exists
- 确保格式为 `KEY-XXXX-XXXX-XXXX` / Ensure format is `KEY-XXXX-XXXX-XXXX`
- 查看启动日志中的错误信息 / Check startup logs for error messages
- 重启服务 / Restart services

#### 4. Celery Worker 未启动 / Celery Worker Not Starting
```bash
# 检查 Redis 连接 / Check Redis connection
# 查看 Celery 日志 / Check Celery logs
tail -f logs/celery.log

# Windows 用户需要使用 --pool=solo / Windows users must use --pool=solo
celery -A backend.workers.tasks worker --loglevel=info --pool=solo
```

### 日志查看 / View Logs

```bash
# 后端日志 / Backend logs
tail -f logs/backend.log

# Celery 日志 / Celery logs
tail -f logs/celery.log

# 前端日志 / Frontend logs
tail -f logs/frontend.log
```

---

## 📞 支持与帮助 / Support & Help

### 获取帮助 / Get Help

- 📧 **邮件支持 / Email Support**: support@your-domain.com
- 💬 **GitHub Issues**: https://github.com/your-username/key-face-frame/issues
- 📖 **文档 / Documentation**: 查看项目 docs/ 目录 / See project docs/ directory

### 许可证相关问题 / License Issues

- 🔑 **丢失许可证 / Lost License**: 请联系支持团队，提供购买凭证 / Contact support with purchase proof
- 🔄 **许可证更新 / License Renewal**: 许可证为一次性购买，终身有效 / One-time purchase, lifetime validity
- 💳 **退款政策 / Refund Policy**: 购买后 30 天内可申请退款 / 30-day refund available

---

## 🎉 感谢使用 / Thank You!

感谢您选择 Key-Face-Frame 商业版！我们致力于提供最好的视频关键帧提取解决方案。

Thank you for choosing Key-Face-Frame Commercial Edition! We're committed to providing the best video keyframe extraction solution.

如有任何问题或建议，请随时联系我们。/ For any questions or suggestions, please feel free to contact us.

---

## 📄 许可证 / License

Key-Face-Frame 商业版受专有许可证保护。/ Key-Face-Frame Commercial Edition is protected by a proprietary license.

- ✅ 允许商业使用 / Commercial use allowed
- ✅ 允许修改和自定义 / Modification and customization allowed
- ✅ 优先技术支持 / Priority technical support
- ❌ 禁止再分发许可证密钥 / License key redistribution prohibited
- ❌ 禁止将软件作为服务转售 / Reselling as SaaS prohibited

完整许可证条款请参阅购买时的许可协议。/ See full license terms in the purchase agreement.

---

**版本 / Version**: 1.0.0
**更新日期 / Last Updated**: 2025-12-13
