#!/usr/bin/env python3
"""把统一规格的片段用柔和淡接（xfade）拼成主视频，首尾黑场淡入淡出。

用法：
  python3 join.py --work ./output/clips --order 0,1,2 --output ./output/master.mp4

不传 --order 时，会自动按片段文件名中的数字排序。
总时长 = STEP*(N-1) + 片段时长；STEP = 片段时长 - 转场重叠时长。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def parse_order(value: str):
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def discover_order(work: Path, prefix: str):
    indexes = []
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)\.mp4$")
    for path in work.glob(f"{prefix}*.mp4"):
        match = pattern.match(path.name)
        if match:
            indexes.append(int(match.group(1)))
    return sorted(indexes)


def main():
    parser = argparse.ArgumentParser(description="使用 xfade 拼接统一规格的视频片段")
    parser.add_argument("--work", default="./output/clips", help="片段目录")
    parser.add_argument("--prefix", default="c", help="片段文件名前缀")
    parser.add_argument("--clip-duration", type=float, default=4.6, help="单个片段时长")
    parser.add_argument("--transition", type=float, default=1.1, help="转场重叠时长")
    parser.add_argument("--order", help="逗号分隔的片段序号，例如 0,1,2")
    parser.add_argument("--fade", type=float, default=1.2, help="首尾淡入淡出时长")
    parser.add_argument("--output", default="./output/master.mp4", help="输出视频")
    parser.add_argument("--crf", type=int, default=20, help="x264 CRF")
    parser.add_argument("--preset", default="medium", help="x264 preset")
    parser.add_argument("--fps", type=int, default=30, help="输出帧率")
    args = parser.parse_args()

    work = Path(args.work)
    order = parse_order(args.order) if args.order else discover_order(work, args.prefix)
    if not order:
        print("没有找到可拼接的片段。", file=sys.stderr)
        return 1

    step = args.clip_duration - args.transition
    if step <= 0:
        print("转场重叠时长必须小于片段时长。", file=sys.stderr)
        return 1

    clip_paths = []
    for idx in order:
        path = work / f"{args.prefix}{idx:02d}.mp4"
        if not path.exists():
            print(f"片段不存在：{path}", file=sys.stderr)
            return 1
        clip_paths.append(path)

    total = step * (len(clip_paths) - 1) + args.clip_duration
    fade = min(args.fade, total / 2)
    inputs = []
    for path in clip_paths:
        inputs += ["-i", str(path)]

    filters = []
    previous = "0:v"
    for k in range(1, len(clip_paths)):
        label = f"v{k}"
        filters.append(
            f"[{previous}][{k}:v]xfade=transition=fade:duration={args.transition}:"
            f"offset={step * k:.2f}[{label}]"
        )
        previous = label

    filters.append(
        f"[{previous}]fade=t=in:st=0:d={fade:.2f},"
        f"fade=t=out:st={total - fade:.2f}:d={fade:.2f}[vout]"
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", *inputs, "-filter_complex", ";".join(filters), "-map", "[vout]",
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-r", str(args.fps), "-an", "-y", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not output.exists():
        print(f"FAIL\n{result.stderr[-1200:]}", file=sys.stderr)
        return 1

    print(f"MASTER OK {total:.1f}s -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
