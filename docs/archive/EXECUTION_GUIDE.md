# 执行指导 - Agent架构实现

## 一、Agent系统概述

### 1.1 设计理念

本项目采用**Lead-Execution Agent架构**，将复杂的视频处理任务分解为多个专门化的智能代理协同完成：

- **Lead Agent (领导代理)**: 任务协调者，负责分析、规划和调度
- **Execution Agents (执行代理)**: 专业工作者，各自专注于特定的处理任务

### 1.2 架构优势

1. **职责分离**: 每个Agent专注单一功能，降低复杂度
2. **并行处理**: 多个Agent可同时工作，提升效率
3. **易于扩展**: 新增功能只需添加新Agent
4. **容错能力**: 单个Agent失败不影响整体流程
5. **可监控性**: 每个Agent独立追踪，便于诊断

## 二、Lead Agent详解

### 2.1 Lead Agent职责

Lead Agent是整个视频处理流程的大脑，负责：

1. **任务接收**: 接收用户的处理请求
2. **视频分析**: 分析视频元信息（时长、分辨率、帧率等）
3. **任务规划**: 根据视频特征制定处理策略
4. **工作分配**: 将任务分解并分配给Execution Agents
5. **进度监控**: 追踪各Agent执行状态
6. **结果汇总**: 整合各Agent结果并返回
7. **异常处理**: 处理执行过程中的错误

### 2.2 Lead Agent实现

