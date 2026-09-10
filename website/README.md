# 盯亿帧产品宣传网站

Mac App Store 产品独立主页。深色电影感页面、交互选帧示意、工作流、能力与限制、FAQ、隐私说明、404、SEO 和安全响应头。

- 正式部署地址：https://key-face-frame.wangzq0708.workers.dev/
- App Store：https://apps.apple.com/app/id6800402462
- 产品支持：https://github.com/MarcelLeon/key-face-frame/issues
- 部署与运维：[OPERATIONS.md](docs/OPERATIONS.md)
- 设计、口径与验证：[DESIGN.md](docs/DESIGN.md)

纯静态 HTML/CSS/JavaScript，无运行时框架、数据库或视频上传接口。`public/` 是唯一发布目录。仓库中旧的 Python/Web 产品与本网站部署相互独立。

在项目根目录运行：

```bash
npm --prefix website run check
npm --prefix website run dev
```

浏览 http://127.0.0.1:4173 。部署命令及登录方式见运维文档。

## 素材

`public/assets/app-icon.png` 是产品现有图标。`coastal-frames.jpg` 是为本站生成的虚构人物电影示意图，采用三联画 CSS 定位展示；没有上传用户视频或测试素材。JPEG 是生成 PNG 的网页压缩版。站内所有素材本地托管。
