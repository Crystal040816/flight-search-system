#!/bin/bash

# ==============================================================================
# 机票元搜索系统 - API 服务生产环境一键部署与守护脚本 (deploy.sh)
# ==============================================================================

# 1. 核心配置变量 (对齐您运行成功的 5000 端口)
PORT=5000
WORKERS=4
APP_MODULE="run:app"
LOG_FILE="gunicorn.log"
CONDA_ENV_NAME="base"

# 控制台颜色输出定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 2. 自动激活虚拟机上安装的隔离 conda Python 环境
if [ -d "$HOME/miniconda3/bin" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate $CONDA_ENV_NAME
fi

# 获取当前占用 $PORT 端口的进程 PID (双网络指令保险，防 lsof 缺失崩溃)
get_pid() {
    local pid=""
    if command -v lsof >/dev/null 2>&1; then
        pid=$(lsof -t -i:$PORT)
    else
        pid=$(ss -lntp 2>/dev/null | grep ":$PORT " | awk '{print $6}' | cut -d, -f2 | cut -d= -f2)
    fi
    echo "$pid"
}

usage() {
    echo -e "${YELLOW}使用方法:${NC} $0 {start|stop|restart|status|logs}"
    echo "  start   : 一键核对依赖并启动后台服务"
    echo "  stop    : 一键优雅关闭后台所有进程"
    echo "  restart : 一键安全重启服务"
    echo "  status  : 查看当前服务的运行状态与线程看板"
    echo "  logs    : 实时追踪查看后端控制台运行日志"
    exit 1
}

start() {
    echo -e "${YELLOW}[1/3] 正在检测端口 $PORT 是否被占用...${NC}"
    PID=$(get_pid)
    if [ ! -z "$PID" ]; then
        echo -e "${RED}[警告] 端口 $PORT 已经被进程 $PID 占用！请先运行 '$0 stop' 关闭旧服务。${NC}"
        exit 1
    fi

    echo -e "${YELLOW}[2/3] 正在自动核对并更新算法运行环境依赖(XGBoost / Sklearn)...${NC}"
    # 静默安装，防止刷屏干扰
   # 修改后：一键补齐所有 Web 层依赖和算法数据层依赖，彻底闭环
    pip install flask flasgger flask-cors gunicorn pymysql cryptography pandas pyarrow xgboost scikit-learn -i https://pypi.tuna.tsinghua.edu.cn/simple > /dev/null 2>&1
    echo -e "${YELLOW}[3/3] 正在启动 Gunicorn 生产级多进程守护服务...${NC}"
    # 后台守护运行，输出定向到 gunicorn.log 中
    nohup gunicorn -w $WORKERS -b 0.0.0.0:$PORT $APP_MODULE > $LOG_FILE 2>&1 &

    sleep 2
    PID=$(get_pid)
    if [ ! -z "$PID" ]; then
        echo -e "${GREEN}【成功】API 服务已在虚拟机后台成功部署并运行！${NC}"
        echo -e "守护 PID: ${GREEN}$PID${NC}，绑定端口: ${GREEN}$PORT${NC}，多进程工作线程数: ${GREEN}$WORKERS${NC}"
        echo -e "您可以运行 '${YELLOW}$0 logs${NC}' 查看实时加载日志。"
    else
        echo -e "${RED}【错误】服务启动失败！请运行 '${YELLOW}$0 logs${NC}' 诊断 gunicorn.log 里的错误信息。${NC}"
    fi
}

stop() {
    echo -e "${YELLOW}正在优雅关闭 Gunicorn 进程...${NC}"
    pkill -f gunicorn > /dev/null 2>&1
    sleep 1
    PID=$(get_pid)
    if [ -z "$PID" ]; then
        echo -e "${GREEN}【成功】API 服务已彻底关闭，端口 $PORT 已安全释放。✅${NC}"
    else
        echo -e "${RED}【警告】仍有残留进程占用，正在执行强行终止 (kill -9)...${NC}"
        kill -9 $PID > /dev/null 2>&1
    fi
}

status() {
    echo -e "=================== API 服务状态看板 ==================="
    PID=$(get_pid)
    if [ ! -z "$PID" ]; then
        echo -e "服务状态 : ${GREEN}运行中 (RUNNING)${NC}"
        echo -e "绑定端口 : ${GREEN}$PORT${NC}"
        echo -e "主进程PID: ${GREEN}$PID${NC}"
        echo -e "工作线程数: ${GREEN}$WORKERS (Gunicorn)${NC}"
        echo -e "--------------------------------------------------------"
        ps -ef | grep gunicorn | grep -v grep
    else
        echo -e "服务状态 : ${RED}已停止 (STOPPED)${NC}"
        echo -e "绑定端口 : $PORT"
    fi
    echo -e "========================================================"
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}正在追踪实时运行日志 (按 Ctrl + C 可退出查看)...${NC}"
        tail -f $LOG_FILE
    else
        echo -e "${RED}[错误] 找不到日志文件 $LOG_FILE，请先启动服务。${NC}"
    fi
}

# 命令路由
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        usage
        ;;
esac