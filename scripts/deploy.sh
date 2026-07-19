#!/bin/bash

# =======================================================================
# 脚本名称: deploy.sh
# 部署机器: node1 (192.168.128.24)
# 部署路径: /home/hadoop/flight-search-system/backend
# =======================================================================

# 1. 定义虚拟机特定的变量
PROJECT_DIR="/home/hadoop/flight-search-system/backend"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/logs"
PORT=5000
WORKERS=4

echo "==================== [node1] 开始部署后端服务 ===================="

# 2. 进入项目目录
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    echo "[Info] 进入工作路径: $PROJECT_DIR"
else
    echo "[Error] 未找到路径: $PROJECT_DIR ，请确认代码已拉取至该路径"
    exit 1
fi

# 3. 创建日志目录
mkdir -p "$LOG_DIR"

# 4. 激活/创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "[Info] 正在创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
echo "[Info] 虚拟环境激活成功"

# 5. 安装依赖
echo "[Info] 正在安装 requirements.txt 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ $? -eq 0 ]; then
    echo "[Info] 依赖库同步完毕"
else
    echo "[Error] 依赖安装失败"
    exit 1
fi

# 6. 安全关闭占用端口的旧进程
PID=$(lsof -t -i:$PORT)
if [ -n "$PID" ]; then
    echo "[Info] 发现旧进程 (PID: $PID) 正在占用 $PORT 端口，正在关闭..."
    kill -9 $PID
    sleep 2
fi

# 7. 使用 Gunicorn 绑定所有网卡启动（允许 node2 前端跨机器访问）
echo "[Info] 启动 Gunicorn 服务 (监听: 0.0.0.0:$PORT)..."
nohup gunicorn -w $WORKERS -b 0.0.0.0:$PORT run:app > "$LOG_DIR/stdout.log" 2>&1 &

# 8. 状态检查
sleep 3
NEW_PID=$(lsof -t -i:$PORT)
if [ -n "$NEW_PID" ]; then
    echo "==================== [node1] 部署成功！===================="
    echo "- 局域网访问地址: http://192.168.128.24:$PORT/api"
    echo "- 进程 PID: $NEW_PID"
    echo "- 实时日志查看命令: tail -f $LOG_DIR/stdout.log"
    echo "=========================================================="
else
    echo "[Error] 服务启动异常，请查看日志: tail -n 50 $LOG_DIR/stdout.log"
    exit 1
fi