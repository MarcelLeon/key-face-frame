# 最佳实践指导

## 一、代码规范

### 1.1 Python代码规范 (后端)

**风格指南**
- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 isort 管理导入顺序
- 使用 pylint/flake8 静态检查

**类型注解** (强制)
```python
from typing import List, Optional, Dict
from pathlib import Path

async def extract_keyframes(
    video_path: Path,
    max_frames: int = 100,
    min_interval: float = 0.5
) -> List[Dict[str, any]]:
    """提取视频关键帧

    Args:
        video_path: 视频文件路径
        max_frames: 最大提取帧数
        min_interval: 最小帧间隔(秒)

    Returns:
        关键帧信息列表
    """
    ...
```

**命名约定**
- 类名: `PascalCase` (例: `VideoProcessor`, `LeadAgent`)
- 函数/变量: `snake_case` (例: `extract_frames`, `video_path`)
- 常量: `UPPER_SNAKE_CASE` (例: `MAX_VIDEO_SIZE`, `DEFAULT_FPS`)
- 私有成员: `_leading_underscore` (例: `_process_frame`)

**文件组织**
```python
# 1. 标准库导入
import os
import sys
from pathlib import Path

# 2. 第三方库导入
import cv2
import numpy as np
from fastapi import FastAPI

# 3. 本地应用导入
from backend.core.agents import LeadAgent
from backend.models import Video
```

### 1.2 TypeScript代码规范 (前端)

**ESLint + Prettier配置**
```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "no-console": "warn",
    "no-unused-vars": "error"
  }
}
```

**组件命名**
- 组件文件: `PascalCase.tsx` (例: `VideoUploader.tsx`)
- Hook文件: `use + PascalCase.ts` (例: `useVideoUpload.ts`)
- 工具文件: `camelCase.ts` (例: `formatTime.ts`)

**Props类型定义**
```typescript
interface VideoUploaderProps {
  onUploadComplete: (videoId: string) => void;
  maxSize?: number;
  acceptedFormats?: string[];
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({
  onUploadComplete,
  maxSize = 500 * 1024 * 1024, // 500MB
  acceptedFormats = ['.mp4', '.mov', '.avi']
}) => {
  // 实现
}
```

## 二、架构模式

### 2.1 后端分层架构

```
API层 (routes/)
  ↓ 调用
Service层 (core/)
  ↓ 调用
Repository层 (models/)
  ↓ 访问
Database/Storage
```

**示例实现**
```python
# api/routes/video.py
@router.post("/videos/upload")
async def upload_video(
    file: UploadFile,
    service: VideoService = Depends(get_video_service)
):
    return await service.upload_video(file)

# core/video_service.py
class VideoService:
    def __init__(self, repo: VideoRepository, storage: Storage):
        self.repo = repo
        self.storage = storage

    async def upload_video(self, file: UploadFile) -> Video:
        # 业务逻辑
        file_path = await self.storage.save(file)
        video = await self.repo.create(file_path)
        return video

# models/video.py
class VideoRepository:
    async def create(self, file_path: str) -> Video:
        # 数据库操作
        ...
```

### 2.2 前端组件模式

**容器/展示组件分离**
```typescript
// containers/VideoListContainer.tsx (业务逻辑)
export const VideoListContainer: React.FC = () => {
  const { videos, loading } = useVideos();
  const { deleteVideo } = useVideoActions();

  return (
    <VideoList
      videos={videos}
      loading={loading}
      onDelete={deleteVideo}
    />
  );
}

// components/VideoList.tsx (纯展示)
interface VideoListProps {
  videos: Video[];
  loading: boolean;
  onDelete: (id: string) => void;
}

export const VideoList: React.FC<VideoListProps> = ({
  videos, loading, onDelete
}) => {
  // 只负责渲染
}
```

### 2.3 依赖注入模式

**后端DI**
```python
# api/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_video_service(
    db: AsyncSession = Depends(get_db)
) -> VideoService:
    repo = VideoRepository(db)
    storage = MinIOStorage()
    return VideoService(repo, storage)
```

## 三、AI/CV模型使用规范

### 3.1 模型加载和管理

