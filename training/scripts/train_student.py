"""
Student QLoRA Training Script
Trains Qwen2.5-3B-Instruct with QLoRA.

Reuses the same QLoRATrainer infrastructure from train_teacher.py (DRY).
The only difference is the config file pointing to a smaller model + different datasets.

Usage:
    python -m training.scripts.train_student --config configs/student_qlora.yaml
"""

import argparse

from training.scripts.train_teacher import TrainingConfig, QLoRATrainer
from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Student QLoRA Training")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to student training YAML config")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint")
    args = parser.parse_args()

    config = TrainingConfig(args.config)
    logger.info(f"Student training with model: {config.model_name}")

    trainer = QLoRATrainer(config)
    trainer.run(resume=args.resume)


if __name__ == "__main__":
    main()
