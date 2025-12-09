# Key-Face-Frame Frontend

视频人物关键帧提取工具 - 前端应用

## 技术栈

- **框架**: React 18 + TypeScript 5
- **构建工具**: Vite 5
- **UI库**: Ant Design 5
- **状态管理**: Zustand 4
- **HTTP客户端**: Axios 1
- **路由**: React Router 6
- **工具库**: dayjs, ahooks

## 项目结构

```
frontend/
├── src/
│   ├── api/                     # API层
│   │   ├── client.ts           # Axios实例配置
│   │   ├── video.ts            # 视频API方法
│   │   └── types.ts            # TypeScript类型定义
│   ├── components/              # 组件
│   │   ├── VideoUploader/      # 视频上传组件
│   │   ├── ConfigPanel/        # 参数配置面板
│   │   ├── ProcessingStatus/   # 处理状态展示
│   │   └── KeyframeGallery/    # 关键帧画廊
│   ├── pages/                   # 页面
│   │   ├── Home/               # 首页（上传+配置）
│   │   ├── Processing/         # 处理页（进度展示）
│   │   └── Result/             # 结果页（关键帧展示）
│   ├── hooks/                   # 自定义Hooks
│   │   └── useProcessingStatus.ts  # 实时轮询Hook
│   ├── stores/                  # 状态管理
│   │   └── videoStore.ts       # 视频状态Store
│   ├── utils/                   # 工具函数
│   │   ├── constants.ts        # 全局常量
│   │   └── formatters.ts       # 格式化函数
│   ├── App.tsx                  # 根组件
│   └── main.tsx                 # 应用入口
├── public/                      # 静态资源
├── .env.development             # 开发环境配置
├── .env.production              # 生产环境配置
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 核心功能

### 1. 视频上传 (VideoUploader)
- 拖拽上传 + 点击选择
- 前端验证（格式、大小）
- 实时上传进度条
- 自动携带处理配置

### 2. 参数配置 (ConfigPanel)
- 三个预设模板（快速/标准/高质量）
- 采样率滑块（1-10帧）
- 最大关键帧数输入（10-500）
- 置信度阈值滑块（0.1-0.9）

### 3. 实时进度追踪 (ProcessingStatus + useProcessingStatus)
- 动态轮询间隔（pending: 1s, processing: 0.5s）
- 超时检测（30分钟）
- 错误重试（最多3次，指数退避）
- 页面可见性检测（隐藏时暂停轮询）

### 4. 关键帧展示 (KeyframeGallery)
- 响应式网格布局（手机2列、桌面4列）
- 图片懒加载
- 点击放大预览
- 排序功能（按评分/时间戳）

### 5. 状态管理 (Zustand)
- 当前视频状态
- 用户配置
- LocalStorage持久化

## 开发规范

### TypeScript
- 所有组件和函数都有完整的类型定义
- 使用接口定义Props和API响应
- 严格模式（strict: true）

### 组件设计
- 单一职责原则
- Props接口清晰
- 使用React.FC类型
- Hooks提取复用逻辑

### 代码注释
- 每个文件顶部有模块说明
- 每个组件有JSDoc注释
- 关键函数有详细说明
- 复杂逻辑有行内注释

### 最佳实践
- 使用useMemo优化计算
- 使用useCallback避免重复渲染
- 清理副作用（定时器、事件监听）
- 统一错误处理
- 响应式设计

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 环境变量

### 开发环境 (.env.development)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Key-Face-Frame
```

### 生产环境 (.env.production)
```bash
VITE_API_BASE_URL=
VITE_APP_TITLE=Key-Face-Frame
```

## API端点

### 后端API（FastAPI）
- `POST /api/videos/upload` - 上传视频
- `GET /api/videos/{video_id}/status` - 查询状态
- `GET /api/videos/{video_id}/keyframes` - 获取关键帧
- `GET /api/videos/{video_id}/download` - 下载ZIP
- `GET /files/video-{id}/keyframes/*.jpg` - 静态文件服务

## 页面路由

- `/` - 首页（上传和配置）
- `/processing/:videoId` - 处理中页面
- `/result/:videoId` - 结果展示页面

## 核心Hooks

### useProcessingStatus
实时轮询视频处理状态

```tsx
const { status, loading, error, refresh } = useProcessingStatus(videoId);
```

**特性**：
- 动态轮询间隔
- 自动超时检测
- 错误重试机制
- 页面可见性检测
- 自动清理定时器

## 核心Store

### videoStore (Zustand)
全局视频状态管理

```tsx
const config = useConfig();
const { updateConfig, setCurrentVideo } = useVideoActions();
```

**持久化字段**：
- currentVideoId
- config

## 代码质量

- ✅ TypeScript严格模式
- ✅ 完整的类型定义
- ✅ 清晰的注释文档
- ✅ 单一职责组件
- ✅ Hooks复用逻辑
- ✅ 性能优化（useMemo/useCallback）
- ✅ 副作用清理
- ✅ 错误边界处理

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 性能优化

1. **图片懒加载** - Ant Design Image组件自带
2. **代码分割** - Vite自动分割路由
3. **轮询优化** - 页面隐藏时暂停
4. **计算缓存** - useMemo缓存排序结果
5. **状态持久化** - LocalStorage减少重复请求

## 已知限制

1. 仅支持现代浏览器（ES2020+）
2. 需要后端API运行在 http://localhost:8000
3. 大文件上传可能较慢（取决于网络）
4. 长视频处理可能超过30分钟（会自动超时）

## 开发建议

### 添加新组件
1. 在 `src/components/` 下创建目录
2. 添加 `index.tsx` 和类型定义
3. 添加完整的JSDoc注释
4. 导出为默认组件

### 添加新Hook
1. 在 `src/hooks/` 下创建文件
2. 使用 `use` 前缀命名
3. 添加返回值接口
4. 处理副作用清理

### 添加新页面
1. 在 `src/pages/` 下创建目录
2. 实现页面组件
3. 在 `App.tsx` 中添加路由
4. 更新文档

## 故障排查

### 上传失败
- 检查文件格式（仅支持.mp4/.mov/.avi/.mkv）
- 检查文件大小（最大500MB）
- 检查后端API是否运行
- 查看浏览器控制台错误

### 轮询不工作
- 确认videoId正确
- 检查API端点可访问
- 查看Network面板请求状态
- 检查是否超时（30分钟）

### 图片加载失败
- 确认后端静态文件服务已启用
- 检查output目录存在
- 验证videoId和filename正确

## 版本历史

### v2.0.0 (2025-12-09)
- ✅ 完整的Web UI实现
- ✅ 实时进度追踪
- ✅ 参数配置面板
- ✅ 关键帧画廊展示
- ✅ 响应式设计
- ✅ TypeScript严格模式

### v1.0.0 (MVP)
- 命令行版本（仅后端）

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改（遵循代码规范）
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

- Issues: https://github.com/MarcelLeon/key-face-frame/issues
