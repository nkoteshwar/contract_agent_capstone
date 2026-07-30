# Smart Contract Training & Integration: Comprehensive Guide

This guide provides an in-depth look at our multi-model training pipeline, the rationale behind each step, and concrete examples of how data flows from raw legal text to a production-ready AI.

---

## 1. The Multi-Model Strategy (What & Why?)

We use two models instead of one to balance **intelligence** and **speed**.

| Component | model | Purpose | Why? |
| :--- | :--- | :--- | :--- |
| **Teacher** | Qwen2.5-7B | Deep Reasoning | Legal analysis requires high precision and "nuance." 7B parameters are needed to understand complex policy playbooks. |
| **Student** | Qwen2.5-3B | Fast Classification | 90% of a contract is "noise." A smaller, faster model can quickly identify which clauses need human or 7B attention. |

---

## 2. Stage 1: Dataset Preparation (The "What" and "How")

We aggregate 6 datasets to ensure the models aren't just good at "chatting," but are masters of "Legal-ese."

### Example: CUAD (Clause Analysis)
*   **What is it?**: 510 gold-standard contracts with expert annotations.
*   **How helps?**: Teaches the model to find specific needles (clauses) in haystacks (30-page PDFs).
*   **Sample Data (ChatML Format):**
```json
{
  "messages": [
    {"role": "system", "content": "Extract the 'Governing Law' clause from this passage."},
    {"role": "user", "content": "This Agreement shall be governed by the laws of the State of Delaware..."},
    {"role": "assistant", "content": "State of Delaware"}
  ]
}
```

---

## 3. Stage 2: Teacher Fine-Tuning (The QLoRA Process)

### What?
Fine-tuning the 7B model on the legal corpus using **QLoRA** (4-bit quantization).

### Why?
Training a 7B model normally requires 160GB+ VRAM. QLoRA compresses it to **13GB-16GB**, fitting easily on an affordable RTX 3090 (24GB).

### How? (Example Config)
The model's "attention" layers (q_proj, v_proj) are updated while the rest of the weights stay frozen. This is like giving an expert lawyer a "Legal Specialization" certificate without retraining their entire brain.

### Stage 2: Training Examples (Multi-Task Fine-Tuning)
To make the 7B model a "Legal Expert," we feed it mixed examples from different legal tasks (Classification, Extraction, NLI).

**Example: ContractNLI (Natural Language Inference)**
-   **User**: "Does this contract provide for a limitation of liability for direct damages? Clause: 'Neither party shall be liable for indirect or consequential damages.'"
-   **Assistant**: "No. The clause only limits indirect/consequential damages, not direct damages."

**Example: LEDGAR (Classification)**
-   **User**: "What is the category of this clause? Clause: 'This agreement is executed under the laws of New York...'"
-   **Assistant**: "Governing Law"

---

## 4. Stage 3: Internal Dataset Generation (The "Synthetic Redline")

### What?
We use the **Teacher** model to analyze your specific **Policy Playbook** against raw contract clauses.

### Why?
You don't have 10,000 human-labeled redlines. This step creates "Synthetic Gold" data for the Student.

### Stage 3: Training Example (The Generation Prompt)
When we run `generate_internal_dataset.py`, we send this to the 7B model:

-   **Input**:
    -   *Clause*: "Company shall indemnify Client against all claims without limit."
    -   *Policy Rule*: "Liability for indemnification must be capped at 100% of the annual contract value ($500k)."
-   **Teacher Output (JSON)**:
    ```json
    {
      "risk_level": "HIGH",
      "reasoning": "The clause provides an unlimited indemnity, violating our $500k cap policy.",
      "redline_suggestion": "Company's liability under this section shall not exceed $500,000 in the aggregate."
    }
    ```

---

## 5. Stage 4: Student Distillation (Learning from the Teacher)

### What?
Training the 3B Student on the Teacher's outputs.

### Why?
The Student learns to "mimic" the Teacher's logic but at **3x the speed** and **half the cost**.

### Stage 4: Training Example (The Distillation Message)
We take the Teacher's JSON output (from Stage 3) and format it into a conversation for the 3B Student model:

-   **User**: "Analyze this clause against policy: 'Company shall indemnify Client without limit.' Policy: 'Cap at $500k.'"
-   **Assistant**: "Risk: HIGH. Reasoning: The clause provides an unlimited indemnity, violating our $500k cap. Redline: 'Liability shall not exceed $500,000.'"

### Example Integration Flow:
1.  **User uploads PDF**.
2.  **Student (3B)**: "This is a Limitation of Liability clause." (Latency: 100ms)
3.  **UI**: Highlights clause.
4.  **Teacher (7B)**: "This is High Risk because..." (Latency: 2s)
5.  **UI**: Provides the Redline suggestion.

---

## 6. Safety, Evaluation & Guardrails

Legal AI cannot "hallucinate." We use three layers to ensure safety:

1.  **Strict JSON Output**: The models are trained to respond *only* in a structured format. This prevents them from being overly "chatty" or offering unasked legal advice.
2.  **ROUGE & Exact Match**: Our `evaluate.py` script doesn't just check if the model "feels" right; it measures the mathematical overlap between the model's suggestion and the ground-truth legal text.
3.  **Confidence Thresholds**: In the application, if the Student model has low confidence in a classification, it automatically "prompts up" to the 7B Teacher or flags it for human review.

