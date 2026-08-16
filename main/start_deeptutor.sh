#!/bin/bash
# ============================================
# DeepTutor 启动脚本
# ============================================

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认端口
PORT="${DEEPTUTOR_PORT:-8003}"

# 检查虚拟环境
if [ -f "$SCRIPT_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON="$SCRIPT_DIR/.venv/Scripts/python.exe"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    echo "错误: 未找到虚拟环境，请先创建虚拟环境"
    exit 1
fi

# 检查端口是否被占用
if command -v netstat &> /dev/null; then
    if netstat -ano | grep ":$PORT " | grep LISTENING > /dev/null 2>&1; then
        echo "端口 $PORT 已被占用"
        echo "请检查是否有其他进程正在使用该端口"
        exit 1
    fi
fi

echo "=========================================="
echo "启动 DeepTutor 服务"
echo "=========================================="
echo "端口: $PORT"
echo "工作目录: $SCRIPT_DIR"
echo "Python: $PYTHON"
echo "=========================================="

# 加载环境变量
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# 启动服务
"$PYTHON" -m deeptutor serve --host 0.0.0.0 --port "$PORT" --reload
