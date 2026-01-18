# Git 双仓库工作流指南

本项目采用双仓库模式管理公开版和商业版代码。

## 仓库配置

| Remote | 用途 | URL |
|--------|------|-----|
| `origin` | 公开版 | https://github.com/MarcelLeon/key-face-frame.git |
| `private` | 商业版 | https://github.com/MarcelLeon/key-face-frame-pro.git |

## 分支对应关系

| 本地分支 | 追踪远程 | 说明 |
|----------|----------|------|
| `main` | `origin/main` | 公开版主分支 |
| `commercial-feature` | `private/main` | 商业版主分支 |

## 快速确认当前版本

```bash
# 查看当前分支
git branch --show-current
# main = 公开版 | commercial-feature = 商业版

# 查看详细分支追踪关系
git branch -vv
```

## 日常开发命令

### 公开版开发

```bash
# 1. 切换到公开版
git checkout main

# 2. 拉取最新代码
git pull origin main

# 3. 修改代码后提交
git add .
git commit -m "fix: 修复xxx问题"

# 4. 推送到公开版
git push origin main
```

### 商业版开发

```bash
# 1. 切换到商业版
git checkout commercial-feature

# 2. 拉取最新代码
git pull private main

# 3. 修改代码后提交
git add .
git commit -m "feat: 商业功能xxx"

# 4. 推送到商业版
git push private commercial-feature:main
```

### 同步公开版到商业版

当公开版有更新（如修复 Issue），需要同步到商业版：

```bash
# 1. 先更新公开版
git checkout main
git pull origin main

# 2. 切换到商业版并合并
git checkout commercial-feature
git merge main

# 3. 解决冲突（如有）后推送
git push private commercial-feature:main
```

## 注意事项

1. **永远不要**将商业版代码推送到 `origin`（公开版）
2. 商业版特有文件（如 `license.py`）只在 `commercial-feature` 分支修改
3. 公共功能修复应先在 `main` 分支完成，再同步到商业版
4. 提交前用 `git branch -vv` 确认当前分支

## 常用检查命令

```bash
# 查看远程仓库配置
git remote -v

# 查看所有分支
git branch -a

# 查看当前状态
git status

# 查看提交历史
git log --oneline -10
```
