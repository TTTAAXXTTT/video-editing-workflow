# Video Editing Workflow

## 直接下载使用

**[下载 Windows x64 便携版 v0.1.1](https://github.com/TTTAAXXTTT/video-editing-workflow/releases/download/v0.1.1/video-editing-workflow-Windows-x64-v0.1.1.zip)** · [发布说明及 SHA-256 校验](https://github.com/TTTAAXXTTT/video-editing-workflow/releases/tag/v0.1.1)

完整解压后通过 `VideoWorkflow.cmd grid|clips|join|verify` 加参数运行。已包含 Python、Pillow、FFmpeg、FFprobe 和 x264，无需另行安装编程环境或 FFmpeg。


一套面向旅行、Vlog、运动相机素材的个人视频剪辑工作流和可复用脚本。项目覆盖素材审查、选镜、裁剪调色、柔和转场拼接，以及成片终验，适合需要批量处理大体积素材、但希望保持流程可复现的场景。

## 适用场景

- 旅行记录、摩旅、骑行、徒步、户外运动视频。
- 运动相机、手机、无人机等设备生成的 MP4/MOV 素材。
- 需要先完整看片，再按叙事线挑选镜头。
- 希望用 FFmpeg 统一画幅、帧率和调色。
- 低内存或临时运行环境下，需要断点续跑和自动恢复。

## 功能矩阵

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 看片 | `scripts/make_grid.py` | 对每个视频抽帧并生成总览网格 |
| 精剪 | `scripts/make_clips.py` | 按镜头清单裁剪、统一规格并调色 |
| 拼接 | `scripts/join.py` | 使用 `xfade` 生成柔和淡接和首尾淡入淡出 |
| 终验 | `scripts/verify_final.py` | 检查规格、黑帧并生成终验网格 |
| 下载 | `scripts/download_watchdog.sh` | 守护大文件下载，客户端退出或低内存时重启 |
| 恢复 | `scripts/recover.sh` | Debian/Ubuntu 环境下恢复客户端和依赖 |

## 项目结构

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── config.yml
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── references/
│   ├── full-workflow.md          # 完整实战复盘
│   └── troubleshooting.md        # 问题排查手册
├── scripts/
│   ├── download_watchdog.sh
│   ├── join.py
│   ├── make_clips.py
│   ├── make_grid.py
│   ├── recover.sh
│   └── verify_final.py
├── SKILL.md                      # 工作流技能说明
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── SECURITY.md
├── requirements.txt
└── shots.example.json
```

## 环境要求

- Python 3.9+
- FFmpeg（包含 `ffmpeg` 和 `ffprobe`）
- Pillow
- 可选：Debian/Ubuntu，用于运行百度网盘客户端恢复脚本

安装 FFmpeg：

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg
```

安装 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 快速开始

1. 将视频素材放入 `footage/`。
2. 复制并编辑镜头清单：

   ```bash
   cp shots.example.json shots.json
   ```

3. 生成素材总览网格：

   ```bash
   python3 scripts/make_grid.py footage grid.jpg
   ```

4. 裁剪并生成调色片段：

   ```bash
   python3 scripts/make_clips.py \
     --src footage \
     --work output/clips \
     --shots shots.json
   ```

5. 拼接成片：

   ```bash
   python3 scripts/join.py \
     --work output/clips \
     --output output/master.mp4
   ```

6. 终验成片：

   ```bash
   python3 scripts/verify_final.py \
     output/master.mp4 \
     output/final_check.jpg
   ```

也可以运行基础检查：

```bash
make check
```

## 镜头清单格式

`shots.json` 是一个 JSON 数组，每个元素包含源文件名和入点时间（秒）：

```json
[
  {"file": "DJI_0001.MP4", "start": 120.5},
  {"file": "DJI_0002.MP4", "start": 35.0}
]
```

## 命令说明

### 1. 抽帧看片

```bash
python3 scripts/make_grid.py footage grid.jpg 8 240
```

参数依次为：视频目录、输出图片、每个视频抽帧数量、缩略图短边像素。

### 2. 生成片段

```bash
python3 scripts/make_clips.py \
  --src footage \
  --work output/clips \
  --shots shots.json \
  --duration 4.6 \
  --width 1920 \
  --height 1080 \
  --fps 30
```

### 3. 拼接片段

```bash
python3 scripts/join.py \
  --work output/clips \
  --order 0,1,2,3 \
  --output output/master.mp4
```

不传 `--order` 时，会自动按文件名中的数字排序。

### 4. 成片终验

```bash
python3 scripts/verify_final.py output/master.mp4 output/final_check.jpg
```

终验内容包括：

- 视频编码、分辨率、时长等规格。
- 中间片段是否存在黑帧。
- 多个时间点的抽帧网格。

## 大文件下载脚本

`download_watchdog.sh` 和 `recover.sh` 是特定 Linux 环境下的辅助脚本，适合需要使用百度网盘官方客户端下载大体积素材的场景。

使用前请确认：

- 客户端 `.deb` 安装包和离线依赖位置正确。
- 你理解脚本中的 `sudo` 安装操作。
- 账号 Cookie、验证码、手机号等信息不会写入脚本、日志或仓库。

可通过环境变量覆盖默认路径：

```bash
DLROOT=/path/to/downloads \
STATE_DIR=/path/to/state \
TARGET_FILES=31 \
bash scripts/download_watchdog.sh
```

## 调色与输出建议

- 仓库中的滤镜参数仅为一次冷色调胶片氛围的示例，不是固定模板。
- 不同素材的光线、曝光和设备不同，应根据项目要求调整 `make_clips.py` 中的 `base` 和 `grade`。
- 慢节奏视频适合使用柔和淡接，避免频繁使用强烈转场。
- 如果画面包含颗粒、暗角、雾、雨、雪或复杂纹理，建议提高目标码率，避免压缩后发糊。

## 安全与隐私

请勿提交以下内容：

- 私有视频、照片或个人素材。
- 账号 Cookie、Token、密码、验证码、手机号。
- 本地绝对路径、私有服务器地址或内部配置。
- 第三方未授权素材。

## 贡献

欢迎提交 Issue 和 Pull Request。提交前请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)。

## 变更记录

见 [CHANGELOG.md](./CHANGELOG.md)。

## 安全问题

见 [SECURITY.md](./SECURITY.md)。

## License

[MIT](./LICENSE)