**懒加载模式**
```python
class ModelManager:
    _instance = None
    _models: Dict[str, any] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self, model_name: str):
        if model_name not in self._models:
            self._models[model_name] = self._load_from_disk(model_name)
        return self._models[model_name]

    def _load_from_disk(self, model_name: str):
        # 实际加载逻辑
        if model_name == "face_detection":
            return cv2.CascadeClassifier('haarcascade_frontalface.xml')
        elif model_name == "yolo":
            from ultralytics import YOLO
            return YOLO('yolov8n.pt')
```

### 3.2 批处理优化

**批量推理**
```python
class KeyframeExtractor:
    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.model = ModelManager.get_instance().load_model("yolo")

    async def process_frames(self, frames: List[np.ndarray]) -> List[Detection]:
        results = []
        for i in range(0, len(frames), self.batch_size):
            batch = frames[i:i + self.batch_size]
            # 批量推理提升效率
            batch_results = self.model(batch)
            results.extend(batch_results)
        return results
```

### 3.3 GPU资源管理

```python
import torch

class GPUManager:
    @staticmethod
    def get_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():  # Apple Silicon
            return torch.device("mps")
        return torch.device("cpu")

    @staticmethod
    def clear_cache():
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

## 四、错误处理

### 4.1 后端异常处理

**自定义异常**
```python
# core/exceptions.py
class VideoProcessingError(Exception):
    """视频处理基础异常"""
    pass

class VideoFormatError(VideoProcessingError):
    """视频格式不支持"""
    pass

class VideoTooLargeError(VideoProcessingError):
    """视频文件过大"""
    pass

# 使用
def validate_video(file: UploadFile):
    if file.size > MAX_VIDEO_SIZE:
        raise VideoTooLargeError(f"视频大小超过限制: {file.size}")
```

**全局异常处理器**
```python
# main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(VideoProcessingError)
async def video_error_handler(request: Request, exc: VideoProcessingError):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc)
        }
    )
```

### 4.2 前端错误处理

**统一错误处理**
```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 处理未授权
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      // 服务器错误
      message.error('服务器错误，请稍后重试');
    }
    return Promise.reject(error);
  }
);
```

**错误边界**
```typescript
class ErrorBoundary extends React.Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Error caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## 五、性能优化

### 5.1 视频处理优化

**流式处理**
```python
async def process_video_stream(video_path: Path):
    """流式处理视频，避免全部加载到内存"""
    cap = cv2.VideoCapture(str(video_path))
    frame_count = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 处理单帧
            yield process_frame(frame, frame_count)
            frame_count += 1

            # 定期释放内存
            if frame_count % 1000 == 0:
                GPUManager.clear_cache()
    finally:
        cap.release()
```

**帧采样策略**
```python
def smart_frame_sampling(
    total_frames: int,
    target_frames: int = 1000
) -> List[int]:
    """智能采样，避免处理所有帧"""
    if total_frames <= target_frames:
        return list(range(total_frames))

    # 均匀采样
    step = total_frames / target_frames
    return [int(i * step) for i in range(target_frames)]
```

### 5.2 数据库优化

**索引设计**
```python
# models/video.py
class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)  # 用户查询
    status = Column(String, index=True)   # 状态过滤
    created_at = Column(DateTime, index=True)  # 时间排序
```

**查询优化**
```python
# 使用select_related避免N+1查询
async def get_videos_with_keyframes(user_id: str):
    stmt = (
        select(Video)
        .options(selectinload(Video.keyframes))  # 预加载关联数据
        .where(Video.user_id == user_id)
        .order_by(Video.created_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

### 5.3 前端性能优化

**虚拟滚动**
```typescript
import { FixedSizeList } from 'react-window';

