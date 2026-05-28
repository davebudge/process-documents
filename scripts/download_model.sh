#!/usr/bin/env bash
# Download the whisper.cpp large-v3 model (~3GB). Run once.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/models"
MODEL_FILE="$MODEL_DIR/ggml-large-v3.bin"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin"

mkdir -p "$MODEL_DIR"

if [[ -f "$MODEL_FILE" ]]; then
    echo "Model already present: $MODEL_FILE"
    exit 0
fi

echo "Downloading large-v3 model (~3GB) to $MODEL_FILE"
curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"
echo "Done."
