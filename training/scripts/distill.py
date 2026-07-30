"""
Knowledge Distillation Script
Teacher → Student response-based distillation.

Phase 1: Run fine-tuned Teacher inference to generate soft labels
Phase 2: Fine-tune Student on Teacher's outputs

Usage:
    python -m training.scripts.distill --config configs/distillation.yaml
    python -m training.scripts.distill --config configs/distillation.yaml --phase labels
    python -m training.scripts.distill --config configs/distillation.yaml --phase train
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

import jsonlines
import yaml
from tqdm import tqdm

from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class DistillationConfig:
    """Loads distillation config from YAML."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self._config = yaml.safe_load(f)

    @property
    def teacher_adapter(self) -> str:
        return self._config["teacher"]["adapter_path"]

    @property
    def teacher_base(self) -> str:
        return self._config["teacher"]["base_model"]

    @property
    def student_adapter(self) -> str:
        return self._config["student"]["adapter_path"]

    @property
    def student_base(self) -> str:
        return self._config["student"]["base_model"]

    @property
    def distillation(self) -> Dict:
        return self._config.get("distillation", {})

    @property
    def data(self) -> Dict:
        return self._config.get("data", {})


# ---------------------------------------------------------------------------
# Phase 1: Generate Teacher labels
# ---------------------------------------------------------------------------

class TeacherLabelGenerator:
    """
    Runs fine-tuned Teacher to generate soft labels on source data.
    Single Responsibility: only handles teacher inference.
    """

    def __init__(self, base_model: str, adapter_path: str):
        self.base_model = base_model
        self.adapter_path = adapter_path
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        logger.info(f"Loading Teacher: {self.base_model} + {self.adapter_path}")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model, quantization_config=bnb_config, device_map="auto"
        )
        self._model = PeftModel.from_pretrained(base_model, self.adapter_path)
        self._model.eval()

    def generate_labels(self, source_dir: Path, output_dir: Path,
                        tasks: List[str], max_examples: int = 10000,
                        resume: bool = False) -> Path:
        """Generate teacher labels on source data."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "teacher_labels.jsonl"

        if resume and output_file.exists():
            logger.info(f"⏭ Resuming Phase 1: Found existing labels at {output_file}. Skipping generation.")
            return output_file

        self._load_model()
        all_examples = self._load_source_data(source_dir, tasks, max_examples)
        logger.info(f"Generating teacher labels for {len(all_examples)} examples…")

        labeled_examples = []
        for example in tqdm(all_examples, desc="Teacher inference"):
            messages = example.get("messages", [])
            if not messages or len(messages) < 2:
                continue

            # Use system + user messages as input, generate teacher's response
            input_messages = [m for m in messages if m["role"] != "assistant"]
            teacher_response = self._generate_response(input_messages)

            labeled_example = {
                "messages": [
                    *input_messages,
                    {"role": "assistant", "content": teacher_response}
                ],
                "task": example.get("task", "unknown"),
                "source": "teacher_distillation",
                "original_response": messages[-1]["content"] if messages[-1]["role"] == "assistant" else "",
            }
            labeled_examples.append(labeled_example)

        # Save teacher labels
        output_file = output_dir / "teacher_labels.jsonl"
        with jsonlines.open(str(output_file), mode="w") as writer:
            writer.write_all(labeled_examples)

        logger.info(f"✓ Teacher labels saved: {len(labeled_examples)} examples → {output_file}")
        return output_file

    def _load_source_data(self, source_dir: Path, tasks: List[str],
                          max_examples: int) -> List[Dict]:
        """Load source data from processed datasets."""
        examples = []
        for task_dir in source_dir.iterdir():
            if not task_dir.is_dir():
                continue

            # Load train + validation for source data
            for split in ["train", "validation"]:
                split_file = task_dir / f"{split}.jsonl"
                if split_file.exists():
                    with jsonlines.open(str(split_file)) as reader:
                        for item in reader:
                            if not tasks or item.get("task", "") in tasks or task_dir.name in tasks:
                                examples.append(item)

            if len(examples) >= max_examples:
                break

        import random
        random.seed(42)
        random.shuffle(examples)
        return examples[:max_examples]

    def _generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response using the teacher model."""
        import torch

        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt", truncation=True,
                                  max_length=1536).to(self._model.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                pad_token_id=self._tokenizer.pad_token_id,
            )

        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        return response


# ---------------------------------------------------------------------------
# Phase 2: Distillation training
# ---------------------------------------------------------------------------

