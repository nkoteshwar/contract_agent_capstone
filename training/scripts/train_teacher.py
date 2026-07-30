"""
Teacher QLoRA Training Script
Trains Qwen2.5-7B-Instruct with QLoRA on multi-task legal datasets.

Follows the Strategy pattern (pluggable model configs via YAML) and
Template Method (load→configure→train→save) from existing codebase.

Usage:
    python -m training.scripts.train_teacher --config configs/teacher_qlora.yaml
    python -m training.scripts.train_teacher --config configs/teacher_qlora.yaml --resume
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Config loader — Single Responsibility
# ---------------------------------------------------------------------------

class TrainingConfig:
    """Loads and validates YAML training config."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self._config = yaml.safe_load(f)

    @property
    def model_name(self) -> str:
        return self._config["model"]["name"]

    @property
    def max_seq_length(self) -> int:
        return self._config["model"].get("max_seq_length", 2048)

    @property
    def quantization(self) -> Dict:
        return self._config.get("quantization", {})

    @property
    def lora(self) -> Dict:
        return self._config.get("lora", {})

    @property
    def training(self) -> Dict:
        return self._config.get("training", {})

    @property
    def data(self) -> Dict:
        return self._config.get("data", {})

    @property
    def output_dir(self) -> str:
        return self.training.get("output_dir", "./outputs/qlora")


# ---------------------------------------------------------------------------
# Data loader — loads and combines multi-task datasets
# ---------------------------------------------------------------------------

class MultiTaskDataLoader:
    """
    Loads and interleaves multiple JSONL datasets with configurable weights.
    Reuses the weighted mixing pattern from the config.
    """

    def __init__(self, data_dir: Path, dataset_configs: List[Dict[str, Any]]):
        self.data_dir = data_dir
        self.dataset_configs = dataset_configs

    def load_split(self, split: str) -> Any:
        """Load and merge a split from all configured datasets."""
        import jsonlines
        from datasets import Dataset

        all_examples = []

        for ds_config in self.dataset_configs:
            ds_name = ds_config["name"]
            weight = ds_config.get("weight", 1.0)

            # Check for internal dataset (batch-based)
            if ds_name == "internal":
                examples = self._load_internal_dataset(split)
            else:
                file_path = self.data_dir / ds_name / f"{split}.jsonl"
                if not file_path.exists():
                    logger.warning(f"Dataset split not found: {file_path}")
                    continue
                with jsonlines.open(str(file_path)) as reader:
                    examples = list(reader)

            # Subsample by weight if needed (weight < 1.0 means reduce, > 1.0 means repeat)
            if weight < 1.0:
                import random
                random.seed(42)
                n = max(1, int(len(examples) * weight))
                examples = random.sample(examples, min(n, len(examples)))
            elif weight > 1.0:
                import math
                repeats = math.floor(weight)
                remainder = weight - repeats
                import random
                random.seed(42)
                expanded = examples * repeats
                n_extra = int(len(examples) * remainder)
                expanded.extend(random.sample(examples, min(n_extra, len(examples))))
                examples = expanded

            logger.info(f"  {ds_name}: {len(examples)} examples (weight={weight})")
            all_examples.extend(examples)

        # Shuffle combined dataset
        import random
        random.seed(42)
        random.shuffle(all_examples)

        logger.info(f"Total {split} examples: {len(all_examples)}")

        # Convert to HuggingFace Dataset
        return Dataset.from_list(all_examples)

    def _load_internal_dataset(self, split: str) -> List[Dict]:
        """Load internal dataset from batch-based ChatML files."""
        internal_dir = self.data_dir.parent / "internal" / "chatml"
        if not internal_dir.exists():
            # Fallback to processed dir
            internal_dir = self.data_dir / "internal"

        examples = []
        if internal_dir.exists():
            import jsonlines
            # Load all batch files
            for batch_file in sorted(internal_dir.glob("batch_*.jsonl")):
                with jsonlines.open(str(batch_file)) as reader:
                    examples.extend(list(reader))

            # Simple split: use 80% train, 10% val, 10% test
            n = len(examples)
            if split == "train":
                examples = examples[:int(n * 0.8)]
            elif split == "validation":
                examples = examples[int(n * 0.8):int(n * 0.9)]
            else:
                examples = examples[int(n * 0.9):]

        if not examples:
            # Fallback: check for train/validation/test.jsonl
            fallback_path = self.data_dir / "internal" / f"{split}.jsonl"
            if fallback_path.exists():
                import jsonlines
                with jsonlines.open(str(fallback_path)) as reader:
                    examples = list(reader)

        return examples


# ---------------------------------------------------------------------------
# Trainer — Template Method pattern
# ---------------------------------------------------------------------------

