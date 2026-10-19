#!/usr/bin/env bash
# 系统盘重置后的完整恢复：重装网盘客户端 + 补齐系统库 + 验证。
# 前提：客户端 deb 与离线依赖放在持久目录（重置不丢）；代理从环境变量读取。
set -u

STATE_DIR="${STATE_DIR:-$PWD/state}"
CLIENT_DEB="${CLIENT_DEB:-$STATE_DIR/baidunetdisk_amd64.deb}"
DEPS_DIR="${DEPS_DIR:-$STATE_DIR/deps}"
BIN="${CLIENT_BIN:-$(command -v baidunetdisk || printf '%s' /usr/bin/baidunetdisk)}"
PX="${http_proxy:-${https_proxy:-}}"

if [ -n "$PX" ]; then
  printf 'Acquire::http::Proxy "%s";\nAcquire::https::Proxy "%s";\n' "$PX" "$PX" \
    | sudo tee /etc/apt/apt.conf.d/99proxy >/dev/null
fi

if [ ! -f "$CLIENT_DEB" ]; then
  echo "未找到客户端安装包：$CLIENT_DEB" >&2
  exit 1
fi

# 1. 离线依赖 + 客户端本体
if [ -d "$DEPS_DIR" ]; then
  sudo dpkg -i "$DEPS_DIR"/*.deb 2>&1 | tail -2
fi
sudo dpkg -i "$CLIENT_DEB" 2>&1 | tail -2

# 2. 拉取包列表，补齐常见缺失库（网盘 Electron 客户端常缺 GTK3 / X11-xcb 等）
sudo apt-get update 2>&1 | tail -1
sudo apt-get install -y libgtk-3-0 libx11-xcb1 libnotify4 libnss3 libxss1 \
  libxtst6 libatspi2.0-0 libgbm1 libdrm2 2>&1 | tail -2
sudo apt-get install -f -y 2>&1 | tail -2

# 3. 验证所有动态库可解析
if ldd "$BIN" 2>/dev/null | grep -q "not found"; then
  echo "LIBS STILL MISSING:"
  ldd "$BIN" | grep "not found"
  exit 1
fi
echo "CLIENT READY (all libs resolved)"