```python
# backend/core/agents/lead_agent.py
from typing import Dict, List, Optional
from pathlib import Path
import asyncio
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class VideoMetadata:
    """视频元信息"""
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    format: str

@dataclass
class ProcessingPlan:
    """处理计划"""
    sample_rate: int  # 采样率（每N帧处理一次）
    enable_scene_detection: bool
    enable_face_clustering: bool
    max_keyframes: int
    parallel_workers: int

class LeadAgent:
    """视频处理领导代理"""

    def __init__(
        self,
        detection_agent: 'DetectionAgent',
        recognition_agent: 'RecognitionAgent',
        keyframe_agent: 'KeyframeAgent',
        db_session: AsyncSession
    ):
        self.detection_agent = detection_agent
        self.recognition_agent = recognition_agent
        self.keyframe_agent = keyframe_agent
        self.db = db_session

    async def process_video(
        self,
        video_id: str,
        video_path: Path,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        处理视频的主流程

        Args:
            video_id: 视频唯一标识
            video_path: 视频文件路径
            options: 可选的处理参数

        Returns:
            处理结果摘要
        """
        try:
            # 1. 更新任务状态
            await self._update_status(video_id, TaskStatus.ANALYZING)

            # 2. 分析视频元信息
            metadata = await self._analyze_video(video_path)

            # 3. 制定处理计划
            plan = self._create_plan(metadata, options)

            # 4. 更新状态为处理中
            await self._update_status(video_id, TaskStatus.PROCESSING)

            # 5. 执行处理流程
            result = await self._execute_pipeline(
                video_id, video_path, metadata, plan
            )

            # 6. 更新完成状态
            await self._update_status(video_id, TaskStatus.COMPLETED)

            return result

        except Exception as e:
            await self._update_status(video_id, TaskStatus.FAILED)
            await self._log_error(video_id, str(e))
            raise

    async def _analyze_video(self, video_path: Path) -> VideoMetadata:
        """分析视频元信息"""
        import cv2

        cap = cv2.VideoCapture(str(video_path))
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames,
                format=video_path.suffix
            )
        finally:
            cap.release()

    def _create_plan(
        self,
        metadata: VideoMetadata,
        options: Optional[Dict]
    ) -> ProcessingPlan:
        """根据视频特征制定处理计划"""

        # 默认参数
        max_keyframes = options.get('max_keyframes', 100) if options else 100

        # 智能采样率计算
        if metadata.total_frames <= 1000:
            sample_rate = 1  # 短视频全部处理
        elif metadata.total_frames <= 10000:
            sample_rate = 2  # 中等视频每2帧处理一次
        else:
            sample_rate = max(1, metadata.total_frames // 5000)

        # 根据分辨率决定是否启用某些功能
        is_hd = metadata.width >= 1280 and metadata.height >= 720
        enable_face_clustering = is_hd  # 高清视频才做人脸聚类

        # 并行度设置
        parallel_workers = min(4, max(1, metadata.total_frames // 1000))

        return ProcessingPlan(
            sample_rate=sample_rate,
            enable_scene_detection=metadata.duration > 10,  # 10秒以上才做场景检测
            enable_face_clustering=enable_face_clustering,
            max_keyframes=max_keyframes,
            parallel_workers=parallel_workers
        )

    async def _execute_pipeline(
        self,
        video_id: str,
        video_path: Path,
        metadata: VideoMetadata,
        plan: ProcessingPlan
    ) -> Dict:
        """执行处理流水线"""

        # 阶段1: 场景检测 (可选)
        scenes = []
        if plan.enable_scene_detection:
            scenes = await self._detect_scenes(video_path)
            await self._update_progress(video_id, 20, "场景检测完成")

        # 阶段2: 人物检测 (并行)
        detection_result = await self.detection_agent.detect_persons(
            video_path=video_path,
            sample_rate=plan.sample_rate,
            scenes=scenes
        )
        await self._update_progress(video_id, 50, "人物检测完成")

        # 阶段3: 人脸识别和聚类 (并行)
        recognition_result = None
        if plan.enable_face_clustering and detection_result['faces']:
            recognition_result = await self.recognition_agent.cluster_faces(
                faces=detection_result['faces'],
                video_id=video_id
            )
            await self._update_progress(video_id, 70, "人脸聚类完成")

        # 阶段4: 关键帧提取
        keyframes = await self.keyframe_agent.extract_keyframes(
            video_path=video_path,
            detections=detection_result,
            clusters=recognition_result,
            max_frames=plan.max_keyframes
        )
        await self._update_progress(video_id, 90, "关键帧提取完成")

        # 阶段5: 保存结果
        result = await self._save_results(
            video_id=video_id,
            keyframes=keyframes,
            metadata=metadata,
            detection_result=detection_result,
            recognition_result=recognition_result
        )
        await self._update_progress(video_id, 100, "处理完成")

        return result

    async def _detect_scenes(self, video_path: Path) -> List[tuple]:
        """场景检测"""
        from scenedetect import detect, ContentDetector

        scenes = detect(str(video_path), ContentDetector())
        return [(s[0].get_seconds(), s[1].get_seconds()) for s in scenes]

    async def _update_status(self, video_id: str, status: TaskStatus):
        """更新任务状态"""
        await self.db.execute(
            "UPDATE videos SET status = :status WHERE id = :id",
            {"status": status.value, "id": video_id}
        )
        await self.db.commit()

    async def _update_progress(
        self,
        video_id: str,
        progress: int,
        message: str
    ):
        """更新处理进度"""
        await self.db.execute(
            "UPDATE videos SET progress = :progress, message = :message WHERE id = :id",
            {"progress": progress, "message": message, "id": video_id}
        )
        await self.db.commit()

    async def _save_results(self, **kwargs) -> Dict:
        """保存处理结果到数据库"""
        # 实现结果保存逻辑
        pass

    async def _log_error(self, video_id: str, error: str):
        """记录错误日志"""
        logger.error(
            "video_processing_error",
            video_id=video_id,
            error=error
        )
```

## 三、Execution Agents详解

### 3.1 Detection Agent (人物检测代理)

**职责**: 检测视频帧中的人物位置和边界框

