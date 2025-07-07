#!/bin/bash

set -e  # 出錯就結束腳本

# ✅ 0. 檢查是否在 Raspberry Pi 上
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "❌ 這不是 Raspberry Pi，停止執行 start.sh"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# ✅ 1. 檢查系統套件是否已安裝
echo "🔍 檢查 gpiozero 與 lgpio 是否已安裝..."

NEED_APT=false

if ! python3 -c "import gpiozero" &>/dev/null; then
    echo "⚠️  gpiozero 尚未安裝"
    NEED_APT=true
fi

if ! python3 -c "import lgpio" &>/dev/null; then
    echo "⚠️  lgpio 尚未安裝"
    NEED_APT=true
fi

if [ "$NEED_APT" = true ]; then
    echo "🔧 安裝系統套件 (gpiozero / lgpio)"
    sudo apt update
    sudo apt install -y python3-gpiozero python3-lgpio
    sudo apt install python3-libgpiod gpiod
else
    echo "✅ 系統套件已存在，跳過 apt install"
fi

# ✅ 2. 建立 / 使用 venv
if [ -d "$VENV_DIR" ]; then
    echo "✅ venv 已存在，跳過建立與安裝依賴"
else
    echo "🧪 建立 Python venv..."
    python3 -m venv "$VENV_DIR"

    echo "📦 安裝 Python 依賴 (requirements.txt)"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_DIR/requirements.txt"
fi

# ✅ 3. 啟動主程式
echo "🚀 啟動主程式"
source "$VENV_DIR/bin/activate"
python "$PROJECT_DIR/main.py"