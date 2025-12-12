#!/bin/bash

# ==============================================================================
# Key-Face-Frame - 一键停止脚本 (Mac/Linux)
# ==============================================================================
# 功能：
# - 优雅关闭所有服务
# - 清理PID文件
# - 可选：关闭Redis
# ==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
echo "║          Key-Face-Frame - 停止服务                       ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# ==============================================================================
# 1. 停止前端服务
# ==============================================================================
log_info "停止前端服务..."

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1
        # 强制终止如果还在运行
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi
        log_success "前端服务已停止 (PID: $FRONTEND_PID)"
    else
        log_warn "前端服务未运行"
    fi
    rm -f logs/frontend.pid
else
    # 尝试通过端口停止
    if lsof -Pi :3000 -sTCP:LISTEN -t &> /dev/null; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        log_success "前端服务已停止（通过端口）"
    else
        log_warn "前端服务未运行"
    fi
fi

# ==============================================================================
# 2. 停止Celery Worker
# ==============================================================================
log_info "停止Celery Worker..."

if [ -f "logs/celery.pid" ]; then
    CELERY_PID=$(cat logs/celery.pid)
    if ps -p $CELERY_PID > /dev/null 2>&1; then
        kill $CELERY_PID 2>/dev/null || true
        sleep 2
        # 强制终止如果还在运行
        if ps -p $CELERY_PID > /dev/null 2>&1; then
            kill -9 $CELERY_PID 2>/dev/null || true
        fi
        log_success "Celery Worker已停止 (PID: $CELERY_PID)"
    else
        log_warn "Celery Worker未运行"
    fi
    rm -f logs/celery.pid
else
    # 尝试通过进程名停止
    if pkill -f "celery.*worker" 2>/dev/null; then
        log_success "Celery Worker已停止（通过进程名）"
    else
        log_warn "Celery Worker未运行"
    fi
fi

# ==============================================================================
# 3. 停止后端服务
# ==============================================================================
log_info "停止后端服务..."

if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1
        # 强制终止如果还在运行
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
        log_success "后端服务已停止 (PID: $BACKEND_PID)"
    else
        log_warn "后端服务未运行"
    fi
    rm -f logs/backend.pid
else
    # 尝试通过端口停止
    if lsof -Pi :8000 -sTCP:LISTEN -t &> /dev/null; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        log_success "后端服务已停止（通过端口）"
    else
        log_warn "后端服务未运行"
    fi
fi

# ==============================================================================
# 4. 询问是否关闭Redis
# ==============================================================================
echo ""
read -p "$(echo -e ${YELLOW}"是否关闭Redis服务? (y/N): "${NC})" -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "关闭Redis服务..."
    if redis-cli ping &> /dev/null; then
        redis-cli shutdown
        sleep 1
        log_success "Redis服务已关闭"
    else
        log_warn "Redis服务未运行"
    fi
else
    log_info "保持Redis运行"
fi

# ==============================================================================
# 5. 显示停止信息
# ==============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║              ✅ 所有服务已停止！                          ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
log_info "下次启动请运行: ./start.sh"
echo ""