```python
# backend/core/agents/detection_agent.py
from typing import List, Dict
import numpy as np
from pathlib import Path
import cv2

class DetectionAgent:
    """人物检测执行代理"""

    def __init__(self, model_name: str = "yolov8n"):
        from ultralytics import YOLO
        self.model = YOLO(f"{model_name}.pt")
        self.confidence_threshold = 0.5

    async def detect_persons(
        self,
        video_path: Path,
        sample_rate: int = 1,
        scenes: List[tuple] = None
    ) -> Dict:
        """
        检测视频中的人物

        Args:
            video_path: 视频路径
            sample_rate: 采样率
            scenes: 场景列表（可选）

        Returns:
            检测结果字典：
            {
                'persons': [...],  # 人物检测框
                'faces': [...],    # 人脸检测框
                'tracks': {...}    # 人物追踪信息
            }
        """
        persons = []
        faces = []
        tracks = {}

        cap = cv2.VideoCapture(str(video_path))
        frame_idx = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 采样
                if frame_idx % sample_rate != 0:
                    frame_idx += 1
                    continue

                # YOLO检测
                results = self.model.track(
                    frame,
                    persist=True,
                    classes=[0],  # 0 = person
                    conf=self.confidence_threshold
                )

                # 解析结果
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        person = {
                            'frame_index': frame_idx,
                            'timestamp': frame_idx / cap.get(cv2.CAP_PROP_FPS),
                            'bbox': box.xyxy[0].tolist(),
                            'confidence': float(box.conf[0]),
                            'track_id': int(box.id[0]) if box.id is not None else None
                        }
                        persons.append(person)

                        # 提取人脸区域
                        face = self._extract_face(frame, person['bbox'])
                        if face is not None:
                            faces.append({
                                **person,
                                'face_image': face
                            })

                frame_idx += 1

        finally:
            cap.release()

        # 构建追踪轨迹
        tracks = self._build_tracks(persons)

        return {
            'persons': persons,
            'faces': faces,
            'tracks': tracks,
            'total_frames_processed': frame_idx
        }

    def _extract_face(self, frame: np.ndarray, bbox: List[float]) -> Optional[np.ndarray]:
        """从人物框中提取人脸"""
        # 使用MediaPipe或其他人脸检测器
        # 这里简化实现
        x1, y1, x2, y2 = map(int, bbox)
        person_crop = frame[y1:y2, x1:x2]

        # 使用人脸检测器
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
        face_rects = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(face_rects) > 0:
            fx, fy, fw, fh = face_rects[0]
            return person_crop[fy:fy+fh, fx:fx+fw]

        return None

    def _build_tracks(self, persons: List[Dict]) -> Dict[int, List[Dict]]:
        """构建人物追踪轨迹"""
        tracks = {}
        for person in persons:
            track_id = person.get('track_id')
            if track_id is not None:
                if track_id not in tracks:
                    tracks[track_id] = []
                tracks[track_id].append(person)
        return tracks
```

### 3.2 Recognition Agent (人脸识别代理)

**职责**: 人脸特征提取和聚类，识别主要角色

```python
# backend/core/agents/recognition_agent.py
from typing import List, Dict
import numpy as np
from sklearn.cluster import DBSCAN

class RecognitionAgent:
    """人脸识别和聚类执行代理"""

    def __init__(self):
        # 使用InsightFace或类似的人脸识别模型
        from insightface.app import FaceAnalysis
        self.app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    async def cluster_faces(
        self,
        faces: List[Dict],
        video_id: str,
        eps: float = 0.5,
        min_samples: int = 3
    ) -> Dict:
        """
        人脸聚类，识别主要角色

        Args:
            faces: 人脸列表（来自DetectionAgent）
            video_id: 视频ID
            eps: DBSCAN的eps参数
            min_samples: 最小样本数

        Returns:
            聚类结果：
            {
                'clusters': {...},      # 聚类结果
                'main_characters': [...] # 主要角色
            }
        """
        if not faces:
            return {'clusters': {}, 'main_characters': []}

        # 1. 提取人脸特征
        embeddings = []
        valid_faces = []

        for face_data in faces:
            face_img = face_data.get('face_image')
            if face_img is None:
                continue

            # 人脸特征提取
            result = self.app.get(face_img)
            if len(result) > 0:
                embedding = result[0].embedding
                embeddings.append(embedding)
                valid_faces.append(face_data)

        if not embeddings:
            return {'clusters': {}, 'main_characters': []}

        # 2. 聚类
        embeddings_array = np.array(embeddings)
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings_array)

        # 3. 组织聚类结果
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:  # 噪声点
                continue

            if label not in clusters:
                clusters[label] = {
                    'character_id': f"{video_id}_char_{label}",
                    'faces': [],
                    'count': 0
                }

            clusters[label]['faces'].append(valid_faces[idx])
            clusters[label]['count'] += 1

        # 4. 识别主要角色（出现次数最多的前3个）
        main_characters = sorted(
            clusters.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:3]

        # 5. 为每个角色选择代表性人脸
        for char in main_characters:
            char['representative_face'] = self._select_best_face(char['faces'])

        return {
            'clusters': clusters,
            'main_characters': main_characters,
            'total_clusters': len(clusters),
            'total_faces': len(valid_faces)
        }

    def _select_best_face(self, faces: List[Dict]) -> Dict:
        """选择最佳代表人脸（最清晰、正面）"""
        # 简化实现：选择confidence最高的
        return max(faces, key=lambda x: x.get('confidence', 0))
```

