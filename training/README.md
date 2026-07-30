# Training Pipeline — Smart Contract Review

Fine-tuning pipeline for the multi-model Teacher/Student architecture using QLoRA.

## Architecture

| Model | Base | LoRA Rank | Role |
|-------|------|-----------|------|
| **Teacher** | Qwen2.5-7B-Instruct | r=64 | Complex reasoning, redlines, M&A analysis |
| **Student** | Qwen2.5-3B-Instruct | r=32 | Classification, routing, simple extraction |

## Quick Start (RunPod)

```bash
# 1. Setup environment
bash runpod/setup.sh

# 2. Run full pipeline
bash runpod/launch.sh

# Or run individual phases:
bash runpod/launch.sh datasets    # Download + format
bash runpod/launch.sh internal    # Generate 500 internal examples
bash runpod/launch.sh teacher     # Teacher QLoRA training
bash runpod/launch.sh student     # Student QLoRA training
bash runpod/launch.sh distill     # Knowledge distillation
bash runpod/launch.sh eval        # Evaluation + comparison
```

## RunPod Configuration

- **GPU**: RTX 3090 (24GB) — Community Cloud
- **Container**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
- **Disk**: 50GB
- **Env vars**: `HF_TOKEN` (optional)

## Directory Structure

```
training/
├── __init__.py
├── requirements.txt
├── README.md
├── configs/
│   ├── teacher_qlora.yaml          # Teacher training config
│   ├── student_qlora.yaml          # Student training config
│   ├── distillation.yaml           # Distillation config
│   └── internal_dataset.yaml       # Internal dataset generation config
├── scripts/
│   ├── __init__.py
│   ├── download_datasets.py        # Step 2: Fetch from HuggingFace
│   ├── format_datasets.py          # Step 3: Convert to ChatML
│   ├── generate_internal_dataset.py# Step 4: Build redline dataset
│   ├── train_teacher.py            # Step 5: Teacher QLoRA
│   ├── train_student.py            # Step 6: Student QLoRA
│   ├── distill.py                  # Step 7: Knowledge distillation
│   ├── evaluate.py                 # Step 9: Evaluation
│   └── merge_adapter.py            # Step 10: Merge adapter
└── runpod/
    ├── setup.sh                    # RunPod environment setup
    └── launch.sh                   # Full pipeline launcher
```

## Adding More Internal Data (Extensible Design)

```bash
# Generate next 500 examples
python -m training.scripts.generate_internal_dataset \
    --batch-size 500 --start-index 500 --use-llm

# Merge all batches
python -m training.scripts.generate_internal_dataset --merge

# Retrain with accumulated data
python -m training.scripts.train_teacher --config configs/teacher_qlora.yaml --resume
```

## Design Patterns Used

- **Strategy**: Pluggable dataset downloaders, formatters, metrics
- **Registry**: Dataset/formatter registries (Open/Closed — add new datasets without modifying code)
- **Template Method**: Training pipeline (load → configure → train → save)
- **DRY**: `train_student.py` reuses `QLoRATrainer` from `train_teacher.py`
- **Single Responsibility**: Each script/class has one focused purpose
