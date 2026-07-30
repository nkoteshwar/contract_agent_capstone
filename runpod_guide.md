# RunPod Execution Guide — Step by Step

## Prerequisites
- **RunPod account** at [runpod.io](https://runpod.io) with credits loaded (~$10–15 recommended)
- **HuggingFace account** (free, for model downloads)
- Your code pushed to a Git repo (GitHub/GitLab)

---

## Step 1: Create a RunPod GPU Pod

1. Go to [runpod.io](https://runpod.io) → **Pods** → **+ GPU Pod**
2. Select these settings:

| Setting | Value |
|---------|-------|
| **GPU** | RTX 3090 (24 GB) |
| **Cloud Type** | Community Cloud (~$0.22/hr) |
| **Container Image** | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` |
| **Disk** | 50 GB (Container) + 20 GB (Volume) |
| **Start Command** | *(leave blank)* |

3. Under **Environment Variables**, add:
   - `HF_TOKEN` = your HuggingFace token (optional, only if using gated models)

4. Click **Deploy** → wait for pod to be **Running**

---

## Step 2: Connect to the Pod

1. Click **Connect** → **Start Web Terminal** (or use SSH)
2. In the terminal:

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/contract_agent_capstone.git
cd contract_agent_capstone/training
```

---

## Step 3: Install Dependencies (~2 min)

```bash
pip install --quiet -r requirements.txt
```

---

## Step 3.5: Enable Session Persistence (CRITICAL)

To prevent training from stopping when you close your laptop:

1.  **Start a Session**: Type `screen -S training`
2.  Now run all subsequent steps inside this window.
3.  **To Leave**: Press `Ctrl + A` then `D` (the training will keep running!).
4.  **To Return**: Type `screen -r training`

> [!TIP]
> Or run the setup script which also pre-caches model configs:
> ```bash
> bash runpod/setup.sh
> ```

---

## Step 4: Download Datasets (~5–10 min)

```bash
# See what will be downloaded (dry run)
python -m training.scripts.download_datasets --dry-run

# Download all 5 datasets from HuggingFace
python -m training.scripts.download_datasets --output-dir ./data/raw
```

**Expected output**: `download_manifest.json` in `./data/raw/` listing all downloads.

> [!NOTE]
> Datasets: CUAD (~200MB), LEDGAR (~50MB), ContractNLI (~30MB), MAUD (~100MB), LegalBench (~5MB)

---

## Step 5: Format Datasets to ChatML (~3–5 min)

```bash
# Format all datasets (creates train/validation/test splits)
python -m training.scripts.format_datasets \
    --raw-dir ./data/raw \
    --output-dir ./data/processed

# Verify: check file counts
ls -la data/processed/*/
```

**Expected output**: JSONL files in `data/processed/{cuad,cuad_simple,ledgar,contract_nli,maud,risk_routing}/` with `train.jsonl`, `validation.jsonl`, `test.jsonl` each.

---

## Step 6: Generate Internal Dataset — Batch 1 (~30–60 min)

```bash
# Generate 500 redline examples using Teacher model (LLM inference)
python -m training.scripts.generate_internal_dataset \
    --batch-size 500 \
    --start-index 0 \
    --output-dir ./data/internal \
    --cuad-path ./data/raw/cuad \
    --use-llm \
    --model "Qwen/Qwen2.5-7B-Instruct"

# Check stats
python -m training.scripts.generate_internal_dataset --stats --output-dir ./data/internal
```

**Expected output**: `data/internal/batch_001.jsonl` + `data/internal/chatml/batch_001.jsonl`

> [!TIP]
> **To save time during first run**, use template mode (no GPU needed, faster but lower quality):
> ```bash
> python -m training.scripts.generate_internal_dataset --batch-size 500 --start-index 0
> ```
> Then regenerate with `--use-llm` later for production quality.

---

## Step 7: Train Teacher Model (~1.5–2 hrs)

```bash
python -m training.scripts.train_teacher --config training/configs/teacher_qlora.yaml
```

**What happens**:
- Loads Qwen2.5-7B-Instruct (4-bit quantized → ~4.5 GB VRAM)
- Applies LoRA (r=64, α=128) → ~1.6% trainable params
- Trains 3 epochs on CUAD + ContractNLI + MAUD + Internal data
- Saves adapter to `./outputs/teacher_qlora/` (~150 MB)

**Monitor**: Watch for decreasing `eval_loss` every 200 steps. Training should reach eval_loss < 1.5.

> [!IMPORTANT]
> If training crashes with OOM, reduce batch size:
> Edit [training/configs/teacher_qlora.yaml](file:///Users/karthikvenkatesan/contract_agent_capstone/training/configs/teacher_qlora.yaml) → set `per_device_train_batch_size: 2`

---

## Step 8: Train Student Model (~45 min–1 hr)

```bash
python -m training.scripts.train_student --config training/configs/student_qlora.yaml
```

**What happens**:
- Loads Qwen2.5-3B-Instruct (4-bit → ~2 GB VRAM)
- LoRA (r=32, α=64), 5 epochs on LEDGAR + CUAD-simple + Risk routing
- Saves adapter to `./outputs/student_qlora/` (~80 MB)

---

## Step 9: Knowledge Distillation (~2–3 hrs)

```bash
# Run both phases (labels + training)
python -m training.scripts.distill --config training/configs/distillation.yaml

# Or run phases separately to manage costs:
# Phase 1: Generate teacher labels (~1–2 hrs)
python -m training.scripts.distill --config training/configs/distillation.yaml --phase labels

# Phase 2: Train student on teacher outputs (~1 hr)
python -m training.scripts.distill --config training/configs/distillation.yaml --phase train
```

**Saves to**: `./outputs/student_distilled/`

---

## Step 10: Evaluate All Models (~30 min)

```bash
# Evaluate baseline (no fine-tuning)
python -m training.scripts.evaluate --model baseline --max-examples 50

# Evaluate fine-tuned Teacher
python -m training.scripts.evaluate --model teacher --max-examples 50

# Evaluate fine-tuned Student
python -m training.scripts.evaluate --model student --max-examples 50

# Evaluate distilled Student
python -m training.scripts.evaluate --model distilled --max-examples 50

# Generate comparison report
python -m training.scripts.evaluate --compare
```

**Output**: `outputs/eval/comparison_report.md` — markdown table comparing all models.

---

## Step 11: Export Adapters (~5 min per model)

```bash
# Download the LoRA adapters (small — ~150 MB each)
# From RunPod web terminal: use the file browser, or:

# Option A: Push to HuggingFace Hub
python -m training.scripts.merge_adapter \
    --base-model Qwen/Qwen2.5-7B-Instruct \
    --adapter-path ./outputs/teacher_qlora \
    --output-dir ./outputs/teacher_merged \
    --push-to-hub --hub-name your-username/contract-teacher-qlora

# Option B: Download via RunPod file manager
# Click the folder icon in RunPod → navigate to outputs/ → download

# Option C: SCP from pod (if using SSH)
scp -r root@YOUR_POD_IP:/workspace/contract_agent_capstone/training/outputs/ ./local_outputs/
```

---

## Step 12: Stop the Pod!

> [!CAUTION]
> **Stop your pod immediately after downloading results to avoid unnecessary charges.**
> RunPod → Pods → click **Stop** (or **Terminate** if done permanently)

---

## Cost Summary

| Step | Duration | Cost (RTX 3090 @ $0.22/hr) |
|------|----------|---------------------------|
| Setup + Downloads | 15 min | $0.06 |
| Format datasets | 5 min | $0.02 |
| Internal dataset (500) | 45 min | $0.16 |
| Train Teacher | 1.5 hrs | $0.33 |
| Train Student | 1 hr | $0.22 |
| Distillation | 2.5 hrs | $0.55 |
| Evaluation | 30 min | $0.11 |
| **Total** | **~6.5 hrs** | **~$1.45** |

> [!NOTE]
> Actual costs may vary. The estimates above assume optimistic runtimes with 500 internal examples. Full 5K run will cost more (~$10–12 total).

---

## Later: Generate More Internal Data

```bash
# Generate batch 2 (examples 500–999)
python -m training.scripts.generate_internal_dataset \
    --batch-size 500 --start-index 500 --use-llm --output-dir ./data/internal

# Generate batch 3 (examples 1000–1499)
python -m training.scripts.generate_internal_dataset \
    --batch-size 500 --start-index 1000 --use-llm --output-dir ./data/internal

# Merge all batches
python -m training.scripts.generate_internal_dataset --merge --output-dir ./data/internal

# Retrain with new data
python -m training.scripts.train_teacher --config training/configs/teacher_qlora.yaml --resume
```