### 3.3 Keyframe Agent (关键帧提取代理)

**职责**: 从检测和识别结果中提取关键帧

```python
# backend/core/agents/keyframe_agent.py
from typing import List, Dict, Optional
import numpy as np
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
        """
        提取关键帧

        策略：
        1. 主要角色出现的帧优先
        2. 动作幅度大的帧
        3. 场景变化的帧
        4. 去重和质量筛选

        Args:
            video_path: 视频路径
            detections: 检测结果
            clusters: 聚类结果
            max_frames: 最大关键帧数

        Returns:
            关键帧列表
        """
        # 1. 收集候选帧
        candidates = self._collect_candidates(detections, clusters)

        # 2. 评分和排序
        scored_frames = self._score_frames(candidates, detections)

        # 3. 去重
        unique_frames = self._remove_duplicates(scored_frames)

        # 4. 选择Top N
        selected = sorted(
            unique_frames,
            key=lambda x: x['score'],
            reverse=True
        )[:max_frames]

        # 5. 提取和保存图像
        keyframes = await self._save_keyframes(video_path, selected)

        return keyframes

    def _collect_candidates(
        self,
        detections: Dict,
        clusters: Optional[Dict]
    ) -> List[Dict]:
        """收集候选关键帧"""
        candidates = []

        # 如果有聚类结果，优先主要角色
        if clusters and 'main_characters' in clusters:
            for char in clusters['main_characters']:
                for face in char['faces']:
                    candidates.append({
                        'frame_index': face['frame_index'],
                        'timestamp': face['timestamp'],
                        'bbox': face['bbox'],
                        'is_main_character': True,
                        'character_id': char['character_id']
                    })

        # 添加所有检测到人物的帧
        for person in detections.get('persons', []):
            candidates.append({
                'frame_index': person['frame_index'],
                'timestamp': person['timestamp'],
                'bbox': person['bbox'],
                'is_main_character': False,
                'character_id': None
            })

        return candidates

    def _score_frames(
        self,
        candidates: List[Dict],
        detections: Dict
    ) -> List[Dict]:
        """为候选帧评分"""
        tracks = detections.get('tracks', {})

        for candidate in candidates:
            score = 0

            # 1. 主要角色加分
            if candidate.get('is_main_character'):
                score += 100

            # 2. 人物大小（占画面比例）
            bbox = candidate['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            score += min(50, area / 10000)  # 归一化

            # 3. 轨迹稳定性（在轨迹中间的帧更稳定）
            track_id = candidate.get('track_id')
            if track_id and track_id in tracks:
                track = tracks[track_id]
                track_pos = [i for i, p in enumerate(track)
                           if p['frame_index'] == candidate['frame_index']]
                if track_pos:
                    # 中间位置加分
                    mid_score = 30 * (1 - abs(track_pos[0] / len(track) - 0.5) * 2)
                    score += mid_score

            candidate['score'] = score

        return candidates

    def _remove_duplicates(
        self,
        frames: List[Dict],
        time_threshold: float = 1.0
    ) -> List[Dict]:
        """去除时间上相近的重复帧"""
        if not frames:
            return []

        # 按时间排序
        sorted_frames = sorted(frames, key=lambda x: x['timestamp'])

        unique = [sorted_frames[0]]
        for frame in sorted_frames[1:]:
            if frame['timestamp'] - unique[-1]['timestamp'] >= time_threshold:
                unique.append(frame)

        return unique

    async def _save_keyframes(
        self,
        video_path: Path,
        frames: List[Dict]
    ) -> List[Dict]:
        """提取并保存关键帧图像"""
        cap = cv2.VideoCapture(str(video_path))
        keyframes = []

        try:
            for frame_data in frames:
                frame_idx = frame_data['frame_index']

                # 定位到指定帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    continue

                # 保存到存储
                image_path = await self.storage.save_frame(
                    frame,
                    frame_idx,
                    frame_data.get('character_id')
                )

                keyframes.append({
                    **frame_data,
                    'image_url': image_path,
                    'width': frame.shape[1],
                    'height': frame.shape[0]
                })

        finally:
            cap.release()

        return keyframes
```

