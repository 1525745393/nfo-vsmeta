#!/bin/bash

# NFO to VSMETA Web UI 快速启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DEFAULT_PORT=8000
LOG_FILE="web_ui.log"

# 函数定义
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查 Flask
    if ! python3 -c "import flask" &> /dev/null; then
        print_warning "Flask 未安装，正在安装..."
        pip3 install flask -q
        if [ $? -eq 0 ]; then
            print_success "Flask 安装成功"
        else
            print_error "Flask 安装失败"
            exit 1
        fi
    else
        print_success "Flask 已安装"
    fi
}

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 启动 Web UI
start_webui() {
    local port=${1:-$DEFAULT_PORT}
    
    print_info "启动 Web UI (端口: $port)..."
    
    # 检查端口
    if ! check_port $port; then
        read -p "是否使用其他端口? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            port=$((port + 1))
            while check_port $port; [ $? -ne 0 ]; do
                port=$((port + 1))
            done
            print_info "使用端口: $port"
        else
            print_error "取消启动"
            exit 1
        fi
    fi
    
    # 启动服务
    python3 web_ui.py --host 0.0.0.0 --port $port --debug >> $LOG_FILE 2>&1 &
    local pid=$!
    
    # 等待服务启动
    sleep 2
    
    # 检查进程是否运行
    if ps -p $pid > /dev/null 2>&1; then
        print_success "Web UI 启动成功!"
        echo
        echo -e "${GREEN}================================${NC}"
        echo -e "  🌐 访问地址: ${BLUE}http://localhost:$port${NC}"
        echo -e "  📱 NAS 访问: ${BLUE}http://<你的IP>:$port${NC}"
        echo -e "  📋 日志文件: ${YELLOW}$LOG_FILE${NC}"
        echo -e "${GREEN}================================${NC}"
        echo
        echo "按 Ctrl+C 停止服务"
        
        # 保存 PID
        echo $pid > .webui.pid
        
        # 等待用户中断
        trap "stop_webui $pid" INT TERM
        wait $pid
    else
        print_error "Web UI 启动失败，请查看日志: $LOG_FILE"
        exit 1
    fi
}

# 停止 Web UI
stop_webui() {
    local pid=$1
    
    if [ -z "$pid" ]; then
        if [ -f .webui.pid ]; then
            pid=$(cat .webui.pid)
        else
            print_error "未找到 Web UI 进程"
            return 1
        fi
    fi
    
    print_info "停止 Web UI (PID: $pid)..."
    kill $pid 2>/dev/null
    rm -f .webui.pid
    print_success "Web UI 已停止"
}

# 查看状态
status_webui() {
    if [ -f .webui.pid ]; then
        local pid=$(cat .webui.pid)
        if ps -p $pid > /dev/null 2>&1; then
            print_success "Web UI 正在运行 (PID: $pid)"
            return 0
        fi
    fi
    
    print_warning "Web UI 未运行"
    return 1
}

# 查看日志
view_logs() {
    if [ -f $LOG_FILE ]; then
        tail -f $LOG_FILE
    else
        print_error "日志文件不存在: $LOG_FILE"
        return 1
    fi
}

# Docker 启动
start_docker() {
    print_info "检查 Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
    
    print_info "启动 Docker 容器..."
    
    docker run -d \
        --name nfo-converter \
        -p $DEFAULT_PORT:$DEFAULT_PORT \
        -v $(pwd)/movies:/workspace/movies \
        python:3.11-slim \
        bash -c "pip install flask -q && cd /workspace && python web_ui.py --host 0.0.0.0 --port $DEFAULT_PORT"
    
    if [ $? -eq 0 ]; then
        print_success "Docker 容器启动成功!"
        echo
        echo -e "访问地址: ${BLUE}http://localhost:$DEFAULT_PORT${NC}"
    else
        print_error "Docker 容器启动失败"
        exit 1
    fi
}

# 停止 Docker
stop_docker() {
    print_info "停止 Docker 容器..."
    docker stop nfo-converter 2>/dev/null
    docker rm nfo-converter 2>/dev/null
    print_success "Docker 容器已停止"
}

# 帮助信息
show_help() {
    echo "NFO to VSMETA Web UI 快速启动脚本"
    echo
    echo "用法: $0 [命令] [选项]"
    echo
    echo "命令:"
    echo "  start       启动 Web UI (默认)"
    echo "  stop        停止 Web UI"
    echo "  status      查看运行状态"
    echo "  logs        查看日志"
    echo "  docker      使用 Docker 启动"
    echo "  docker-stop 停止 Docker 容器"
    echo "  help        显示帮助信息"
    echo
    echo "选项:"
    echo "  -p, --port  指定端口 (默认: $DEFAULT_PORT)"
    echo "  -h, --help  显示帮助"
    echo
    echo "示例:"
    echo "  $0 start                    # 启动 Web UI"
    echo "  $0 start -p 8080            # 使用端口 8080"
    echo "  $0 docker                   # 使用 Docker 启动"
    echo "  $0 logs                     # 查看日志"
}

# 主程序
main() {
    local command="start"
    local port=$DEFAULT_PORT
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            start)
                command="start"
                shift
                ;;
            stop)
                command="stop"
                shift
                ;;
            status)
                command="status"
                shift
                ;;
            logs)
                command="logs"
                shift
                ;;
            docker)
                command="docker"
                shift
                ;;
            docker-stop)
                command="docker-stop"
                shift
                ;;
            -p|--port)
                port="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行命令
    case $command in
        start)
            check_dependencies
            start_webui $port
            ;;
        stop)
            stop_webui
            ;;
        status)
            status_webui
            ;;
        logs)
            view_logs
            ;;
        docker)
            start_docker
            ;;
        docker-stop)
            stop_docker
            ;;
    esac
}

# 运行主程序
main "$@"
