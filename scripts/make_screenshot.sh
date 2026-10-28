#!/usr/bin/env bash
# 生成不包含启动弹窗的主界面截图。
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
OUT="$ROOT_DIR/assets/screenshot.png"
mkdir -p "$ROOT_DIR/assets"

DISPLAY="${DISPLAY:-:99}"
python3 "$SCRIPT_DIR/gui.py" --no-popup &
pid=$!

cleanup () {
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}
trap cleanup EXIT

sleep 4
import -window "视频剪辑工作流" "$OUT"
echo "$OUT"
