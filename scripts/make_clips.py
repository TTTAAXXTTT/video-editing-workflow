#!/usr/bin/env python3
"""镜头裁剪 + 统一/逐镜头调色，输出统一规格的片段。

镜头清单使用 JSON 文件配置：
[
  {"file": "DJI_0001.MP4", "start": 120.5},
  {"file": "DJI_0002.MP4", "start": 35.0}
]

用法：
  python3 make_clips.py --src ./footage --work ./output/clips --shots shots.json

下方 GRADE 是“冷色调胶片氛围”的示例值，可按项目要求修改，不要直接当作固定滤镜。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_shots(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(item["file"], float(item["start"])) for item in data]


def main():
    parser = argparse.ArgumentParser(description="生成统一规格且完成调色的视频片段")
    parser.add_argument("--src", default="./footage", help="源素材目录")
    parser.add_argument("--work", default="./output/clips", help="片段输出目录")
    parser.add_argument("--shots", required=True, help="镜头清单 JSON 文件")
    parser.add_argument("--duration", type=float, default=4.6, help="每个片段时长（秒）")
    parser.add_argument("--width", type=int, default=1920, help="输出宽度")
    parser.add_argument("--height", type=int, default=1080, help="输出高度")
    parser.add_argument("--fps", type=int, default=30, help="输出帧率")
    parser.add_argument("--crf", type=int, default=18, help="x264 CRF，越小质量越高")
    parser.add_argument("--preset", default="medium", help="x264 preset")
    args = parser.parse_args()

    src = Path(args.src)
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    shots = load_shots(args.shots)
    if not shots:
        print("镜头清单为空，请在 JSON 文件中配置至少一个镜头。", file=sys.stderr)
        return 1

    # 统一画幅/帧率（必做）+ 调色（示例：冷青蓝 + 褪色曲线）
    base = (
        f"scale={args.width}:{args.height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={args.width}:{args.height},fps={args.fps},"
        "eq=contrast=1.08:saturation=1.2:brightness=0.004:gamma=1.0,"
        "colorbalance=rs=-.03:gs=.01:bs=.04:rm=-.015:gm=.002:bm=.02:rh=-.02:gh=.004:bh=.025,"
        "curves=all='0/0.035 0.3/0.28 0.7/0.74 1/1'"
    )
    # 氛围：高光 bloom（split→模糊→screen）+ 胶片颗粒 + 暗角。按需增减。
    grade = (
        base
        + ",split[a][b];[b]gblur=sigma=24[g];[a][g]blend=all_mode=screen:all_opacity=0.28,"
        "noise=alls=7:allf=t+u,vignette=PI/5.2[out]"
    )

    failures = []
    for i, (filename, start) in enumerate(shots):
        source = src / filename
        output = work / f"c{i:02d}.mp4"
        if output.exists():
            print(f"c{i:02d} SKIP")
            continue
        if not source.exists():
            print(f"c{i:02d} MISSING: {source}", file=sys.stderr)
            failures.append(i)
            continue

        cmd = [
            "ffmpeg", "-ss", str(start), "-i", str(source), "-t", str(args.duration),
            "-filter_complex", grade, "-map", "[out]", "-an",
            "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
            "-pix_fmt", "yuv420p", "-y", str(output),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not output.exists():
            print(f"c{i:02d} FAIL\n{result.stderr[-800:]}", file=sys.stderr)
            failures.append(i)
            continue

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nk=1:nw=1", str(output)],
            capture_output=True, text=True,
        )
        print(f"c{i:02d} {probe.stdout.strip()}")

    if failures:
        print(f"FAILED CLIPS: {failures}", file=sys.stderr)
        return 1
    print("ALL DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
