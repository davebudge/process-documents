#!/usr/bin/env bash
# Transcribe a video to a timestamped JSON transcript.
# Usage: scripts/transcribe.sh source/foo.mp4
#   Produces:  output/foo/audio.wav  (intermediate, gitignored)
#              output/foo/transcript.json
#              output/foo/transcript.txt
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <video.mp4>" >&2
    exit 1
fi

VIDEO="$1"
if [[ ! -f "$VIDEO" ]]; then
    echo "Video not found: $VIDEO" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL="$PROJECT_ROOT/models/ggml-large-v3.bin"

if [[ ! -f "$MODEL" ]]; then
    echo "Whisper model missing. Run scripts/download_model.sh first." >&2
    exit 1
fi

BASENAME="$(basename "$VIDEO")"
SLUG="${BASENAME%.*}"
SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//')"
OUT_DIR="$PROJECT_ROOT/output/$SLUG"
mkdir -p "$OUT_DIR"

echo "[transcribe] $VIDEO -> output/$SLUG/"
echo "[1/3] Extracting 16kHz mono audio..."
ffmpeg -y -i "$VIDEO" -ar 16000 -ac 1 -c:a pcm_s16le "$OUT_DIR/audio.wav" 2>&1 | tail -3

echo "[2/3] Running whisper-cli (large-v3, Metal)..."
whisper-cli -m "$MODEL" -f "$OUT_DIR/audio.wav" -oj -of "$OUT_DIR/transcript" --print-progress 2>&1 | tail -5

echo "[3/3] Writing plain-text transcript..."
python3 - "$OUT_DIR/transcript.json" "$OUT_DIR/transcript.txt" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src) as f:
    data = json.load(f)
with open(dst, "w") as f:
    for s in data["transcription"]:
        f.write(f"[{s['timestamps']['from']} --> {s['timestamps']['to']}] {s['text'].strip()}\n")
PY

echo "Done. Slug: $SLUG"
echo "  output/$SLUG/transcript.json"
echo "  output/$SLUG/transcript.txt"