## 四、Agent协作流程

### 4.1 通信协议

Agents之间通过**标准化的数据结构**进行通信：

```python
# backend/core/schemas/agent_messages.py
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class AgentMessage(BaseModel):
    """Agent间通信消息基类"""
    agent_name: str
    timestamp: datetime
    video_id: str
    data: Any

class DetectionMessage(AgentMessage):
    """人物检测消息"""
    data: Dict[str, Any]  # persons, faces, tracks

class RecognitionMessage(AgentMessage):
    """人脸识别消息"""
    data: Dict[str, Any]  # clusters, main_characters

class KeyframeMessage(AgentMessage):
    """关键帧消息"""
    data: List[Dict]  # keyframes
```

### 4.2 完整工作流程

```
用户上传视频
    ↓
API接收请求 → 创建Celery任务
    ↓
Lead Agent启动
    ↓
┌───────────────────────────────────┐
│  1. 视频分析 (Lead Agent)         │
│     - 提取元信息                  │
│     - 制定处理计划                │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  2. 场景检测 (Lead Agent)         │
│     - 识别场景切换点              │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  3. 人物检测 (Detection Agent)    │
│     - YOLO检测人物                │
│     - 人物追踪                    │
│     - 人脸提取                    │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  4. 人脸聚类 (Recognition Agent)  │
│     - 特征提取                    │
│     - DBSCAN聚类                  │
│     - 识别主要角色                │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  5. 关键帧提取 (Keyframe Agent)   │
│     - 候选帧收集                  │
│     - 评分排序                    │
│     - 去重筛选                    │
│     - 保存图像                    │
└───────────────────────────────────┘
    ↓
Lead Agent汇总结果
    ↓
返回给用户
```

### 4.3 并行执行示例

某些阶段可以并行执行以提升性能：

```python
class LeadAgent:
    async def _parallel_processing(self, video_path: Path):
        """并行执行多个Agent任务"""

        # 同时执行场景检测和人物检测
        scene_task = asyncio.create_task(
            self._detect_scenes(video_path)
        )
        detection_task = asyncio.create_task(
            self.detection_agent.detect_persons(video_path)
        )

        # 等待两个任务完成
        scenes, detections = await asyncio.gather(
            scene_task,
            detection_task
        )

        return scenes, detections
```

## 五、Celery任务集成

### 5.1 定义Celery任务

```python
# backend/workers/tasks.py
from celery import Celery
from backend.core.agents import LeadAgent, DetectionAgent, RecognitionAgent, KeyframeAgent

celery_app = Celery('key-face-frame', broker='redis://localhost:6379/0')

@celery_app.task(bind=True)
def process_video_task(self, video_id: str, video_path: str, options: dict = None):
    """
    视频处理Celery任务

    Args:
        self: Task实例 (bind=True时自动传入)
        video_id: 视频ID
        video_path: 视频文件路径
        options: 处理选项
    """
    # 更新任务状态
    self.update_state(
        state='PROGRESS',
        meta={'progress': 0, 'status': '初始化...'}
    )

    # 创建Agent实例
    detection_agent = DetectionAgent()
    recognition_agent = RecognitionAgent()
    keyframe_agent = KeyframeAgent(storage_client)

    # 创建Lead Agent
    async def run():
        async with get_db_session() as db:
            lead_agent = LeadAgent(
                detection_agent,
                recognition_agent,
                keyframe_agent,
                db
            )

            # 执行处理
            result = await lead_agent.process_video(
                video_id,
                Path(video_path),
                options
            )

            return result

    # 运行异步任务
    import asyncio
    result = asyncio.run(run())

    return result
```

### 5.2 API触发任务

```python
# backend/api/routes/videos.py
from fastapi import APIRouter, UploadFile, BackgroundTasks
from backend.workers.tasks import process_video_task

router = APIRouter()

@router.post("/videos/upload")
async def upload_and_process(file: UploadFile):
    # 1. 保存视频文件
    video_id = str(uuid.uuid4())
    video_path = await save_upload_file(file, video_id)

    # 2. 创建数据库记录
    await create_video_record(video_id, video_path)

    # 3. 提交Celery任务
    task = process_video_task.delay(video_id, str(video_path))

    return {
        "video_id": video_id,
        "task_id": task.id,
        "status": "processing"
    }

@router.get("/videos/{video_id}/status")
async def get_processing_status(video_id: str):
    """查询处理状态"""
    video = await get_video(video_id)
    return {
        "video_id": video_id,
        "status": video.status,
        "progress": video.progress,
        "message": video.message
    }
```

