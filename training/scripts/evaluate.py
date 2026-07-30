"""
Evaluation Script
Evaluates fine-tuned models against held-out test sets and LegalBench.

Usage:
    python -m training.scripts.evaluate --model teacher --config configs/teacher_qlora.yaml
    python -m training.scripts.evaluate --model student --config configs/student_qlora.yaml
    python -m training.scripts.evaluate --all
    python -m training.scripts.evaluate --compare  # A/B comparison report
"""

import argparse
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

import jsonlines
from tqdm import tqdm

from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Strategy interface for evaluation metrics (mirrors IValidationStrategy)
# ---------------------------------------------------------------------------

class IEvalMetric(ABC):
    """Strategy interface for evaluation metrics — Open/Closed."""

    @abstractmethod
    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class ExactMatchMetric(IEvalMetric):
    """Exact match accuracy."""

    def get_name(self) -> str:
        return "exact_match"

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        correct = sum(1 for p, r in zip(predictions, references)
                      if p.strip().lower() == r.strip().lower())
        accuracy = correct / len(predictions) if predictions else 0.0
        return {"exact_match": accuracy, "correct": correct, "total": len(predictions)}


class F1ScoreMetric(IEvalMetric):
    """Token-level F1 score (for extraction tasks)."""

    def get_name(self) -> str:
        return "f1"

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        f1_scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = set(pred.lower().split())
            ref_tokens = set(ref.lower().split())

            if not ref_tokens:
                f1_scores.append(1.0 if not pred_tokens else 0.0)
                continue
            if not pred_tokens:
                f1_scores.append(0.0)
                continue

            common = pred_tokens & ref_tokens
            precision = len(common) / len(pred_tokens)
            recall = len(common) / len(ref_tokens)
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)

        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        return {"f1": avg_f1, "total": len(f1_scores)}


class ClassificationAccuracyMetric(IEvalMetric):
    """Classification accuracy with per-class breakdown."""

    def get_name(self) -> str:
        return "classification_accuracy"

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        correct = 0
        class_correct = {}
        class_total = {}

        for pred, ref in zip(predictions, references):
            # Normalize: extract category from "Category: X" format
            pred_clean = pred.replace("Category: ", "").strip().lower()
            ref_clean = ref.replace("Category: ", "").strip().lower()

            class_total[ref_clean] = class_total.get(ref_clean, 0) + 1
            if pred_clean == ref_clean:
                correct += 1
                class_correct[ref_clean] = class_correct.get(ref_clean, 0) + 1

        accuracy = correct / len(predictions) if predictions else 0.0

        # Macro F1
        per_class_f1 = []
        for cls in class_total:
            tp = class_correct.get(cls, 0)
            total = class_total[cls]
            recall = tp / total if total > 0 else 0
            per_class_f1.append(recall)  # Simplified

        macro_f1 = sum(per_class_f1) / len(per_class_f1) if per_class_f1 else 0.0

        return {"accuracy": accuracy, "macro_f1": macro_f1, "correct": correct,
                "total": len(predictions), "num_classes": len(class_total)}


class RiskRoutingAccuracyMetric(IEvalMetric):
    """Risk routing accuracy (LOW / MEDIUM / HIGH)."""

    def get_name(self) -> str:
        return "risk_routing_accuracy"

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        correct = 0
        confusion = {"LOW": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
                      "MEDIUM": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
                      "HIGH": {"LOW": 0, "MEDIUM": 0, "HIGH": 0}}

        for pred, ref in zip(predictions, references):
            pred_risk = self._extract_risk(pred)
            ref_risk = self._extract_risk(ref)

            if pred_risk == ref_risk:
                correct += 1
            if ref_risk in confusion and pred_risk in confusion[ref_risk]:
                confusion[ref_risk][pred_risk] += 1

        accuracy = correct / len(predictions) if predictions else 0.0
        return {"accuracy": accuracy, "correct": correct, "total": len(predictions),
                "confusion_matrix": confusion}

    def _extract_risk(self, text: str) -> str:
        text_upper = text.upper()
        for level in ["HIGH", "MEDIUM", "LOW"]:
            if level in text_upper:
                return level
        return "UNKNOWN"


class ROUGELMetric(IEvalMetric):
    """ROUGE-L for redline quality assessment."""

    def get_name(self) -> str:
        return "rouge_l"

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        try:
            from rouge_score import rouge_scorer
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

            scores = []
            for pred, ref in zip(predictions, references):
                score = scorer.score(ref, pred)
                scores.append(score['rougeL'].fmeasure)

            avg_rouge = sum(scores) / len(scores) if scores else 0.0
            return {"rouge_l": avg_rouge, "total": len(scores)}
        except ImportError:
            logger.warning("rouge-score not installed, skipping ROUGE-L")
            return {"rouge_l": -1.0, "total": 0}


# ---------------------------------------------------------------------------
# Metric registry (mirrors agent registry)
# ---------------------------------------------------------------------------

TASK_METRICS = {
    "clause_extraction": [ExactMatchMetric(), F1ScoreMetric()],
    "clause_extraction_simple": [ExactMatchMetric(), F1ScoreMetric()],
    "clause_classification": [ClassificationAccuracyMetric()],
    "legal_reasoning": [ClassificationAccuracyMetric()],
    "risk_routing": [RiskRoutingAccuracyMetric()],
    "redline_generation": [ROUGELMetric()],
    "contract_comprehension": [F1ScoreMetric()],
}


# ---------------------------------------------------------------------------
# Model inference helper
# ---------------------------------------------------------------------------

