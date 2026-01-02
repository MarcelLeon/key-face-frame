# AGENTS.md

> AI助手工作指南 - Key-Face-Frame v2.0

---

## 🚀 快速开始

**一键启动**：
- Mac/Linux: `./start.sh`
- Windows: `start.bat`

**一键停止**：
- Mac/Linux: `./stop.sh`  
- Windows: `stop.bat`

**运行测试**：`./run_tests.sh`

---

## 🏗️ 核心架构

### 三Agent协作系统

```
┌─────────────────┐
│   LeadAgent     │  流程编排、进度追踪
│  (协调器)        │
└────────┬────────┘
         │
    ┌────┴─────┐
    ▼          ▼
┌─────────┐ ┌──────────┐
│Detection│ │Keyframe  │
│Agent    │ │Agent     │
│(检测)   │ │(提取)    │
└─────────┘ └──────────┘
```

**职责划分**：
- `DetectionAgent`：YOLOv8人物检测
- `KeyframeAgent`：关键帧评分与提取（权重：大小40% + 置信度30% + 居中20% + 稳定性10%）
- `LeadAgent`：流程编排与进度追踪

### 异步任务流

```
HTTP请求 → FastAPI → Celery任务 → LeadAgent → [Agents] → 数据库更新
```

### 状态管理

**后端状态**：
- `pending`：已入队，未开始
- `processing`：处理中（包含stage和progress字段）
- `completed`：成功完成
- `failed`：处理失败

**前端状态** (Zustand)：
- 持久化：`currentVideoId`, `config`
- 实时获取：`currentStatus`（轮询API）

---

## ⚠️ 关键提醒

### 必须遵守

1. **从项目根目录运行所有命令**（不要在 `backend/` 目录）
2. **Mac M系列芯片必须使用 `--pool=solo` 启动Celery**
3. **提交代码前必须运行**：`black` + `isort` + `./run_tests.sh`

### 常见错误速查

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `ModuleNotFoundError: backend` | 不在项目根目录 | `cd` 到项目根目录 |
| Celery SIGABRT崩溃 | Mac未使用solo模式 | 使用 `--pool=solo` 参数 |
| Redis连接失败 | Redis未启动 | `redis-cli ping` 检查 |
| 端口被占用 | 旧进程未清理 | 运行 `./stop.sh` |

---

## 📁 重要文件位置

**后端核心**：
- Agent实现：`backend/core/agents/`
  - `lead_agent.py`：流程编排
  - `detection_agent.py`：YOLOv8检测
  - `keyframe_agent.py`：评分提取
- API路由：`backend/api/routes/video.py`
- Celery任务：`backend/workers/tasks.py`
- 配置管理：`backend/core/config.py`

**前端核心**：
- 状态管理：`frontend/src/stores/videoStore.ts`
- API客户端：`frontend/src/api/video.ts`
- 页面路由：`frontend/src/pages/`
  - `Home/`：上传+配置
  - `Processing/`：实时进度
  - `Result/`：关键帧展示

---

## 🔧 开发配置

### 环境变量（.env）

```bash
# 核心配置
CELERY_BROKER_URL=redis://localhost:6379/0
YOLO_MODEL=yolov8m.pt
OUTPUT_DIR=./output
UPLOAD_DIR=./uploads

# 处理参数
DEFAULT_SAMPLE_RATE=5        # 采样率（1-10）
DEFAULT_MAX_FRAMES=20        # 最大关键帧数
DEFAULT_CONFIDENCE=0.5       # 检测置信度阈值
```

### 测试标记

```python
@pytest.mark.unit          # 快速单元测试（<1s）
@pytest.mark.integration   # 集成测试（需真实视频）
@pytest.mark.slow          # 耗时测试（完整流程）
@pytest.mark.requires_model # 需要YOLOv8模型
```

### 代码规范

**格式化**（提交前必须）：
```bash
black backend/ tests/
isort backend/ tests/
```

**类型提示**（必需）：
```python
def process_video(
    self,
    video_path: Path,
    video_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> ProcessingResult:
    ...
```

---

## 📝 用户扩展区域

> 💡 **提示**：在此区域添加项目特定内容，此部分会被Git忽略（配置在 `.gitignore`）

### 个性化开发规划

<!-- 
示例：
- [ ] 优先级1：实现人脸识别功能
- [ ] 优先级2：优化评分算法
- [ ] 技术债务：重构DetectionAgent的错误处理
-->

### 交互方式偏好

<!-- 
示例：
- 代码风格：优先使用dataclass而非dict
- 命名约定：Agent方法统一使用process_前缀
- 日志级别：生产环境使用INFO，开发环境使用DEBUG
-->

### 最佳实践

<!-- 
示例：
- 性能优化：长视频建议sample_rate=10
- 调试技巧：使用logs/目录查看实时日志
- 内存管理：超过1小时的视频分段处理
-->

### 避免的行为

<!-- 
示例：
- ❌ 不要直接修改Agent的输出dataclass定义
- ❌ 不要在Agent之间直接通信（必须通过LeadAgent）
- ❌ 不要跳过代码格式化直接提交
-->

---

## 📚 详细文档

需要深入了解时，查看以下文档：

- **`AGENTS_DETAILED.md`** - 详细架构和实践（本地文件，不提交Git）
- **`README.md`** - 用户文档和安装指南
- **`FAQ.md`** - 常见问题解决方案
- **`MVP_v1.0_SUMMARY.md`** - 架构决策记录
- **API文档** - http://localhost:8000/docs（后端运行时）

---

## 🌏 交流语言

**重要**：后续所有与AI助手的交流均使用**中文**：
- ✅ 文档编写
- ✅ 方案设计
- ✅ 脑暴讨论
- ✅ 代码注释（关键业务逻辑）

---

## 📌 Git提交规则

### 不要提交以下文件

已在 `.gitignore` 中配置，请勿手动添加到Git：

```
# AI CLI相关文档
AGENTS_DETAILED.md
.cursorrules
.github/copilot-instructions.md
.cursor/
.aider*
.agents.local.md

# 运行时生成文件
logs/
*.pid
```

### 提交检查清单

提交代码前确认：
- [ ] 代码已格式化（`black` + `isort`）
- [ ] 测试已通过（`./run_tests.sh`）
- [ ] 无AI助手个人配置文件

---

**最后更新**：2026-01-01  
**文档版本**：v2.0.0
