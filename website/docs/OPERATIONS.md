# 盯亿帧网站运维手册

## 资源与发布范围

| 项目 | 配置 |
| --- | --- |
| 平台 | Cloudflare Workers Static Assets |
| Worker 名称 | `key-face-frame` |
| 部署域名 | `https://key-face-frame.wangzq0708.workers.dev/` |
| 仓库 | `MarcelLeon/key-face-frame` |
| 发布目录 | `website/public/` |
| 配置 | `website/wrangler.jsonc` |
| 工具版本 | Wrangler `4.130.0`，依赖由 package-lock.json 固定 |
| 运行环境 | Node.js 22；本地预览使用 Python 3 |
| 数据存储 | 无数据库、KV、R2 或素材上传服务 |

已完成正式部署；本次线上内容验证与当前网络访问限制见“发布记录”。不要仅凭配置中的 URL 判定可访问。

## 本地预览与检查

所有命令从仓库根目录执行：

```bash
npm --prefix website ci
npm --prefix website run check
node --check website/public/app.js
npm --prefix website run dev
```

检查 http://127.0.0.1:4173 ，覆盖桌面和手机布局、选帧点击/左右键、FAQ、App Store/支持/隐私链接。`check` 检查本地资源、锚点、商店 ID 和关键产品边界。

## 身份与部署

复用官方登录，不在仓库、日志、Issue 或聊天中存放令牌：

```bash
npx --prefix website wrangler login --browser=false --scopes account:read user:read workers:write workers_scripts:write
npx --prefix website wrangler whoami
npm --prefix website run check
npm --prefix website run deploy
```

`--browser=false` 输出登录地址，使用受信任的浏览器完成官方授权。macOS Codex 环境不要先在沙箱内直接启动系统 Chrome。

首次发布确认账号正确且不存在同名 Worker；本配置不绑定其他站点或数据库，也不会上传整个仓库。不要使用 `--temporary`，临时账号不是产品正式托管。

## 上线验收

```bash
curl -fsS https://key-face-frame.wangzq0708.workers.dev/ -o /tmp/kff-home.html
curl -I https://key-face-frame.wangzq0708.workers.dev/assets/coastal-frames.jpg
curl -IL https://key-face-frame.wangzq0708.workers.dev/privacy.html
curl -I https://key-face-frame.wangzq0708.workers.dev/not-a-page
```

首页需含“把好镜头”，资源类型正确、隐私页可读、未知路径为 404；还需浏览器实看在线样式、图片、交互以及控制台。HTTP 200 不能替代这些检查。记录部署版本 ID、对应 Git commit 和验证时间。

## 日常更新

1. 只编辑 `website/`。修改产品能力、体验次数或系统要求前重新核实当前商店与实际发布版本。
2. 在独立工作分支检查差异；本仓库可能有其他未提交业务代码，禁止 `git add .` 或全目录同步。
3. 通过网站检查与浏览器检查后发布；每次发布留存 Git SHA 与 Cloudflare 版本 ID。
4. 修改域名时同步 `index.html` 的 canonical/OG、`robots.txt`、`sitemap.xml` 和本手册。App Store Connect 的 Marketing URL 需单独更新，部署不自动修改商店资料。

当前采用显式手动发布，不宣称 GitHub push 会自动部署。需要 CI 时，将最小权限 Cloudflare API token 放在 GitHub Actions Secret 中，Account ID 放在 Repository Variable，发布仅限网站变更；不要把凭据写入 workflow 或源码。

## 回滚

```bash
npx --prefix website wrangler deployments list --config website/wrangler.jsonc
npx --prefix website wrangler rollback <已核实的历史版本ID> --config website/wrangler.jsonc
```

回滚后重新验收首页、静态资源、隐私页及 404。首次部署没有可回滚版本；若需撤回，在控制台停用该 Worker 的 workers.dev 路由。不要删除整个 Cloudflare 账号或其他应用。长期恢复应从已知正常 Git 版本重新发布网站。

## 故障排查

- `Authentication error / 10000`：检查当前连接是否只读；执行 `whoami`，重新走官方登录。能列出站点不等于有部署权限。
- 图片 404：检查 `public/assets/` 与 CSS/HTML 引用，必须同批发布。
- 样式未刷新：确认线上内容与当前 Git 版本，再做浏览器强制刷新，避免盲目改缓存策略。
- `workers.dev` 无法访问：检查 Worker 子域启用状态、DNS 和网络；不同网络可达性需分别验证，不把单一网络测试当作全球可用证明。
- 下载无地区可用性：以 Apple 商店可用范围为准，不在网站承诺全球上架。

## 发布记录

2026-09-10：通过官方 OAuth 登录后完成 Cloudflare 正式部署。

- 当前正常版本：`af9791e2-92ca-4a08-9c77-477a9bb7ec37`。
- 站点页面与素材对应 Git 提交 `1a75df45c4346f3abc12f5263a08b82eb847059c`；本次提交同步路由修正与发布记录。
- 首版 `9d823645-9583-4909-b52e-834dabac93a2` 的 `/index.html` 正常但 `/` 为 404，已将 `html_handling` 修正为 `auto-trailing-slash` 后重新部署。不要回滚到该首版。
- 自检及本地 IAB 桌面/手机交互检查通过。线上 HTTPS 验证：首页、CSS、JavaScript、示意图片、隐私页均为 200 且字节与本地一致，未知路径为 404；隐私页允许规范路径重定向。
- 验证网络限制：当前设备默认 DNS 返回 `199.59.148.106`，默认浏览器与 curl 访问超时；Google Public DNS 查询返回 `104.21.32.199` 与 `172.67.154.179`。上述线上验证使用 curl `--resolve` 指向公开解析结果，保留域名与 TLS 证书校验，没有更改系统 DNS。**这证明部署内容正常，不代表当前网络默认访问或在线浏览器验收已通过。**
- 后续在可正常解析的网络复查在线浏览器，或为产品配置另行选定的自定义域名。诊断 IP 可能变化，不能作为永久地址或 hosts 配置。

排查 DNS 时可临时使用以下命令（先重新查询公开 DNS，不要长期固定 IP）：

```bash
curl -fsS 'https://dns.google/resolve?name=key-face-frame.wangzq0708.workers.dev&type=A'
curl --resolve key-face-frame.wangzq0708.workers.dev:443:<公开解析IP> -I https://key-face-frame.wangzq0708.workers.dev/
```

GitHub push 不会自动触发部署，App Store Connect 的 Marketing URL 未在本次修改。

完整仓库检查已尝试：Python 环境缺少 Black/isort/Flake8，`run_tests.sh` 在 Flake8 阶段退出，因此没有宣称旧后端测试通过。本次不改 Python 后端或 Mac App。

部署工具依赖已通过公共 npm 安装验证。2026-09-10 npm audit 报告 3 个 high 条目，根因是 Miniflare 间接依赖 sharp 的 libheif 公告；仅涉及开发/部署工具，发布目录没有 node_modules，网站无运行时 npm 依赖。未采用 audit 建议的大幅降级或强制修复。使用新工具版本时应复核并更新锁文件。
