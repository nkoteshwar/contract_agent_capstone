"""
Adapter Merge & Export Script
Merges LoRA adapters into base model weights for deployment.

Usage:
    python -m training.scripts.merge_adapter --base-model Qwen/Qwen2.5-7B-Instruct \\
           --adapter-path ./outputs/teacher_qlora --output-dir ./outputs/teacher_merged

    python -m training.scripts.merge_adapter --base-model Qwen/Qwen2.5-3B-Instruct \\
           --adapter-path ./outputs/student_distilled --output-dir ./outputs/student_merged
"""

import argparse
import os
from pathlib import Path

from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


def merge_adapter(base_model: str, adapter_path: str, output_dir: str,
                  push_to_hub: bool = False, hub_name: str = None):
    """Merge LoRA adapter into base model and save."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load base model (full precision for merging)
    logger.info(f"Loading base model: {base_model}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

    # Load and merge adapter
    logger.info(f"Loading adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)

    logger.info("Merging adapter into base model…")
    model = model.merge_and_unload()

    # Save merged model
    logger.info(f"Saving merged model to {output_dir}")
    model.save_pretrained(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    # Log size
    total_size = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fns in os.walk(str(output_path))
        for f in fns
    )
    logger.info(f"✓ Merged model size: {total_size / 1e9:.2f} GB")

    # Optional: push to HuggingFace Hub
    if push_to_hub and hub_name:
        logger.info(f"Pushing to HuggingFace Hub: {hub_name}")
        model.push_to_hub(hub_name)
        tokenizer.push_to_hub(hub_name)
        logger.info(f"✓ Pushed to {hub_name}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA Adapter")
    parser.add_argument("--base-model", type=str, required=True)
    parser.add_argument("--adapter-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--push-to-hub", action="store_true")
    parser.add_argument("--hub-name", type=str, default=None)
    args = parser.parse_args()

    merge_adapter(args.base_model, args.adapter_path, args.output_dir,
                  args.push_to_hub, args.hub_name)


if __name__ == "__main__":
    main()
