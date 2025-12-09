# 常见问题（FAQ）

## 安装和配置问题

### Q1: 启动后端时报错 "ModuleNotFoundError: No module named 'backend'"

**症状**:
```
ModuleNotFoundError: No module named 'backend'
```

**原因**: uvicorn需要从项目根目录启动，而不是从backend目录启动。

**解决方案**:
```bash
# ❌ 错误 - 从backend目录启动
cd backend
uvicorn main:app --reload

# ✅ 正确 - 从项目根目录启动
cd /path/to/key-face-frame
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Q2: 上传视频后报错 "Failed to start processing"

**症状**: 视频上传成功但无法开始处理，提示"Failed to start processing"

**原因**: Redis服务器或Celery worker未启动

**解决方案**:

1. **检查Redis是否运行**:
```bash
# 测试Redis连接
redis-cli ping
# 应该返回: PONG
```

2. **启动Redis（如果未安装）**:
```bash
# macOS (使用Homebrew)
brew install redis
redis-server --daemonize yes

# 或使用系统服务
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

3. **启动Celery worker**:
```bash
cd /path/to/key-face-frame
source .venv/bin/activate

# 对于macOS M系列芯片，必须使用 --pool=solo 参数
celery -A backend.workers.tasks worker --loglevel=info --pool=solo
```

---

### Q3: Celery worker崩溃 "Worker exited prematurely: signal 6 (SIGABRT)"

**症状**:
```
/AppleInternal/Library/BuildRoots/.../MPSLibrary.mm:500: failed assertion
Worker exited prematurely: signal 6 (SIGABRT)
```

**原因**: Apple Silicon (M系列芯片)上MPS与Celery的默认prefork模式不兼容

**解决方案**: 使用`--pool=solo`参数启动Celery

```bash
# ✅ 正确 - 使用solo模式（适用于macOS M系列芯片）
celery -A backend.workers.tasks worker --loglevel=info --pool=solo

# ❌ 错误 - 默认prefork模式会在M芯片上崩溃
celery -A backend.workers.tasks worker --loglevel=info
```

**说明**:
- `solo`模式使用单进程处理任务，避免了fork与MPS的冲突
- 虽然是单进程，但仍然支持MPS GPU加速
- 对于本项目的使用场景，性能影响可以忽略

---

## 前端问题

### Q4: 前端报错 "useRoutes() may be used only in the context of a <Router> component"

**症状**: 前端启动后浏览器控制台报错

**原因**: main.tsx中缺少BrowserRouter包裹

**解决方案**: 检查`frontend/src/main.tsx`是否已添加BrowserRouter:

```tsx
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>  {/* 必须添加 */}
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

---

### Q5: Ant Design警告 "Static function can not consume context like dynamic theme"

**症状**: 浏览器控制台出现Ant Design的警告

**原因**: 直接调用`message.error()`等静态方法，而没有使用App组件的上下文

**解决方案**: 已在代码中修复，使用App.useApp() hooks:

```tsx
import { App } from 'antd';

const MyComponent = () => {
  const { message } = App.useApp();  // 使用hooks

  const handleClick = () => {
    message.success('成功！');  // 正确方式
  };
};
```

---

## 视频处理问题

### Q6: 视频处理一直停留在"pending"状态

**可能原因**:
1. Celery worker未启动
2. Redis连接失败
3. 视频文件格式不支持

**排查步骤**:

1. **检查Celery worker日志**:
```bash
# 查看worker是否有任务接收日志
[2025-12-10 02:12:04,917: INFO/MainProcess] Task backend.workers.tasks.process_video_task[...] received
```

2. **检查Redis连接**:
```bash
redis-cli ping
```

3. **检查视频格式**:
   - 支持格式：MP4, MOV, AVI, MKV
   - 最大文件大小：500MB

---

### Q7: 处理完成后没有提取到关键帧

**可能原因**:
1. 视频中没有检测到人物
2. 置信度阈值设置过高
3. 采样率过大导致错过关键帧

**解决方案**:

1. **降低置信度阈值**:
   - 默认值：0.5
   - 建议范围：0.3 - 0.7
   - 如果人物较小或模糊，可降低到0.3

2. **调整采样率**:
   - 快速模式（采样率10）：可能错过部分帧
   - 标准模式（采样率5）：推荐
   - 高质量模式（采样率1）：处理所有帧，耗时较长

3. **增加最大关键帧数**:
   - 如果检测数充足但提取帧数少，可以增加`max_frames`参数

---

## 性能问题

### Q8: 处理速度很慢

**优化建议**:

1. **使用GPU加速**:
   - macOS M系列：自动使用MPS
   - Linux/Windows with NVIDIA GPU：确保安装CUDA版本的PyTorch
   - 纯CPU：考虑使用较小的YOLO模型（yolov8n.pt）

2. **调整采样率**:
   ```python
   # 快速处理（可能遗漏部分帧）
   sample_rate = 10  # 每10帧采样1次

   # 平衡模式（推荐）
   sample_rate = 5

   # 高质量（耗时最长）
   sample_rate = 1  # 处理每一帧
   ```

3. **减少最大关键帧数**:
   - 如果只需要少量关键帧，可以减少`max_frames`参数

---

## 系统要求

### Q9: 最低系统配置要求是什么？

**推荐配置**:
- **CPU**: 4核心或以上
- **内存**: 8GB RAM
- **存储**: 至少10GB可用空间
- **GPU**:
  - macOS: M1或以上（MPS）
  - Linux/Windows: NVIDIA GPU with CUDA支持（可选）
  - CPU-only模式也可运行，但速度较慢

**软件要求**:
- Python 3.10+
- Node.js 20+（仅前端）
- Redis 5.0+
- 操作系统：macOS（推荐M系列）、Linux、Windows

---

## 开发问题

### Q10: 如何查看详细的错误日志？

**后端日志**:
```bash
# Uvicorn日志（API服务器）
tail -f logs/uvicorn.log

# Celery worker日志
tail -f logs/celery.log

# 或直接在终端查看实时日志
celery -A backend.workers.tasks worker --loglevel=debug
```

**前端日志**:
- 打开浏览器开发者工具（F12）
- 查看Console标签页
- 查看Network标签页的API请求

---

## 其他问题

如果以上FAQ没有解决您的问题，请：

1. 查看项目GitHub Issues: https://github.com/MarcelLeon/key-face-frame/issues
2. 提交新的Issue并附上：
   - 错误日志
   - 系统信息（操作系统、Python版本等）
   - 重现步骤
