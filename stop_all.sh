#!/bin/bash
# 停止所有服务

echo "================================================================"
echo "🛑 停止所有服务"
echo "================================================================"

# 停止HydroNet Pro
if [ -f .hydronet.pid ]; then
    PID=$(cat .hydronet.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 停止HydroNet Pro (PID: $PID)..."
        kill $PID
        rm .hydronet.pid
        echo "✅ HydroNet Pro已停止"
    else
        echo "⚠️  HydroNet Pro进程不存在"
        rm .hydronet.pid
    fi
else
    echo "⚠️  未找到HydroNet Pro PID文件"
fi

# 停止HydroSIS MCP服务器
if [ -d "HydroSIS/mcp_server" ]; then
    echo ""
    echo "🛑 停止HydroSIS MCP服务器..."
    cd HydroSIS/mcp_server
    docker-compose down
    cd ../..
    echo "✅ HydroSIS MCP服务器已停止"
else
    echo "⚠️  HydroSIS目录不存在"
fi

echo ""
echo "================================================================"
echo "✅ 所有服务已停止"
echo "================================================================"