---

## 7. Human-in-the-Loop (Scaling to 50,000+)

1.  **Batching**: Run `generate_internal_dataset.py` with `--start-index 5000`.
2.  **Audit Mode**: Before distillation, a legal expert should review a random 5% sample of the Teacher's synthetic redlines.
3.  **Active Learning**: If the expert corrects a redline, that correction is added back into the "Internal Dataset" as a "Gold Example," making the next training run even stronger.

---

## 8. Common Troubleshooting (RunPod Hub)

| Issue | Solution |
| :--- | :--- |
| **CUDA Out of Memory (OOM)** | Reduce `per_device_train_batch_size` (try 2) and enable `gradient_checkpointing: true`. Also set `export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. |
| **AttributeError: set_submodule** | This is a `bitsandbytes` version conflict. Our `utils.py` includes a monkey-patch to fix this automatically. |
| **ValueError: CVE-2025-32434** | `torch.load` security check. Upgrade torch via: `pip install --upgrade torch>=2.6.0` or don't use `--resume`. |
| **Slow Training** | Ensure `bf16: true` is set and you are using an RTX 3090 or better. |
| **Spot Interruption** | Re-run the script with the `--resume` flag. It will look in `./outputs/` for the latest checkpoint. |

---

---

## 10. Understanding Training Steps (The Math)

If you see `0/4705 steps` in your logs, here is how that number is calculated:

*   **Dataset Size**: 30,109 examples.
*   **Effective Batch Size**: 32 (Batch 4 x Accumulation 8).
*   **Steps per Epoch**: 30,109 / 32 = ~941 steps.
*   **Total Steps (5 Epochs)**: 941 x 5 = **4,705 steps**.

> [!TIP]
> **1 Step = 1 Learning Update**. In each step, the model looks at 32 examples, calculates the error, and updates its weights.

---

## 11. Post-Training: Merged vs. Adapter Inference

You have two ways to run the fine-tuned model on your production server.

### Option A: The Merged Model (Simplest & Fastest)
You run `merge_adapter.py` on RunPod to create a standalone model folder.
*   **What you move to the server**: Just one folder (the merged weights).
*   **Pros**: No complex dependencies in your server code; faster loading.
*   **Example**:
    ```python
    model = AutoModelForCausalLM.from_pretrained("./models/teacher_final")
    ```

### Option B: Base + Adapter (Best for swapping)
You keep the original Qwen base model and just move the small (200MB) adapter file from `outputs/`.
*   **What you move to the server**: Both the base model (cached) and the adapter file.
*   **Pros**: If you have multiple custom policies (e.g. Sales vs. Procurement), you can swap 200MB adapters instantly without reloading the 15GB base model.
*   **Example**:
    ```python
    base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
    model = PeftModel.from_pretrained(base_model, "./adapters/legal_v1")
    ```

---

## 11. Deployment Flow: Step-by-Step

1.  **Stage 1**: `format_datasets.py` (✓ Done)
2.  **Stage 2**: `train_teacher.py` (✓ Done - Teacher Expert trained)
3.  **Stage 3**: `generate_internal_dataset.py` (✓ Done - 5k synthetic labels)
4.  **Stage 4**: `train_student.py` (✓ Done - Student Base trained)
9.  **Stage 9**: `distill.py` (**PENDING** - Resume on new Pod)
10. **Final**: `merge_adapter.py` & Update Backend `.env`.

---

## 9. RunPod Resilience (Spot Instance Pro-Tips)

To ensure you don't lose data or waste money on spot instances:

1.  **Persistent Volumes**: Always attach a Network Volume to `/contract_agent_capstone/data` and `/contract_agent_capstone/outputs`.
2.  **Environment Setup**: Set these in your RunPod terminal before training:
    ```bash
    # Ensure large models don't fill up the tiny root disk
    export HF_HOME=/workspace/huggingface_cache
    
    # Required for gated models
    export HF_TOKEN="your_token_here"
    
    # Prevent fragmentation OOM
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    ```
3.  **The Resume Workflow**:
    If your pod is terminated or you close your laptop, simply connect back and run:
    ```bash
    python -m training.scripts.train_student --config training/configs/student_qlora.yaml --resume
    ```

4.  **Running in Background (Laptop Safety)**:
    Don't keep your terminal open for 6 hours! Use `screen` to run in the background. 
    
    *   **Install Screen** (If missing): `apt-get update && apt-get install -y screen`
    *   **Start**: `screen -S training`
    *   **Run**: Launch your command inside the screen.
    *   **Detach**: Press `Ctrl+A` then `D`.
    *   **Close Laptop**: You are safe!
    *   **Check Stats**: Reconnect and type `screen -r training`.

4.  **Session Persistence (Laptop Safety)**:
    If you don't want the training to stop when you close your laptop, use `screen`:
    1.  Start a new session: `screen -S training`
    2.  Run your training command.
    3.  **Detach**: Press `Ctrl + A` then `D`.
    4.  **Close your laptop**.
    5.  **Reattach later**: Open terminal and type `screen -r training`.
5.  **Managing Background Processes**:
    If you started a process with `nohup` or `screen` and need to stop it:
    *   **Find PID**: `ps aux | grep training.scripts`
    *   **Kill Specific**: `kill <PID_Number>`
    *   **Kill All**: `pkill -f training.scripts`
