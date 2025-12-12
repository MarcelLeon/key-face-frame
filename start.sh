#!/bin/bash

# ==============================================================================
# Key-Face-Frame - 一键启动脚本 (Mac/Linux)
# ==============================================================================
# 功能：
# - 检查依赖（Python、Node、Redis）
# - 自动启动Redis（如未运行）
# - 后台启动FastAPI后端
# - 后台启动Celery worker
# - 启动前端开发服务器
# - 自动打开浏览器
# - 日志输出到logs/目录
# ==============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 横幅
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║          Key-Face-Frame Pro - 一键启动脚本               ║"
echo "║          AI视频关键帧提取工具                             ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

log_info "项目目录: $PROJECT_DIR"

# 创建日志目录
mkdir -p logs

# ==============================================================================
# 1. 检查依赖
# ==============================================================================
log_info "检查系统依赖..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安装！请先安装Python 3.9+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_success "Python版本: $PYTHON_VERSION"

# 检查Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装！请先安装Node.js 18+"
    exit 1
fi
NODE_VERSION=$(node --version)
log_success "Node.js版本: $NODE_VERSION"

# 检查Redis
if ! command -v redis-server &> /dev/null; then
    log_warn "Redis 未安装！尝试使用Homebrew安装..."
    if command -v brew &> /dev/null; then
        brew install redis
    else
        log_error "请先安装Redis: brew install redis"
        exit 1
    fi
fi
REDIS_VERSION=$(redis-server --version | awk '{print $3}')
log_success "Redis版本: $REDIS_VERSION"

# ==============================================================================
# 2. 检查虚拟环境
# ==============================================================================
log_info "检查Python虚拟环境..."

if [ ! -d ".venv" ]; then
    log_warn "虚拟环境不存在，正在创建..."
    python3 -m venv .venv
    log_success "虚拟环境创建成功"
fi

# 激活虚拟环境
source .venv/bin/activate
log_success "虚拟环境已激活"

# 检查依赖
if [ ! -f ".venv/bin/uvicorn" ]; then
    log_warn "后端依赖未安装，正在安装..."
    pip install -r requirements.txt
    log_success "后端依赖安装完成"
fi

# ==============================================================================
# 3. 检查前端依赖
# ==============================================================================
log_info "检查前端依赖..."

cd frontend
if [ ! -d "node_modules" ]; then
    log_warn "前端依赖未安装，正在安装..."
    npm install
    log_success "前端依赖安装完成"
fi
cd ..

# ==============================================================================
# 4. 启动Redis
# ==============================================================================
log_info "检查Redis服务..."

if redis-cli ping &> /dev/null; then
    log_success "Redis已运行"
else
    log_info "启动Redis服务..."
    redis-server --daemonize yes
    sleep 1
    if redis-cli ping &> /dev/null; then
        log_success "Redis启动成功"
    else
        log_error "Redis启动失败！"
        exit 1
    fi
fi

# ==============================================================================
# 5. 清理旧进程
# ==============================================================================
log_info "清理旧进程..."

# 清理端口8000（FastAPI）
if lsof -Pi :8000 -sTCP:LISTEN -t &> /dev/null; then
    log_warn "端口8000被占用，正在清理..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 清理端口3000（前端）
if lsof -Pi :3000 -sTCP:LISTEN -t &> /dev/null; then
    log_warn "端口3000被占用，正在清理..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 清理Celery进程
pkill -f "celery.*worker" 2>/dev/null || true
sleep 1

log_success "旧进程清理完成"

# ==============================================================================
# 6. 启动后端服务
# ==============================================================================
log_info "启动FastAPI后端服务..."

source .venv/bin/activate
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

sleep 2
if ps -p $BACKEND_PID > /dev/null; then
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
else
    log_error "后端服务启动失败！查看日志: tail -f logs/backend.log"
    exit 1
fi

# ==============================================================================
# 7. 启动Celery Worker
# ==============================================================================
log_info "启动Celery任务处理器..."

nohup celery -A backend.workers.tasks worker --loglevel=info --pool=solo > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > logs/celery.pid

sleep 2
if ps -p $CELERY_PID > /dev/null; then
    log_success "Celery Worker已启动 (PID: $CELERY_PID)"
else
    log_error "Celery启动失败！查看日志: tail -f logs/celery.log"
    exit 1
fi

# ==============================================================================
# 8. 启动前端服务
# ==============================================================================
log_info "启动前端开发服务器..."

cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

sleep 3
if ps -p $FRONTEND_PID > /dev/null; then
    log_success "前端服务已启动 (PID: $FRONTEND_PID)"
else
    log_error "前端服务启动失败！查看日志: tail -f logs/frontend.log"
    exit 1
fi

# ==============================================================================
# 9. 等待服务完全启动
# ==============================================================================
log_info "等待服务完全启动..."

# 检查后端健康
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        log_success "后端服务健康检查通过"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "后端服务未能正常启动"
    exit 1
fi

echo ""

# ==============================================================================
# 10. 打开浏览器
# ==============================================================================
log_info "自动打开浏览器..."

sleep 1
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
fi

# ==============================================================================
# 11. 显示启动信息
# ==============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║              ✅ 服务启动成功！                            ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 服务状态:${NC}"
echo -e "  ${GREEN}✓${NC} 前端:   http://localhost:3000"
echo -e "  ${GREEN}✓${NC} 后端:   http://localhost:8000"
echo -e "  ${GREEN}✓${NC} API文档: http://localhost:8000/docs"
echo -e "  ${GREEN}✓${NC} Redis:  已运行"
echo -e "  ${GREEN}✓${NC} Celery: 已运行"
echo ""
echo -e "${BLUE}📁 日志文件:${NC}"
echo -e "  - 后端日志:  logs/backend.log"
echo -e "  - Celery日志: logs/celery.log"
echo -e "  - 前端日志:  logs/frontend.log"
echo ""
echo -e "${BLUE}🛑 停止服务:${NC}"
echo -e "  运行: ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${YELLOW}💡 提示: 按 Ctrl+C 不会停止后台服务，请使用 ./stop.sh${NC}"
echo ""

# ==============================================================================
# 12. 保持脚本运行（可选）
# ==============================================================================
# 让用户知道服务已在后台运行
log_info "所有服务已在后台运行"
log_info "查看实时日志: tail -f logs/backend.log"
