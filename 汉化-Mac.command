#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3。请先安装 Python 3（https://www.python.org/downloads/）后重试。"
  read -r "?按回车键关闭..."
  exit 1
fi
python3 scripts/devin_zh.py apply
echo
echo "完成后请完全退出 Devin 再重新打开。"
read -r "?按回车键关闭..."
