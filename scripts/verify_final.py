#!/usr/bin/env python3
"""成片终验：ffprobe 规格 + 中间黑帧检测 + 多时间点抽帧网格。

用法：
  python3 verify_final.py <成片.mp4> [输出检查图.jpg]
"""
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
    return float(result.stdout.strip())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    video = Path(sys.argv[1])
    check_image = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./final_check.jpg")
    if not video.exists():
        print(f"成片不存在：{video}", file=sys.stderr)
        return 1

    spec = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height,codec_name,codec_type",
         "-of", "default=nw=1", str(video)],
        capture_output=True, text=True,
    )
    if spec.returncode != 0:
        print(spec.stderr, file=sys.stderr)
        return 1
    print("--- spec ---\n" + spec.stdout.strip())

    duration = probe_duration(video)
    inspect_start = 1.5
    inspect_duration = max(0.0, duration - 3.0)
    black_count = 0
    if inspect_duration > 0:
        black_detect = subprocess.run(
            ["ffmpeg", "-ss", str(inspect_start), "-t", f"{inspect_duration:.1f}",
             "-i", str(video), "-vf", "blackdetect=d=0.3:pic_th=0.98",
             "-an", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        black_count = black_detect.stderr.count("blackdetect")
    print(f"--- mid black frames: {black_count} (应为 0) ---")

    timestamps = [duration * x / 11 for x in range(1, 11)]
    cell_width, cell_height, label_height = 380, 214, 20
    columns, rows = 5, 2
    grid = Image.new(
        "RGB",
        (columns * cell_width, rows * (cell_height + label_height)),
        (0, 0, 0),
    )
    draw = ImageDraw.Draw(grid)

    with tempfile.TemporaryDirectory(prefix="verify_final_") as temp_dir:
        for i, timestamp in enumerate(timestamps):
            row, col = divmod(i, columns)
            x, y = col * cell_width, row * (cell_height + label_height)
            draw.text((x + 4, y + 2), f"{timestamp:.0f}s", fill=(255, 230, 120))
            frame_path = Path(temp_dir) / f"frame_{i}.jpg"
            subprocess.run(
                ["ffmpeg", "-ss", f"{timestamp:.1f}", "-i", str(video),
                 "-frames:v", "1", "-vf", f"scale={cell_width}:-2",
                 "-q:v", "3", "-y", str(frame_path)],
                capture_output=True,
            )
            if not frame_path.exists():
                continue
            frame = Image.open(frame_path).convert("RGB")
            scaled_height = int(frame.height * cell_width / frame.width)
            frame = frame.resize((cell_width, scaled_height))
            if scaled_height >= cell_height:
                frame = frame.crop((0, 0, cell_width, cell_height))
            grid.paste(frame, (x, y + label_height))

    check_image.parent.mkdir(parents=True, exist_ok=True)
    grid.save(check_image, quality=92)
    print(f"--- check image: {check_image} ---")
    return 1 if black_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
