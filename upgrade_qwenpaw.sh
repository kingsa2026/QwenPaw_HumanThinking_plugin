#!/bin/bash
# QwenPaw v1.1.3.post1 升级脚本
# 在服务器上执行此脚本升级 QwenPaw

set -e

echo "========================================="
echo "QwenPaw 升级脚本"
echo "========================================="

# 1. 检查当前版本
echo ""
echo "[1/6] 检查当前版本..."
CURRENT_VERSION=$(python3 -c "import qwenpaw; print(qwenpaw.__version__)" 2>/dev/null || echo "未安装")
echo "当前版本: $CURRENT_VERSION"

# 2. 停止 QwenPaw 服务
echo ""
echo "[2/6] 停止 QwenPaw 服务..."
pkill -f "qwenpaw" 2>/dev/null || true
sleep 2
echo "服务已停止"

# 3. 备份当前安装
echo ""
echo "[3/6] 备份当前安装..."
BACKUP_DIR=~/.qwenpaw_backup_$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
if [ -d ~/.qwenpaw ]; then
    cp -r ~/.qwenpaw $BACKUP_DIR/
    echo "备份已保存到: $BACKUP_DIR"
fi

# 4. 升级 QwenPaw
echo ""
echo "[4/6] 升级 QwenPaw 到 v1.1.3.post1..."
pip install --upgrade qwenpaw==1.1.3.post1

# 5. 验证升级
echo ""
echo "[5/6] 验证升级..."
NEW_VERSION=$(python3 -c "import qwenpaw; print(qwenpaw.__version__)")
echo "新版本: $NEW_VERSION"

if [ "$NEW_VERSION" = "1.1.3.post1" ]; then
    echo "✓ 升级成功！"
else
    echo "✗ 升级失败，版本不匹配"
    exit 1
fi

# 6. 重新部署 HumanThinking 插件
echo ""
echo "[6/6] 重新部署 HumanThinking 插件..."
# 如果 HumanThinking 插件目录存在，先删除
if [ -d ~/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/agents/tools/HumanThinkingMemoryManager ]; then
    rm -rf ~/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/agents/tools/HumanThinkingMemoryManager
    echo "已删除旧的 HumanThinkingMemoryManager"
fi

# 复制新的 HumanThinking 插件（需要先上传到服务器）
# TODO: 用户需要先上传 HumanThinking 插件到服务器
# 然后取消注释下面的命令：
# python3 /path/to/install_to_qwenpaw.py

echo ""
echo "========================================="
echo "升级完成！"
echo "========================================="
echo ""
echo "下一步："
echo "1. 上传最新的 HumanThinking 插件到服务器"
echo "2. 执行 install_to_qwenpaw.py 安装插件"
echo "3. 重启 QwenPaw 服务: qwenpaw app"
echo ""
