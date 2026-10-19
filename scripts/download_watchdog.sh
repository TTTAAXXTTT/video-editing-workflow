#!/usr/bin/env bash
# 大文件下载守护：系统重置自动重装、客户端退出自动重启、内存过低主动重启防 OOM。
# 官方客户端支持断点续传，重启后任务继续；单并发通常最快且最稳。
set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DLROOT="${DLROOT:-$PWD/downloads}"
STATE_DIR="${STATE_DIR:-$PWD/state}"
BIN="${CLIENT_BIN:-$(command -v baidunetdisk || true)}"
TARGET="${TARGET_FILES:-0}"                 # 0 表示不按文件数量自动退出
LOW="${MEM_LOW_MB:-1200}"
DPORT="${CDP_PORT:-9333}"
LOG="${WATCH_LOG:-$STATE_DIR/watchdog.log}"
RECOVER="${RECOVER_SH:-$SCRIPT_DIR/recover.sh}"
RUN_LOG="$STATE_DIR/run.log"

mkdir -p "$DLROOT" "$STATE_DIR"
if [ -z "$BIN" ]; then
  echo "未找到 baidunetdisk，请先安装或通过 CLIENT_BIN 指定可执行文件路径。" >&2
  exit 1
fi
CLIENT_NAME="$(basename "$BIN")"

start_client () {
  rm -f "${HOME}/.config/baidunetdisk/Singleton"* 2>/dev/null || true
  setsid env DISPLAY="${DISPLAY:-:99.0}" "$BIN" --no-sandbox \
    --remote-debugging-port="$DPORT" > "$RUN_LOG" 2>&1 < /dev/null &
  sleep 30
}

kill_client () {
  for p in $(pgrep -x "$CLIENT_NAME" || true); do kill -9 "$p" 2>/dev/null || true; done
  sleep 6
  for p in $(pgrep -x "$CLIENT_NAME" || true); do kill -9 "$p" 2>/dev/null || true; done
  sync
  sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
  sleep 2
}

echo "=== watchdog started $(date) ===" >> "$LOG"
while true; do
  TS="$(date +%H:%M:%S)"
  N="$(pgrep -x "$CLIENT_NAME" | wc -l)"
  AVAIL="$(free -m | awk '/Mem:/ {print $7}')"
  DONE="$(find "$DLROOT" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' \) \
    ! -iname '*.downloading*' 2>/dev/null | wc -l)"
  echo "$TS procs=$N avail=${AVAIL}MB done=$DONE" >> "$LOG"

  if [ ! -x "$BIN" ]; then
    echo "$TS reset -> recover" >> "$LOG"
    bash "$RECOVER" >> "$LOG" 2>&1
    start_client
  elif [ "$N" -eq 0 ]; then
    echo "$TS client gone -> start" >> "$LOG"
    start_client
  elif [ "$AVAIL" -lt "$LOW" ]; then
    echo "$TS low mem -> restart" >> "$LOG"
    kill_client
    start_client
  fi

  if [ "$TARGET" -gt 0 ] && [ "$DONE" -ge "$TARGET" ]; then
    echo "$TS ALL $TARGET COMPLETE" >> "$LOG"
    break
  fi
  sleep 12
done
