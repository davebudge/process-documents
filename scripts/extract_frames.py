#!/usr/bin/env python3
"""
Extract one frame per step from a video using ffmpeg, based on timestamps in steps.json.

Usage:
    scripts/extract_frames.py <video_path> <steps_json> <output_dir>

steps.json format:
    {
        "video": "source/foo.mp4",
        "steps": [
            {"n": 1, "timestamp_sec": 12.5, "title": "..."},
            {"n": 2, "timestamp_sec": 28.0, "title": "..."},
            ...
        ]
    }

Writes <output_dir>/frames/step-01.png, step-02.png, etc.
"""
import json
import subprocess
import sys
from pathlib import Path


def extract_frame(video: Path, timestamp_sec: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp_sec:.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-vf",
        "scale='min(1920,iw)':-2",
        "-q:v",
        "3",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"ffmpeg failed for {out_path}")


def main() -> None:
    if len(sys.argv) != 4:
        sys.stderr.write(__doc__)
        raise SystemExit(2)

    video = Path(sys.argv[1])
    steps_file = Path(sys.argv[2])
    out_dir = Path(sys.argv[3])

    if not video.exists():
        raise SystemExit(f"Video not found: {video}")
    if not steps_file.exists():
        raise SystemExit(f"Steps file not found: {steps_file}")

    data = json.loads(steps_file.read_text())
    steps = data["steps"]
    frames_dir = out_dir / "frames"

    for step in steps:
        n = step["n"]
        ts = float(step["timestamp_sec"])
        out_path = frames_dir / f"step-{n:02d}.jpg"
        print(f"[step {n:02d}] t={ts:.1f}s  ->  {out_path.relative_to(out_dir.parent)}")
        extract_frame(video, ts, out_path)

    print(f"\nExtracted {len(steps)} frames to {frames_dir.relative_to(out_dir.parent)}/")


if __name__ == "__main__":
    main()