## 六、监控和调试

### 6.1 Agent日志

```python
import structlog

logger = structlog.get_logger()

class DetectionAgent:
    async def detect_persons(self, video_path: Path, **kwargs):
        logger.info(
            "detection_started",
            agent="DetectionAgent",
            video_path=str(video_path)
        )

        try:
            result = await self._detect(video_path)

            logger.info(
                "detection_completed",
                agent="DetectionAgent",
                persons_count=len(result['persons']),
                faces_count=len(result['faces'])
            )

            return result
        except Exception as e:
            logger.error(
                "detection_failed",
                agent="DetectionAgent",
                error=str(e),
                exc_info=True
            )
            raise
```

### 6.2 性能监控

```python
import time
from functools import wraps

def monitor_agent(agent_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()

            logger.info(f"{agent_name}_started")

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start

                logger.info(
                    f"{agent_name}_completed",
                    duration=duration,
                    success=True
                )

                return result
            except Exception as e:
                duration = time.time() - start

                logger.error(
                    f"{agent_name}_failed",
                    duration=duration,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator

# 使用
class DetectionAgent:
    @monitor_agent("DetectionAgent.detect_persons")
    async def detect_persons(self, ...):
        ...
```

## 七、扩展性设计

### 7.1 添加新Agent

添加新功能只需创建新的Execution Agent：

```python
# 例如：添加情感分析Agent
class EmotionAgent:
    """情感分析执行代理"""

    async def analyze_emotions(self, faces: List[Dict]) -> Dict:
        """分析人脸情感"""
        # 实现情感识别逻辑
        pass

# 在Lead Agent中集成
class LeadAgent:
    def __init__(self, ..., emotion_agent: EmotionAgent):
        ...
        self.emotion_agent = emotion_agent

    async def _execute_pipeline(self, ...):
        ...
        # 添加情感分析阶段
        emotions = await self.emotion_agent.analyze_emotions(faces)
        ...
```

### 7.2 Agent配置化

通过配置文件灵活控制Agent行为：

```python
# config/agents.yaml
agents:
  detection:
    model: "yolov8n"
    confidence_threshold: 0.5
    enable_tracking: true

  recognition:
    clustering_eps: 0.5
    min_samples: 3
    enable_face_quality_filter: true

  keyframe:
    max_frames: 100
    min_interval: 1.0
    enable_deduplication: true

# 加载配置
import yaml

class AgentConfig:
    @staticmethod
    def load(agent_name: str) -> Dict:
        with open('config/agents.yaml') as f:
            config = yaml.safe_load(f)
        return config['agents'][agent_name]

# 使用
class DetectionAgent:
    def __init__(self):
        config = AgentConfig.load('detection')
        self.model = YOLO(config['model'])
        self.confidence_threshold = config['confidence_threshold']
```

## 八、常见问题和解决方案

### Q1: Agent执行失败如何处理？

**方案**: 实现重试机制和降级策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class DetectionAgent:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def detect_persons(self, ...):
        # 自动重试，指数退避
        ...
```

### Q2: 如何处理GPU OOM？

**方案**: 批次大小动态调整

```python
class DetectionAgent:
    def __init__(self):
        self.batch_size = 32

    async def detect_persons(self, ...):
        try:
            # 尝试批量处理
            return await self._detect_batch(self.batch_size)
        except RuntimeError as e:
            if "out of memory" in str(e):
                # 减小批次大小重试
                self.batch_size = max(1, self.batch_size // 2)
                torch.cuda.empty_cache()
                return await self._detect_batch(self.batch_size)
            raise
```

### Q3: 如何测试单个Agent？

**方案**: 编写独立的单元测试

```python
import pytest

@pytest.mark.asyncio
async def test_detection_agent():
    agent = DetectionAgent()

    # 准备测试数据
    test_video = Path("tests/fixtures/test_video.mp4")

    # 执行
    result = await agent.detect_persons(test_video, sample_rate=10)

    # 断言
    assert 'persons' in result
    assert 'faces' in result
    assert len(result['persons']) > 0
```