const KeyframeGrid: React.FC<{ items: Keyframe[] }> = ({ items }) => (
  <FixedSizeList
    height={600}
    itemCount={items.length}
    itemSize={120}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        <KeyframeThumbnail keyframe={items[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

**图片懒加载**
```typescript
import { LazyLoadImage } from 'react-lazy-load-image-component';

const KeyframeThumbnail: React.FC<{ keyframe: Keyframe }> = ({ keyframe }) => (
  <LazyLoadImage
    src={keyframe.thumbnailUrl}
    alt={`Frame ${keyframe.index}`}
    effect="blur"
    placeholder={<Skeleton />}
  />
);
```

## 六、安全规范

### 6.1 文件上传安全

**文件验证**
```python
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

async def validate_upload(file: UploadFile):
    # 1. 检查文件扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise VideoFormatError(f"不支持的格式: {ext}")

    # 2. 检查文件大小
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise VideoTooLargeError(f"文件过大: {size} bytes")

    # 3. 检查MIME类型
    if not file.content_type.startswith('video/'):
        raise VideoFormatError("非视频文件")
```

**文件名处理**
```python
import uuid
from pathlib import Path

def generate_safe_filename(original_filename: str) -> str:
    """生成安全的文件名，避免路径遍历"""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"
```

### 6.2 API安全

**速率限制**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/videos/upload")
@limiter.limit("5/minute")  # 每分钟最多5次上传
async def upload_video(request: Request, file: UploadFile):
    ...
```

**输入验证**
```python
from pydantic import BaseModel, Field, validator

class KeyframeExtractionRequest(BaseModel):
    video_id: str = Field(..., regex=r'^[a-f0-9-]{36}$')
    max_frames: int = Field(100, ge=10, le=1000)
    min_interval: float = Field(0.5, ge=0.1, le=10.0)

    @validator('video_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v
```

## 七、日志和监控

### 7.1 结构化日志

```python
import structlog
from pythonjsonlogger import jsonlogger

logger = structlog.get_logger()

async def process_video(video_id: str):
    logger.info(
        "video_processing_started",
        video_id=video_id,
        timestamp=time.time()
    )

    try:
        result = await _process(video_id)
        logger.info(
            "video_processing_completed",
            video_id=video_id,
            frames_extracted=len(result),
            duration=time.time() - start
        )
    except Exception as e:
        logger.error(
            "video_processing_failed",
            video_id=video_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### 7.2 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start

            # 记录性能指标
            logger.info(
                "function_executed",
                function=func.__name__,
                duration=duration,
                success=True
            )
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(
                "function_failed",
                function=func.__name__,
                duration=duration,
                error=str(e)
            )
            raise
    return wrapper

@monitor_performance
async def extract_keyframes(video_path: Path):
    ...
```

## 八、测试驱动开发 (TDD)

### 8.1 TDD 核心原则

**先写测试，后写实现** - 这是保证开发目标不偏离的关键实践。

### 8.2 TDD 工作流程

遵循 **红-绿-重构** 循环：

```
1. 🔴 Red (写测试)
   ├─ 明确功能需求
   ├─ 定义输入输出
   ├─ 编写测试用例
   └─ 运行测试 → 失败（因为功能未实现）

2. 🟢 Green (写实现)
   ├─ 编写最简单的代码通过测试
   ├─ 运行测试 → 通过
   └─ 不关注代码优雅，只关注功能正确

3. 🔵 Refactor (重构)
   ├─ 优化代码结构
   ├─ 消除重复代码
   ├─ 改进命名和可读性
   └─ 运行测试 → 确保仍然通过
```

### 8.3 TDD 实践示例

**场景**：实现 KeyframeAgent 的关键帧提取功能

#### 步骤 1: 先写测试 (Red)

```python
# tests/unit/agents/test_keyframe_agent.py
import pytest
from backend.core.agents import KeyframeAgent
from unittest.mock import Mock

class TestKeyframeAgent:
    """KeyframeAgent 的测试套件"""

    @pytest.fixture
    def mock_storage(self):
        """Mock 存储服务"""
        storage = Mock()
        storage.save_frame = Mock(return_value="/path/to/frame.jpg")
        return storage

    @pytest.fixture
    def agent(self, mock_storage):
        """创建 KeyframeAgent 实例"""
        return KeyframeAgent(mock_storage)

    @pytest.fixture
    def sample_detections(self):
        """示例检测数据"""
        return {
            'persons': [
                {'frame_index': 10, 'timestamp': 0.33, 'bbox': [100, 100, 200, 300], 'confidence': 0.95},
                {'frame_index': 20, 'timestamp': 0.67, 'bbox': [150, 120, 250, 320], 'confidence': 0.92},
                {'frame_index': 30, 'timestamp': 1.00, 'bbox': [120, 110, 220, 310], 'confidence': 0.88},
            ]
        }

    @pytest.mark.asyncio
    async def test_extract_keyframes_returns_correct_count(
        self, agent, sample_detections, test_video_path
    ):
        """测试返回正确数量的关键帧"""
        max_frames = 2

        result = await agent.extract_keyframes(
            video_path=test_video_path,
            detections=sample_detections,
            clusters=None,
            max_frames=max_frames
        )

        # 断言：返回的关键帧数量不超过 max_frames
        assert len(result) <= max_frames

    @pytest.mark.asyncio
    async def test_extract_keyframes_sorted_by_score(
        self, agent, sample_detections, test_video_path
    ):
        """测试关键帧按分数降序排列"""
        result = await agent.extract_keyframes(
            video_path=test_video_path,
            detections=sample_detections,
            clusters=None,
            max_frames=10
        )

        # 断言：结果按分数降序排列
        scores = [kf['score'] for kf in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_extract_keyframes_removes_duplicates(
        self, agent, test_video_path
    ):
        """测试去除时间上相近的重复帧"""
        # 构造时间相近的检测数据
        close_detections = {
            'persons': [
                {'frame_index': 10, 'timestamp': 0.33, 'bbox': [100, 100, 200, 300]},
                {'frame_index': 11, 'timestamp': 0.37, 'bbox': [101, 101, 201, 301]},  # 很接近
                {'frame_index': 50, 'timestamp': 1.67, 'bbox': [120, 110, 220, 310]},  # 较远
            ]
        }

        result = await agent.extract_keyframes(
            video_path=test_video_path,
            detections=close_detections,
            clusters=None,
            max_frames=10
        )

        # 断言：相近的帧被去重
        timestamps = [kf['timestamp'] for kf in result]
        for i in range(len(timestamps) - 1):
            assert timestamps[i+1] - timestamps[i] >= 1.0  # 至少间隔1秒
```

**运行测试**：
```bash
$ pytest tests/unit/agents/test_keyframe_agent.py -v

# 结果：所有测试失败 ❌
# 原因：KeyframeAgent.extract_keyframes 方法还未实现
```

#### 步骤 2: 实现功能 (Green)

```python
# backend/core/agents/keyframe_agent.py
from typing import List, Dict, Optional
from pathlib import Path
import cv2

class KeyframeAgent:
    """关键帧提取执行代理"""

    def __init__(self, storage_client):
        self.storage = storage_client

    async def extract_keyframes(
        self,
        video_path: Path,
        detections: Dict,
        clusters: Optional[Dict],
        max_frames: int = 100
    ) -> List[Dict]:
        """提取关键帧 - 初步实现"""

        # 1. 收集候选帧
        candidates = self._collect_candidates(detections, clusters)

        # 2. 评分
        scored_frames = self._score_frames(candidates, detections)

        # 3. 去重
        unique_frames = self._remove_duplicates(scored_frames, time_threshold=1.0)

        # 4. 选择 Top N
        selected = sorted(unique_frames, key=lambda x: x['score'], reverse=True)[:max_frames]

        # 5. 保存图像
        keyframes = await self._save_keyframes(video_path, selected)

        return keyframes

    def _collect_candidates(self, detections: Dict, clusters: Optional[Dict]) -> List[Dict]:
        """收集候选帧"""
        candidates = []
        for person in detections.get('persons', []):
            candidates.append({
                'frame_index': person['frame_index'],
                'timestamp': person['timestamp'],
                'bbox': person['bbox'],
                'is_main_character': False
            })
        return candidates

    def _score_frames(self, candidates: List[Dict], detections: Dict) -> List[Dict]:
        """为候选帧评分"""
        for candidate in candidates:
            # 简单评分：基于边界框大小
            bbox = candidate['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            candidate['score'] = area / 10000  # 归一化
        return candidates

    def _remove_duplicates(self, frames: List[Dict], time_threshold: float = 1.0) -> List[Dict]:
        """去除时间上相近的重复帧"""
        if not frames:
            return []

        sorted_frames = sorted(frames, key=lambda x: x['timestamp'])
        unique = [sorted_frames[0]]

        for frame in sorted_frames[1:]:
            if frame['timestamp'] - unique[-1]['timestamp'] >= time_threshold:
                unique.append(frame)

        return unique

    async def _save_keyframes(self, video_path: Path, frames: List[Dict]) -> List[Dict]:
        """保存关键帧图像"""
        # 简化实现：直接返回帧信息
        for frame in frames:
            frame['image_url'] = f"/path/to/frame_{frame['frame_index']}.jpg"
        return frames
```

**运行测试**：
```bash
$ pytest tests/unit/agents/test_keyframe_agent.py -v

# 结果：所有测试通过 ✅
```

#### 步骤 3: 重构优化 (Refactor)

```python
# 优化后的代码
class KeyframeAgent:
    """关键帧提取执行代理 - 重构版"""

    def __init__(self, storage_client):
        self.storage = storage_client
        self.default_time_threshold = 1.0

    async def extract_keyframes(
        self,
        video_path: Path,
        detections: Dict,
        clusters: Optional[Dict] = None,
        max_frames: int = 100
    ) -> List[Dict]:
        """
        提取关键帧

        遵循的策略：
        1. 收集所有候选帧
        2. 基于多个维度评分（人物大小、置信度等）
        3. 去重相近时间的帧
        4. 返回评分最高的 N 帧
        """
        candidates = self._collect_candidates(detections, clusters)

        if not candidates:
            return []

        scored = self._score_frames(candidates, detections)
        unique = self._remove_duplicates(scored, self.default_time_threshold)
        top_frames = self._select_top_frames(unique, max_frames)

        return await self._save_keyframes(video_path, top_frames)

    def _select_top_frames(self, frames: List[Dict], max_count: int) -> List[Dict]:
        """选择评分最高的 N 帧"""
        return sorted(frames, key=lambda x: x['score'], reverse=True)[:max_count]

    # ... 其他方法保持不变
```

**再次运行测试**：
```bash
$ pytest tests/unit/agents/test_keyframe_agent.py -v

# 结果：所有测试仍然通过 ✅
# 代码更清晰、更易维护
```

### 8.4 TDD 的优势

1. **目标明确**：测试定义了"完成"的标准，不会偏离需求
2. **边界清晰**：提前考虑边界条件和异常情况
3. **重构安全**：有测试保护，可以放心优化代码
4. **文档作用**：测试即文档，展示如何使用代码
5. **调试简单**：问题更早发现，调试范围更小
6. **设计改进**：先写测试促使你思考 API 设计

### 8.5 TDD 适用场景

**推荐使用 TDD**:
- ✅ 核心业务逻辑（Agent 处理逻辑）
- ✅ 算法实现（评分、聚类、过滤）
- ✅ 数据转换和处理
- ✅ API 端点
- ✅ 工具函数和辅助方法

**可选使用 TDD**:
- ⚠️ UI 组件（可以后补测试）
- ⚠️ 配置文件
- ⚠️ 简单的数据结构定义

**不适合 TDD**:
- ❌ 探索性编程（不确定最终实现）
- ❌ 原型验证
- ❌ 一次性脚本

### 8.6 TDD 常见陷阱

**陷阱 1：测试实现细节而非行为**
```python
# ❌ 不好：测试内部实现
def test_uses_specific_algorithm():
    agent = KeyframeAgent()
    assert hasattr(agent, '_use_dbscan')  # 测试内部方法

# ✅ 好：测试行为和结果
def test_clusters_similar_faces():
    agent = RecognitionAgent()
    result = agent.cluster_faces(similar_faces)
    assert len(result['clusters']) == 1  # 相似人脸应该在一个簇
```

**陷阱 2：测试太多，过度设计**
```python
# ❌ 不好：为每个细节写测试
def test_variable_name_is_correct():
    assert agent.storage is not None

# ✅ 好：测试有意义的行为
def test_saves_to_storage():
    result = await agent.save_frame(frame)
    agent.storage.save.assert_called_once()
```

**陷阱 3：测试依赖外部资源**
```python
# ❌ 不好：依赖真实数据库
def test_with_real_db():
    db = PostgreSQL("production_db")  # 危险！
    result = service.query(db)

# ✅ 好：使用 Mock 或测试数据库
def test_with_mock_db(db_session):  # 使用 fixture
    result = service.query(db_session)
```

### 8.7 与本项目结合

在 Key-Face-Frame 项目中，TDD 工作流：

```bash
# 1. 创建新功能分支
git checkout -b feature/emotion-detection

# 2. 先写测试
vim tests/unit/agents/test_emotion_agent.py
# 定义 EmotionAgent 应该做什么

# 3. 运行测试（应该失败）
pytest tests/unit/agents/test_emotion_agent.py
# ❌ 测试失败：EmotionAgent 不存在

# 4. 实现最小功能
vim backend/core/agents/emotion_agent.py
# 实现 EmotionAgent 基本功能

# 5. 运行测试（应该通过）
pytest tests/unit/agents/test_emotion_agent.py
# ✅ 测试通过

# 6. 重构优化
# 优化代码结构，确保测试仍通过

# 7. 提交
git add .
git commit -m "feat(agents): add emotion detection agent"
```

### 8.8 TDD 工具和技巧

**Pytest 实用技巧**:
```bash
# 只运行失败的测试
pytest --lf

# 监视模式：代码改动自动运行测试
pytest-watch

# 详细输出
pytest -vv

# 调试模式
pytest --pdb

# 并行运行测试
pytest -n auto
```

**使用 pytest-testmon 加速**:
```bash
pip install pytest-testmon

# 只运行受影响的测试
pytest --testmon
```

## 九、测试规范

### 8.1 单元测试

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def video_service():
    repo = Mock(VideoRepository)
    storage = Mock(Storage)
    return VideoService(repo, storage)

@pytest.mark.asyncio
async def test_upload_video_success(video_service):
    # Arrange
    mock_file = Mock(UploadFile)
    mock_file.filename = "test.mp4"
    video_service.storage.save.return_value = "/path/to/video.mp4"

    # Act
    result = await video_service.upload_video(mock_file)

    # Assert
    assert result.file_path == "/path/to/video.mp4"
    video_service.storage.save.assert_called_once_with(mock_file)
```

### 8.2 集成测试

```python
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_video_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.mp4", open("test.mp4", "rb"), "video/mp4")}
        response = await client.post("/api/videos/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
```

## 九、版本控制

### 9.1 Git提交规范

**提交消息格式**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**
- `feat`: 新功能
- `fix`: 修复bug
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `docs`: 文档更新
- `chore`: 构建/工具变动

**示例**
```
feat(video): add keyframe extraction for multiple faces

- Implement face clustering algorithm
- Support tracking multiple characters
- Add confidence score for each detection

Closes #123
```

### 9.2 分支策略

```
main          (生产环境)
  ↑
develop       (开发主线)
  ↑
feature/*     (功能分支)
hotfix/*      (紧急修复)
```

## 十、文档规范

### 10.1 代码注释

**函数文档**
```python
def extract_keyframes(
    video_path: Path,
    detector: PersonDetector,
    threshold: float = 0.5
) -> List[Keyframe]:
    """从视频中提取包含人物的关键帧

    该函数使用场景检测和人物追踪相结合的方式，
    提取视频中的关键帧。只返回包含检测到人物的帧。

    Args:
        video_path: 视频文件路径，支持常见格式(mp4, mov, avi)
        detector: 人物检测器实例
        threshold: 检测置信度阈值，范围[0,1]，默认0.5

    Returns:
        关键帧列表，每个元素包含:
        - frame_index: 帧索引
        - timestamp: 时间戳(秒)
        - persons: 检测到的人物列表
        - image: 图像数据(numpy array)

    Raises:
        VideoFormatError: 视频格式不支持
        FileNotFoundError: 视频文件不存在

    Example:
        >>> detector = PersonDetector.load()
        >>> frames = extract_keyframes(Path("video.mp4"), detector)
        >>> print(f"Extracted {len(frames)} keyframes")
    """
    ...
```

### 10.2 API文档

**使用OpenAPI自动生成**
```python
@router.post(
    "/videos/{video_id}/extract",
    response_model=ExtractionResponse,
    summary="提取视频关键帧",
    description="""
    异步提取视频中关键角色的关键帧。

    处理流程：
    1. 视频解码和场景检测
    2. 人物检测和追踪
    3. 关键帧提取和去重
    4. 结果保存和返回

    预计处理时间: 约视频时长的1.5-2倍
    """,
    responses={
        200: {"description": "任务创建成功"},
        404: {"description": "视频不存在"},
        422: {"description": "参数验证失败"}
    }
)
async def extract_keyframes(
    video_id: str = Path(..., description="视频ID"),
    params: ExtractionParams = Body(..., description="提取参数")
):
    ...
```
