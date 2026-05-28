# process-documents

Video → Notion process documentation pipeline. Drop an MP4 in `source/`, point Claude Code at this repo, get a Draft-status workshop manual page in Notion.

See [PROJECT.md](PROJECT.md) for full context and conventions.

## Quick start

```bash
# One-time setup
scripts/download_model.sh                          # whisper large-v3, ~3GB

# Per video
cp ~/Downloads/foo.mp4 source/
# In Claude Code:  "process source/foo.mp4"
```

## What the scripts do

- [`scripts/download_model.sh`](scripts/download_model.sh) — pulls `models/ggml-large-v3.bin` (~3GB) from HuggingFace. Idempotent.
- [`scripts/transcribe.sh`](scripts/transcribe.sh) — `<video> → output/<slug>/transcript.{json,txt}` via ffmpeg + whisper-cli.
- [`scripts/extract_frames.py`](scripts/extract_frames.py) — reads `output/<slug>/steps.json` and writes one JPEG per step (1920px max, q=3) to `output/<slug>/frames/`.

## Requirements

Already installed on the workstation:

- ffmpeg
- whisper-cpp (provides `whisper-cli`, brew: `brew install whisper-cpp`)
- python3 (no third-party deps; stdlib only)
- git, gh (for pushing frames so Notion can embed them via raw URLs)
