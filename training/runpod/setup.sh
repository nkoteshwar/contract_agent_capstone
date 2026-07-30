#!/bin/bash
# RunPod Environment Setup
# Run this once when your pod starts to install dependencies and download models.
#
# Usage: bash runpod/setup.sh

set -e

echo "=== RunPod Training Environment Setup ==="

# 1. Install Python dependencies
echo "[1/4] Installing dependencies…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 2. Login to HuggingFace (for gated models if needed)
if [ -n "$HF_TOKEN" ]; then
    echo "[2/4] Logging into HuggingFace…"
    huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential
else
    echo "[2/4] HF_TOKEN not set — skipping HuggingFace login"
    echo "       Set HF_TOKEN env var if you need access to gated models"
fi

# 3. Pre-download model weights (cached for subsequent runs)
echo "[3/4] Pre-downloading model weights…"
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import snapshot_download

print('  Downloading Qwen2.5-7B-Instruct tokenizer…')
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', trust_remote_code=True)

print('  Downloading Qwen2.5-3B-Instruct tokenizer…')
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-3B-Instruct', trust_remote_code=True)

print('  Pre-caching model configs…')
snapshot_download('Qwen/Qwen2.5-7B-Instruct', allow_patterns=['*.json', '*.txt'])
snapshot_download('Qwen/Qwen2.5-3B-Instruct', allow_patterns=['*.json', '*.txt'])
print('  ✓ Model configs cached')
"

# 4. Create output directories
echo "[4/4] Creating directories…"
mkdir -p data/raw data/processed data/internal data/teacher_labels
mkdir -p outputs/teacher_qlora outputs/student_qlora outputs/student_distilled outputs/eval

echo ""
echo "=== Setup Complete ==="
echo "Run 'bash runpod/launch.sh' to start the full training pipeline"
echo "Or run individual steps manually (see training/README.md)"
