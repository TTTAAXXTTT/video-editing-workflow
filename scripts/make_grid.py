#!/usr/bin/env python3
"""抽帧网格看片：对目录下每个视频抽 N 帧拼成总览图，确保逐个看过、不漏。

用法：
  python3 make_grid.py <视频目录> <输出图.jpg> [每文件帧数=8] [短边px=240]
"""
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    source_dir = Path(sys.argv[1])
    output = Path(sys.argv[2])
    frames_per_file = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    thumb_width = int(sys.argv[4]) if len(sys.argv) > 4 else 240

    files = {
        Path(path)
        for pattern in ("*.mp4", "*.mov", "*.mkv", "*.avi")
        for path in (
            glob.glob(str(source_dir / pattern))
            + glob.glob(str(source_dir / pattern.upper()))
        )
    }
    files = sorted(files)
    if not files:
        print(f"目录中没有找到视频：{source_dir}", file=sys.stderr)
        return 1

    thumb_height = int(thumb_width * 9 / 16)
    label_height = 18
    grid = Image.new(
        "RGB",
        (frames_per_file * thumb_width, len(files) * (thumb_height + label_height)),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(grid)

    with tempfile.TemporaryDirectory(prefix="make_grid_") as temp_dir:
        for row, file_path in enumerate(files):
            y = row * (thumb_height + label_height)
            draw.text((4, y + 2), file_path.name[:42], fill=(255, 220, 120))
            duration = probe_duration(file_path)

            for col in range(frames_per_file):
                timestamp = duration * (col + 0.5) / frames_per_file if duration else 0
                frame_path = Path(temp_dir) / f"frame_{row}_{col}.jpg"
                subprocess.run(
                    ["ffmpeg", "-ss", f"{timestamp:.1f}", "-i", str(file_path),
                     "-frames:v", "1", "-vf", f"scale={thumb_width}:-2",
                     "-q:v", "5", "-y", str(frame_path)],
                    capture_output=True,
                )
                if not frame_path.exists():
                    continue
                frame = Image.open(frame_path).convert("RGB")
                scaled_height = int(frame.height * thumb_width / frame.width)
                frame = frame.resize((thumb_width, scaled_height))
                if scaled_height >= thumb_height:
                    frame = frame.crop((0, 0, thumb_width, thumb_height))
                grid.paste(frame, (col * thumb_width, y + label_height))

    output.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output, quality=90)
    print(f"{len(files)} files -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