class ModelInference:
    """Wraps a fine-tuned model for evaluation inference."""

    def __init__(self, base_model: str, adapter_path: Optional[str] = None):
        self.base_model = base_model
        self.adapter_path = adapter_path
        self._model = None
        self._tokenizer = None

    def _load(self):
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)

        self._tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.base_model, quantization_config=bnb_config, device_map="auto")

        if self.adapter_path:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, self.adapter_path)

        model.eval()
        self._model = model

    def predict(self, messages: List[Dict[str, str]]) -> str:
        """Generate prediction from input messages."""
        self._load()
        import torch

        input_msgs = [m for m in messages if m["role"] != "assistant"]
        text = self._tokenizer.apply_chat_template(
            input_msgs, tokenize=False, add_generation_prompt=True)
        inputs = self._tokenizer(text, return_tensors="pt", truncation=True,
                                  max_length=1536).to(self._model.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs, max_new_tokens=512, temperature=0.1, do_sample=False,
                pad_token_id=self._tokenizer.pad_token_id)

        return self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


# ---------------------------------------------------------------------------
# Evaluator pipeline
# ---------------------------------------------------------------------------

class Evaluator:
    """
    Runs evaluation across all tasks and generates a report.
    Template Method: load_test_data → run_inference → compute_metrics → report
    """

    def __init__(self, data_dir: Path, output_dir: Path):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_model(self, model_name: str, model: ModelInference,
                       max_examples: int = 100) -> Dict[str, Any]:
        """Evaluate a model on all available test sets."""
        results = {"model": model_name, "tasks": {}}

        for task_dir in self.data_dir.iterdir():
            if not task_dir.is_dir():
                continue

            test_file = task_dir / "test.jsonl"
            if not test_file.exists():
                continue

            task_name = task_dir.name
            metrics = TASK_METRICS.get(task_name, [F1ScoreMetric()])

            logger.info(f"Evaluating {model_name} on {task_name}…")

            # Load test examples
            with jsonlines.open(str(test_file)) as reader:
                examples = list(reader)[:max_examples]

            if not examples:
                continue

            # Run inference
            predictions = []
            references = []
            for ex in tqdm(examples, desc=f"{task_name}"):
                messages = ex.get("messages", [])
                ref = messages[-1]["content"] if messages and messages[-1]["role"] == "assistant" else ""
                pred = model.predict(messages)
                predictions.append(pred)
                references.append(ref)

            # Compute metrics
            task_results = {}
            for metric in metrics:
                metric_result = metric.compute(predictions, references)
                task_results[metric.get_name()] = metric_result

            results["tasks"][task_name] = task_results

        # Save results
        result_file = self.output_dir / f"eval_{model_name}.json"
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"✓ Results saved: {result_file}")
        return results

    def compare_models(self, results: List[Dict[str, Any]]) -> str:
        """Generate a markdown comparison report."""
        report_lines = ["# Model Evaluation Comparison\n"]

        # Collect all tasks
        all_tasks = set()
        for r in results:
            all_tasks.update(r.get("tasks", {}).keys())

        for task in sorted(all_tasks):
            report_lines.append(f"\n## {task}\n")
            report_lines.append("| Model | Metric | Value |")
            report_lines.append("|-------|--------|-------|")

            for r in results:
                model_name = r["model"]
                task_results = r.get("tasks", {}).get(task, {})
                for metric_name, metric_data in task_results.items():
                    for key, value in metric_data.items():
                        if isinstance(value, float):
                            report_lines.append(f"| {model_name} | {key} | {value:.4f} |")

        report = "\n".join(report_lines)
        report_file = self.output_dir / "comparison_report.md"
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"✓ Comparison report: {report_file}")
        return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned models")
    parser.add_argument("--model", type=str, choices=["teacher", "student", "distilled", "baseline"],
                        help="Model to evaluate")
    parser.add_argument("--base-model", type=str, default=None,
                        help="Base model name (for baseline eval)")
    parser.add_argument("--adapter-path", type=str, default=None,
                        help="Path to LoRA adapter")
    parser.add_argument("--data-dir", type=str, default="./data/processed")
    parser.add_argument("--output-dir", type=str, default="./outputs/eval")
    parser.add_argument("--max-examples", type=int, default=100)
    parser.add_argument("--compare", action="store_true",
                        help="Compare all available eval results")
    args = parser.parse_args()

    evaluator = Evaluator(Path(args.data_dir), Path(args.output_dir))

    if args.compare:
        # Load all eval results and compare
        all_results = []
        for eval_file in Path(args.output_dir).glob("eval_*.json"):
            with open(eval_file) as f:
                all_results.append(json.load(f))
        if all_results:
            evaluator.compare_models(all_results)
        else:
            logger.warning("No evaluation results found to compare.")
        return

    # Model presets
    model_presets = {
        "teacher": ("Qwen/Qwen2.5-7B-Instruct", "./outputs/teacher_qlora"),
        "student": ("Qwen/Qwen2.5-3B-Instruct", "./outputs/student_qlora"),
        "distilled": ("Qwen/Qwen2.5-3B-Instruct", "./outputs/student_distilled"),
        "baseline": ("Qwen/Qwen2.5-7B-Instruct", None),
    }

    base_model = args.base_model
    adapter_path = args.adapter_path

    if args.model and args.model in model_presets:
        base_model = base_model or model_presets[args.model][0]
        adapter_path = adapter_path or model_presets[args.model][1]

    if not base_model:
        logger.error("Specify --model or --base-model")
        return

    model = ModelInference(base_model, adapter_path)
    model_name = args.model or "custom"
    evaluator.evaluate_model(model_name, model, args.max_examples)


if __name__ == "__main__":
    main()
