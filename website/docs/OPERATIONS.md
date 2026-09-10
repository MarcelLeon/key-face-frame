# 盯亿帧网站运维手册

## 当前正式入口

- 官网：https://key-face-frame.pages.dev/
- Cloudflare Pages 项目：`key-face-frame`，生产分支：`main`。
- 仓库：`MarcelLeon/key-face-frame`，唯一上传目录：`website/public/`。
- 配置：`website/wrangler.jsonc`；Wrangler 4.130.0，Node.js 22。
- 纯静态 HTML/CSS/JS，无数据库、视频上传接口、运行时 npm 依赖或跟踪器。
- 采用手动 Direct Upload，GitHub push 不自动发布；App Store Connect 的 Marketing URL 需单独更新。

## 本地与发布

从仓库根目录执行：

```bash
npm --prefix website ci
npm --prefix website run check
node --check website/public/app.js
npm --prefix website run dev
# 另一个终端，使用已有官方登录身份
npm --prefix website run deploy
```

预览：http://127.0.0.1:4173 。当前 deploy 脚本明确调用 `wrangler pages deploy public --project-name key-face-frame --branch main`。

未登录时运行 `npx --prefix website wrangler login --browser=false`，在官方页面核对 Pages 发布权限后授权。不把令牌放入仓库、Issue 或文档。macOS Codex 环境不要在沙箱内直接启动系统 Chrome。

该 Pages 项目已存在，无需重复创建。Wrangler 4.130.0 首次创建项目时可能自动转为 Workers；本次通过 `pages project create key-face-frame --production-branch main --force` 明确创建 Pages，后续部署不需要 `--force`。

官方流程：https://developers.cloudflare.com/pages/get-started/direct-upload/

## 验收

```bash
curl -fsS --max-time 20 https://key-face-frame.pages.dev/ -o /tmp/kff-home.html
curl -I --max-time 20 https://key-face-frame.pages.dev/assets/coastal-frames.jpg
curl -IL --max-time 20 https://key-face-frame.pages.dev/privacy.html
curl -I --max-time 20 https://key-face-frame.pages.dev/not-a-page
```

首页、资源与隐私页须正常，未知路径须为 404。浏览器直接打开正式域名，核对图片、选帧按钮/左右键、FAQ、移动端、App Store 与隐私链接及控制台。不以部署成功或绕过默认解析的 200 替代普通用户访问验证。

## 更新、回滚与故障排查

1. 只同步 `website/`；不要 `git add .`，本地可能有其他未提交业务代码。
2. 产品能力、系统要求和体验次数以当前商店与发布版本为准。修改域名时同步 canonical、OG、robots、sitemap、README 和 GitHub homepage。
3. 通过检查后发布，记录生产部署 URL/ID 与源码提交。依赖升级需复核锁文件与 npm audit。
4. 回滚优先在 Cloudflare Pages 的 Deployments 中选择核实过的生产版本回滚；或从已知正常 Git 版本恢复 `website/` 再发布。不要操作其他项目。
5. 图片或样式异常时先核对响应内容和引用路径；域名超时则对比默认 DNS、公开 DNS 与其他网络，避免盲目改页面代码或固定 hosts。

## 2026-09-10 访问修复

原 `key-face-frame.wangzq0708.workers.dev` 在当前网络解析到 `199.59.148.106`，普通浏览器/curl 超时；公开 DNS 返回 Cloudflare 地址，通过指定解析访问内容正常。证据指向旧域名在当前网络的解析/连接故障，无法仅据此断言具体运营商或拦截原因。

已将正式入口迁移至 Cloudflare Pages，生产部署 `https://133aee75.key-face-frame.pages.dev`。正式别名 `https://key-face-frame.pages.dev/` 已通过**默认 DNS、普通 HTTPS**验收：首页、CSS、JS、图片、隐私页均为 200 且与本地字节一致，未知路径 404。Chrome 直接打开成功，页面图片正常，点击特写选帧状态正确，控制台未见错误。没有修改系统 DNS、代理或浏览器安全设置。

源码基于 `57666d0771a098e35403b36b6adc16d03563f07e`，域名和部署配置修正在本次提交中。旧 Worker 保留用于历史追溯，但不再作为宣传入口；旧地址的网络故障不能依靠 HTTP 重定向解决。

## 历史记录（原 Workers 部署，已被 Pages 入口替代）


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