class DistillationTrainer:
    """
    Fine-tunes Student on Teacher's outputs (response-based distillation).
    Reuses QLoRATrainer infrastructure from train_teacher.py.
    """

    def __init__(self, config: DistillationConfig):
        self.config = config

    def train(self, teacher_labels_path: Path, resume: bool = False):
        """Train student on teacher labels."""
        from training.scripts.train_teacher import TrainingConfig, QLoRATrainer

        # Create a synthetic config that adapts distillation params to training format
        dist_cfg = self.config.distillation
        synthetic_config = {
            "model": {
                "name": self.config.student_base,
                "max_seq_length": 2048,
            },
            "quantization": {
                "load_in_4bit": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_compute_dtype": "bfloat16",
                "bnb_4bit_use_double_quant": True,
            },
            "lora": {
                "r": 32,
                "lora_alpha": 64,
                "lora_dropout": 0.05,
                "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                                   "gate_proj", "up_proj", "down_proj"],
                "task_type": "CAUSAL_LM",
                "bias": "none",
            },
            "training": {
                "output_dir": dist_cfg.get("output_dir", "./outputs/student_distilled"),
                "num_train_epochs": dist_cfg.get("num_train_epochs", 2),
                "per_device_train_batch_size": dist_cfg.get("per_device_train_batch_size", 4),
                "gradient_accumulation_steps": dist_cfg.get("gradient_accumulation_steps", 4),
                "learning_rate": dist_cfg.get("learning_rate", 1e-4),
                "lr_scheduler_type": dist_cfg.get("lr_scheduler_type", "cosine"),
                "warmup_ratio": dist_cfg.get("warmup_ratio", 0.05),
                "bf16": dist_cfg.get("bf16", True),
                "gradient_checkpointing": dist_cfg.get("gradient_checkpointing", True),
                "save_steps": dist_cfg.get("save_steps", 200),
                "logging_steps": dist_cfg.get("logging_steps", 10),
                "seed": dist_cfg.get("seed", 42),
                "eval_strategy": "steps",
                "eval_steps": dist_cfg.get("save_steps", 200),
                "load_best_model_at_end": True,
                "metric_for_best_model": "eval_loss",
                "report_to": "none",
                "save_total_limit": 3,
            },
            "data": {
                "datasets": [{"name": "_distillation", "weight": 1.0}],
                "train_split": "train",
                "eval_split": "validation",
                "data_dir": str(teacher_labels_path.parent),
            },
        }

        # Prepare distillation data with splits
        self._prepare_distillation_splits(teacher_labels_path)

        # Write temp config
        import tempfile
        config_path = Path(tempfile.mktemp(suffix=".yaml"))
        with open(config_path, "w") as f:
            yaml.dump(synthetic_config, f)

        # Reuse QLoRATrainer (DRY)
        config = TrainingConfig(str(config_path))
        trainer = QLoRATrainer(config)
        trainer.run(resume=resume)

        # Cleanup temp config
        config_path.unlink(missing_ok=True)

    def _prepare_distillation_splits(self, labels_path: Path):
        """Split teacher labels into train/val for distillation."""
        with jsonlines.open(str(labels_path)) as reader:
            examples = list(reader)

        from sklearn.model_selection import train_test_split
        train_data, val_data = train_test_split(examples, test_size=0.1, random_state=42)

        dist_dir = labels_path.parent / "_distillation"
        dist_dir.mkdir(parents=True, exist_ok=True)

        with jsonlines.open(str(dist_dir / "train.jsonl"), mode="w") as writer:
            writer.write_all(train_data)
        with jsonlines.open(str(dist_dir / "validation.jsonl"), mode="w") as writer:
            writer.write_all(val_data)

        logger.info(f"Distillation splits: {len(train_data)} train, {len(val_data)} val")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Knowledge Distillation")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to distillation.yaml config")
    parser.add_argument("--phase", type=str, choices=["all", "labels", "train"],
                        default="all", help="Which phase to run")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing labels or checkpoint")
    args = parser.parse_args()

    config = DistillationConfig(args.config)
    data_cfg = config.data
    source_dir = Path(data_cfg.get("source_dir", "./data/processed"))
    labels_dir = Path(data_cfg.get("teacher_labels_dir", "./data/teacher_labels"))
    tasks = data_cfg.get("tasks", [])
    max_examples = config.distillation.get("num_examples", 10000)

    if args.phase in ("all", "labels"):
        logger.info("=== Phase 1: Generating Teacher Labels ===")
        teacher_gen = TeacherLabelGenerator(config.teacher_base, config.teacher_adapter)
        labels_path = teacher_gen.generate_labels(source_dir, labels_dir, tasks, max_examples, resume=args.resume)
    else:
        labels_path = labels_dir / "teacher_labels.jsonl"

    if args.phase in ("all", "train"):
        logger.info("=== Phase 2: Distillation Training ===")
        trainer = DistillationTrainer(config)
        trainer.train(labels_path, resume=args.resume)

    logger.info("✓ Distillation complete!")


if __name__ == "__main__":
    main()