class QLoRATrainer:
    """
    QLoRA training pipeline.
    Template Method: load_model → configure_lora → prepare_data → train → save
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.peft_model = None

    def run(self, resume: bool = False):
        """Execute the full training pipeline."""
        logger.info(f"Starting QLoRA training for {self.config.model_name}")

        # Step 1: Load model with quantization
        self._load_model()

        # Step 2: Configure LoRA adapters
        self._configure_lora()

        # Step 3: Prepare datasets
        train_dataset, eval_dataset = self._prepare_data()

        # Step 4: Train
        self._train(train_dataset, eval_dataset, resume=resume)

        # Step 5: Save adapter
        self._save_adapter()

        logger.info("✓ Training complete!")

    def _load_model(self):
        """Load base model with 4-bit quantization."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        qconfig = self.config.quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=qconfig.get("load_in_4bit", True),
            bnb_4bit_quant_type=qconfig.get("bnb_4bit_quant_type", "nf4"),
            bnb_4bit_compute_dtype=getattr(torch, qconfig.get("bnb_4bit_compute_dtype", "bfloat16")),
            bnb_4bit_use_double_quant=qconfig.get("bnb_4bit_use_double_quant", True),
        )

        logger.info(f"Loading model: {self.config.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name, trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        self.model.config.use_cache = False  # Required for gradient checkpointing

        logger.info(f"✓ Model loaded: {self.model.get_memory_footprint() / 1e9:.2f} GB")

    def _configure_lora(self):
        """Apply LoRA adapters."""
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

        self.model = prepare_model_for_kbit_training(self.model)

        lora_cfg = self.config.lora
        peft_config = LoraConfig(
            r=lora_cfg.get("r", 64),
            lora_alpha=lora_cfg.get("lora_alpha", 128),
            lora_dropout=lora_cfg.get("lora_dropout", 0.05),
            target_modules=lora_cfg.get("target_modules", ["q_proj", "v_proj"]),
            task_type=lora_cfg.get("task_type", "CAUSAL_LM"),
            bias=lora_cfg.get("bias", "none"),
        )

        self.peft_model = get_peft_model(self.model, peft_config)
        trainable, total = self.peft_model.get_nb_trainable_parameters()
        logger.info(
            f"✓ LoRA configured: {trainable:,} trainable / {total:,} total "
            f"({100 * trainable / total:.2f}%)"
        )
        self._peft_config = peft_config

    def _prepare_data(self):
        """Load and prepare multi-task datasets."""
        data_cfg = self.config.data
        data_dir = Path(data_cfg.get("data_dir", "./data/processed"))

        loader = MultiTaskDataLoader(data_dir, data_cfg.get("datasets", []))
        train_dataset = loader.load_split(data_cfg.get("train_split", "train"))
        eval_dataset = loader.load_split(data_cfg.get("eval_split", "validation"))

        logger.info(f"✓ Data prepared: {len(train_dataset)} train, {len(eval_dataset)} eval")
        return train_dataset, eval_dataset

    def _train(self, train_dataset, eval_dataset, resume: bool = False):
        """Run SFTTrainer."""
        from trl import SFTTrainer, SFTConfig

        t_cfg = self.config.training
        output_dir = t_cfg.get("output_dir", "./outputs/qlora")

        sft_config = SFTConfig(
            output_dir=output_dir,
            num_train_epochs=t_cfg.get("num_train_epochs", 3),
            per_device_train_batch_size=t_cfg.get("per_device_train_batch_size", 4),
            gradient_accumulation_steps=t_cfg.get("gradient_accumulation_steps", 4),
            learning_rate=t_cfg.get("learning_rate", 2e-4),
            lr_scheduler_type=t_cfg.get("lr_scheduler_type", "cosine"),
            warmup_ratio=t_cfg.get("warmup_ratio", 0.03),
            weight_decay=t_cfg.get("weight_decay", 0.01),
            optim=t_cfg.get("optim", "paged_adamw_8bit"),
            bf16=t_cfg.get("bf16", True),
            gradient_checkpointing=t_cfg.get("gradient_checkpointing", True),
            logging_steps=t_cfg.get("logging_steps", 10),
            save_steps=t_cfg.get("save_steps", 200),
            save_total_limit=t_cfg.get("save_total_limit", 3),
            eval_strategy=t_cfg.get("eval_strategy", "steps"),
            eval_steps=t_cfg.get("eval_steps", 200),
            load_best_model_at_end=t_cfg.get("load_best_model_at_end", True),
            metric_for_best_model=t_cfg.get("metric_for_best_model", "eval_loss"),
            report_to=t_cfg.get("report_to", "none"),
            seed=t_cfg.get("seed", 42),
            max_seq_length=self.config.max_seq_length,
        )

        trainer = SFTTrainer(
            model=self.peft_model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            peft_config=self._peft_config,
            tokenizer=self.tokenizer,
            args=sft_config,
        )

        logger.info("Starting training…")
        trainer.train(resume_from_checkpoint=resume if resume else None)
        logger.info("✓ Training finished")

        self._trainer = trainer

    def _save_adapter(self):
        """Save LoRA adapter weights (small — ~100-200MB)."""
        output_dir = self.config.output_dir
        self._trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        logger.info(f"✓ Adapter saved to {output_dir}")

        # Log adapter size
        import os
        total_size = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, fns in os.walk(output_dir)
            for f in fns
        )
        logger.info(f"  Adapter size: {total_size / 1e6:.1f} MB")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Teacher QLoRA Training")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to training YAML config")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint")
    args = parser.parse_args()

    config = TrainingConfig(args.config)
    trainer = QLoRATrainer(config)
    trainer.run(resume=args.resume)


if __name__ == "__main__":
    main()
