#!/bin/bash
# RunPod Training Launch Script
# Runs the full training pipeline sequentially.
# Can be run end-to-end or per-phase.
#
# Usage:
#   bash runpod/launch.sh              # Full pipeline
#   bash runpod/launch.sh datasets     # Only download + format
#   bash runpod/launch.sh internal     # Only generate internal dataset
#   bash runpod/launch.sh teacher      # Only teacher training
#   bash runpod/launch.sh student      # Only student training
#   bash runpod/launch.sh distill      # Only distillation
#   bash runpod/launch.sh eval         # Only evaluation

set -e

PHASE="${1:-all}"
TRAINING_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$TRAINING_DIR"

echo "=== Training Pipeline ==="
echo "Phase: $PHASE"
echo "Working dir: $TRAINING_DIR"
echo ""

# Phase 1: Download datasets
if [ "$PHASE" = "all" ] || [ "$PHASE" = "datasets" ]; then
    echo ">>> Phase 1: Downloading datasets…"
    python -m training.scripts.download_datasets --output-dir ./data/raw
    echo ""

    echo ">>> Phase 1b: Formatting datasets to ChatML…"
    python -m training.scripts.format_datasets --raw-dir ./data/raw --output-dir ./data/processed
    echo ""
fi

# Phase 2: Generate internal dataset (Batch 1 — 500 examples)
if [ "$PHASE" = "all" ] || [ "$PHASE" = "internal" ]; then
    echo ">>> Phase 2: Generating internal dataset (500 examples)…"
    python -m training.scripts.generate_internal_dataset \
        --batch-size 500 \
        --start-index 0 \
        --output-dir ./data/internal \
        --cuad-path ./data/raw/cuad \
        --use-llm \
        --model "Qwen/Qwen2.5-7B-Instruct"
    echo ""
fi

# Phase 3: Teacher QLoRA training
if [ "$PHASE" = "all" ] || [ "$PHASE" = "teacher" ]; then
    echo ">>> Phase 3: Training Teacher (Qwen2.5-7B-Instruct + QLoRA)…"
    python -m training.scripts.train_teacher --config configs/teacher_qlora.yaml
    echo ""
fi

# Phase 4: Student QLoRA training
if [ "$PHASE" = "all" ] || [ "$PHASE" = "student" ]; then
    echo ">>> Phase 4: Training Student (Qwen2.5-3B-Instruct + QLoRA)…"
    python -m training.scripts.train_student --config configs/student_qlora.yaml
    echo ""
fi

# Phase 5: Knowledge distillation
if [ "$PHASE" = "all" ] || [ "$PHASE" = "distill" ]; then
    echo ">>> Phase 5: Knowledge Distillation (Teacher → Student)…"
    python -m training.scripts.distill --config configs/distillation.yaml
    echo ""
fi

# Phase 6: Evaluation
if [ "$PHASE" = "all" ] || [ "$PHASE" = "eval" ]; then
    echo ">>> Phase 6: Evaluating models…"

    echo "  Evaluating baseline…"
    python -m training.scripts.evaluate --model baseline --max-examples 100

    echo "  Evaluating teacher…"
    python -m training.scripts.evaluate --model teacher --max-examples 100

    echo "  Evaluating student…"
    python -m training.scripts.evaluate --model student --max-examples 100

    echo "  Evaluating distilled student…"
    python -m training.scripts.evaluate --model distilled --max-examples 100

    echo "  Generating comparison report…"
    python -m training.scripts.evaluate --compare
    echo ""
fi

echo "=== Pipeline Complete ==="
echo "Results: ./outputs/eval/"
echo "Adapters: ./outputs/teacher_qlora/ ./outputs/student_qlora/ ./outputs/student_distilled/"
