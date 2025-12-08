# 项目启动文档 - 视频关键角色关键帧提取系统

## 一、项目概述

### 1.1 项目名称
**Key-Face-Frame** - 视频关键角色关键帧智能提取系统

### 1.2 项目目标
构建一个商用级的视频处理系统，自动识别并提取视频中关键角色的关键帧截图，为二创工作提供高质量的素材基础。

### 1.3 核心价值
- **智能识别**：自动识别视频中的主要角色
- **精准提取**：提取角色的关键动作、表情、姿态帧
- **高效处理**：支持批量视频处理和异步任务队列
- **易于集成**：提供API接口，便于二创工具集成

## 二、技术架构

### 2.1 整体架构
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   前端UI    │─────▶│   API网关    │─────▶│  任务队列   │
│  (React)    │◀─────│  (FastAPI)   │◀─────│  (Celery)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │   存储层     │      │  AI处理层   │
                     │ (MinIO/S3)   │      │ (GPU Worker)│
                     └──────────────┘      └─────────────┘
```

### 2.2 技术栈选型

**后端服务**
- **框架**: FastAPI (Python 3.10+)
  - 高性能异步框架
  - 自动生成API文档
  - 类型检查和数据验证

- **任务队列**: Celery + Redis
  - 异步视频处理
  - 任务进度追踪
  - 支持分布式扩展

- **AI/CV引擎**:
  - OpenCV: 视频解码和帧提取
  - MediaPipe/YOLO: 人物检测和追踪
  - RetinaFace/InsightFace: 人脸识别和聚类
  - PySceneDetect: 场景切换检测

**前端界面**
- **框架**: React 18 + TypeScript
- **UI组件**: Ant Design / shadcn/ui
- **状态管理**: Zustand
- **视频播放**: Video.js
- **文件上传**: react-dropzone

**数据存储**
- **关系数据**: PostgreSQL
  - 任务记录、用户数据
  - 角色信息、标签数据

- **对象存储**: MinIO (兼容S3)
  - 视频文件存储
  - 截图文件存储

- **缓存层**: Redis
  - 任务状态缓存
  - API响应缓存

**部署运维**
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana (可选)

## 三、核心功能模块

### 3.1 视频上传模块
- 支持拖拽上传
- 大文件分片上传
- 支持常见视频格式 (MP4, MOV, AVI, MKV)
- 上传进度实时显示

### 3.2 视频分析模块
**Lead Agent**: 视频分析协调器
- 视频元信息提取 (分辨率、时长、帧率)
- 场景切换检测
- 任务拆分和调度

**Execution Agents**:
1. **人物检测Agent**
   - 检测视频中所有出现的人物
   - 人物追踪和ID分配
   - 计算人物出现频率和时长

2. **人脸识别Agent**
   - 人脸检测和特征提取
   - 人脸聚类（同一角色）
   - 主要角色识别

3. **关键帧提取Agent**
   - 基于场景变化提取关键帧
   - 基于动作幅度提取关键帧
   - 基于表情变化提取关键帧
   - 去重和质量评估

### 3.3 结果展示模块
- 角色分组展示
- 时间轴视图
- 缩略图网格视图
- 单张预览和下载
- 批量打包下载

### 3.4 任务管理模块
- 任务列表和状态追踪
- 实时进度显示
- 任务取消和重试
- 历史记录查询

## 四、项目结构

```
key-face-frame/
├── backend/                    # 后端服务
│   ├── api/                   # API接口层
│   │   ├── routes/            # 路由定义
│   │   ├── schemas/           # 数据模型
│   │   └── dependencies.py    # 依赖注入
│   ├── core/                  # 核心业务逻辑
│   │   ├── agents/            # Agent实现
│   │   │   ├── lead_agent.py
│   │   │   ├── detection_agent.py
│   │   │   ├── recognition_agent.py
│   │   │   └── keyframe_agent.py
│   │   ├── video_processor.py
│   │   └── storage.py
│   ├── workers/               # Celery任务
│   ├── models/                # 数据库模型
│   ├── config.py              # 配置管理
│   └── main.py                # 应用入口
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/             # 页面
│   │   ├── services/          # API调用
│   │   ├── stores/            # 状态管理
│   │   └── App.tsx
│   └── package.json
├── docker/                     # Docker配置
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── models/                     # AI模型文件
├── tests/                      # 测试文件
├── docs/                       # 文档目录
│   ├── BEST_PRACTICES.md
│   ├── EXECUTION_GUIDE.md
│   └── REVIEW_TESTING.md
├── .env.example               # 环境变量示例
├── requirements.txt           # Python依赖
└── README.md                  # 项目说明
```

## 五、开发路线图

**总体时间：1-2 周**（快速迭代，本地运行优先）

### 第 1-3 天：核心后端实现
- [x] 项目结构初始化
- [ ] **TDD方式**：先写测试，后写实现
- [ ] 数据库模型定义（SQLAlchemy）
- [ ] 基础 API 框架（FastAPI）
- [ ] Detection Agent（YOLO 人物检测）
- [ ] Recognition Agent（人脸聚类）
- [ ] Keyframe Agent（关键帧提取）
- [ ] Lead Agent（流程协调）
- [ ] 本地文件存储（MinIO 可选）

### 第 4-5 天：任务队列和API完善
- [ ] Celery worker 配置
- [ ] 视频上传 API
- [ ] 任务状态查询 API
- [ ] 关键帧获取 API
- [ ] Docker Compose 本地环境
- [ ] 单元测试和集成测试

### 第 6-8 天：前端开发（MVP）
- [ ] 简洁的上传界面
- [ ] 任务进度显示
- [ ] 关键帧网格展示
- [ ] 图片预览和下载
- [ ] 与后端 API 集成

### 第 9-10 天：测试和优化
- [ ] 完整流程测试
- [ ] 边界条件处理
- [ ] 性能优化（帧采样、批处理）
- [ ] 错误处理完善
- [ ] README 和使用文档

### 第 11-14 天：打磨和分享（可选）
- [ ] UI/UX 改进
- [ ] 代码重构和清理
- [ ] 增加示例视频
- [ ] 准备 GitHub 开源
- [ ] 编写项目介绍文档

### 注意事项

**本地运行优先**：
- 所有功能设计为本地 Docker 环境可运行
- 不依赖云服务（GPU、对象存储等）
- 支持 CPU 降级运行（无 GPU 时）
- 适合 `git clone` 后直接使用

**生产部署（可选）**：
- 项目支持部署到生产环境
- 但需要用户自备 GPU 和存储资源
- 不在初始开发范围内

## 六、关键技术决策

### 6.1 为什么选择FastAPI
- 原生异步支持，处理高并发请求
- 自动生成OpenAPI文档
- 与AI/ML生态系统无缝集成
- 类型安全，减少运行时错误

### 6.2 为什么使用Celery
- 成熟的分布式任务队列
- 支持任务优先级和调度
- 易于监控和管理
- 支持多种消息broker

### 6.3 为什么采用Agent架构
- **模块化**: 每个Agent专注单一职责
- **可扩展**: 易于添加新的处理能力
- **并行化**: 多个Agent可并行执行
- **容错性**: 单个Agent失败不影响整体

### 6.4 存储方案选择
- **对象存储**: 视频和图片文件量大，使用MinIO降低成本
- **关系数据库**: 结构化数据便于查询和关联
- **缓存层**: 提升API响应速度

## 七、质量标准

### 7.1 功能质量
- 角色识别准确率 > 90%
- 关键帧提取覆盖率 > 95%
- 单个视频处理时间 < 视频时长 × 2

### 7.2 性能指标
- API响应时间 < 200ms (P95)
- 支持并发处理 >= 10个视频
- 前端首屏加载 < 2s

### 7.3 代码质量
- 测试覆盖率 >= 80%
- 类型检查 100% (TypeScript/Python typing)
- 代码复杂度控制 (Cyclomatic Complexity < 10)

## 八、风险和挑战

### 8.1 技术风险
- **AI模型精度**: 不同类型视频效果差异大
  - 缓解: 多模型ensemble，可调节参数

- **GPU资源**: 大规模处理需要GPU加速
  - 缓解: 支持CPU降级，任务队列限流

### 8.2 业务风险
- **视频格式兼容**: 各种编码格式支持
  - 缓解: 使用FFmpeg统一转码

- **大文件处理**: 长视频内存占用
  - 缓解: 流式处理，分段加载

## 九、下一步行动

1. **环境准备**
   - 安装Python 3.10+, Node.js 18+
   - 配置Docker环境
   - 准备GPU机器（可选）

2. **依赖安装**
   - 后端: `pip install -r requirements.txt`
   - 前端: `cd frontend && npm install`

3. **初始化数据库**
   - 运行数据库迁移脚本
   - 创建默认配置

4. **启动开发服务**
   - 后端: `uvicorn backend.main:app --reload`
   - 前端: `npm run dev`
   - Worker: `celery -A backend.workers worker -l info`

5. **开始编码**
   - 参考 EXECUTION_GUIDE.md 开始实现
   - 遵循 BEST_PRACTICES.md 编码规范
   - 定期执行 REVIEW_TESTING.md 质量检查
