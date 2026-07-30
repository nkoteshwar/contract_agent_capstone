"""
Internal Dataset Generator
Extensible batch-based design for synthetic redline / policy compliance data.

Generates (clause, policy_rule, redline_suggestion, risk_level) tuples by
running a teacher model inference over CUAD clauses against the policy playbook.

Design:
    - Configurable batch ranges (start, generate 500 at a time, resume later)
    - Append mode: each batch is saved as a separate JSONL file
    - Auto-discovers existing batches for dedup

Usage:
    # Generate first 500 examples
    python -m training.scripts.generate_internal_dataset --batch-size 500 --start-index 0

    # Generate next 500 later
    python -m training.scripts.generate_internal_dataset --batch-size 500 --start-index 500

    # Generate from config
    python -m training.scripts.generate_internal_dataset --config configs/internal_dataset.yaml
"""

import argparse
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional

import jsonlines
import yaml
from tqdm import tqdm

from training.scripts.utils import setup_training_logging, get_logger

setup_training_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data models (mirrors Clause dataclass in clause_extraction_agent.py)
# ---------------------------------------------------------------------------

@dataclass
class RedlineExample:
    """Single redline training example."""
    clause_text: str
    policy_rule: str
    risk_level: str
    reasoning: str
    redline_suggestion: str
    source_doc: str = ""
    clause_type: str = ""
    batch_id: int = 0
    index: int = 0


# ---------------------------------------------------------------------------
# Strategy interface for clause source extraction
# ---------------------------------------------------------------------------

class IClauseSource(ABC):
    """Strategy for extracting source clauses — Open/Closed."""

    @abstractmethod
    def extract_clauses(self, start_index: int, count: int) -> List[Dict[str, Any]]:
        """Extract clauses from source data."""
        pass


class CUADClauseSource(IClauseSource):
    """Extract clauses from raw CUAD dataset."""

    def __init__(self, cuad_path: str):
        self.cuad_path = cuad_path

    def extract_clauses(self, start_index: int, count: int) -> List[Dict[str, Any]]:
        from datasets import load_from_disk, load_dataset

        try:
            dataset = load_from_disk(self.cuad_path)
            data = dataset["train"] if "train" in dataset else dataset[list(dataset.keys())[0]]
        except Exception:
            logger.info("Loading CUAD from HuggingFace…")
            dataset = load_dataset("theatticusproject/cuad-qa", trust_remote_code=True)
            data = dataset["train"]

        clauses = []
        # Filter for examples with actual clause answers
        for i, example in enumerate(data):
            if i < start_index:
                continue
            if len(clauses) >= count:
                break

            answers = example.get("answers", {})
            answer_texts = answers.get("text", [])
            if answer_texts and answer_texts[0] and len(answer_texts[0]) > 20:
                question = example.get("question", "")
                clause_type = question.replace(
                    "Highlight the parts (if any) of this contract related to ", ""
                ).rstrip(".")

                clauses.append({
                    "clause_text": answer_texts[0],
                    "clause_type": clause_type,
                    "context": example.get("context", "")[:500],
                    "source_doc": example.get("title", f"cuad_doc_{i}"),
                })

        logger.info(f"Extracted {len(clauses)} clauses (index {start_index}–{start_index + count})")
        return clauses


# ---------------------------------------------------------------------------
# Policy loader
# ---------------------------------------------------------------------------

class PolicyLoader:
    """Load policy rules from playbook. Single Responsibility."""

    # Default policy rules when playbook PDF can't be parsed
    DEFAULT_POLICY_RULES = [
        {
            "rule_id": "POL-001",
            "rule_text": "All contracts must include a liability cap no greater than 2x the contract value.",
            "rule_type": "mandatory",
            "severity": "HIGH",
            "applies_to": ["Cap On Liability", "Uncapped Liability"],
        },
        {
            "rule_id": "POL-002",
            "rule_text": "Termination for convenience requires a minimum 90-day written notice period.",
            "rule_type": "mandatory",
            "severity": "MEDIUM",
            "applies_to": ["Termination For Convenience"],
        },
        {
            "rule_id": "POL-003",
            "rule_text": "Non-compete clauses must be limited to 12 months and a reasonable geographic scope.",
            "rule_type": "mandatory",
            "severity": "HIGH",
            "applies_to": ["Non-Compete"],
        },
        {
            "rule_id": "POL-004",
            "rule_text": "All IP created during the contract belongs to the contracting party unless explicitly assigned.",
            "rule_type": "mandatory",
            "severity": "HIGH",
            "applies_to": ["Ip Ownership Assignment", "Joint Ip Ownership"],
        },
        {
            "rule_id": "POL-005",
            "rule_text": "Governing law must be specified and should preferably be the company's home jurisdiction.",
            "rule_type": "mandatory",
            "severity": "MEDIUM",
            "applies_to": ["Governing Law"],
        },
        {
            "rule_id": "POL-006",
            "rule_text": "Exclusivity clauses are prohibited unless approved by the legal committee.",
            "rule_type": "prohibited",
            "severity": "HIGH",
            "applies_to": ["Exclusivity"],
        },
        {
            "rule_id": "POL-007",
            "rule_text": "Insurance coverage must meet minimum thresholds: $1M general liability, $5M professional liability.",
            "rule_type": "mandatory",
            "severity": "MEDIUM",
            "applies_to": ["Insurance"],
        },
        {
            "rule_id": "POL-008",
            "rule_text": "Change of control provisions must allow either party to terminate within 30 days of a change event.",
            "rule_type": "mandatory",
            "severity": "MEDIUM",
            "applies_to": ["Change Of Control"],
        },
        {
            "rule_id": "POL-009",
            "rule_text": "Audit rights must be included for contracts exceeding $500K annual value.",
            "rule_type": "mandatory",
            "severity": "MEDIUM",
            "applies_to": ["Audit Rights"],
        },
        {
            "rule_id": "POL-010",
            "rule_text": "Warranties must have a minimum duration of 12 months from delivery.",
            "rule_type": "mandatory",
            "severity": "LOW",
            "applies_to": ["Warranty Duration"],
        },
    ]

    def __init__(self, playbook_path: Optional[str] = None):
        self.playbook_path = playbook_path

    def load_rules(self) -> List[Dict[str, Any]]:
        """Load policy rules. Falls back to defaults if playbook unavailable."""
        # Could be extended to parse PDF playbook
        logger.info(f"Loaded {len(self.DEFAULT_POLICY_RULES)} policy rules")
        return self.DEFAULT_POLICY_RULES

    def get_matching_rule(self, clause_type: str) -> Optional[Dict[str, Any]]:
        """Find the most relevant policy rule for a clause type."""
        rules = self.load_rules()
        for rule in rules:
            if clause_type in rule.get("applies_to", []):
                return rule
        # Return a generic rule for unmatched types
        return {
            "rule_id": "POL-GEN",
            "rule_text": "All contract clauses must use clear, unambiguous language and comply with company standards.",
            "rule_type": "general",
            "severity": "LOW",
            "applies_to": ["general"],
        }


# ---------------------------------------------------------------------------
# Teacher inference engine
# ---------------------------------------------------------------------------

class IRedlineGenerator(ABC):
    """Strategy for generating redline suggestions."""

    @abstractmethod
    def generate(self, clause_text: str, policy_rule: str) -> Dict[str, Any]:
        pass


class LLMRedlineGenerator(IRedlineGenerator):
    """Generate redlines using the Teacher model (for RunPod execution)."""

    def __init__(self, model_name: str, max_new_tokens: int = 512, temperature: float = 0.3):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """Lazy load model — only when first needed."""
        if self._model is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        logger.info(f"Loading model {self.model_name}…")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
        )

    def generate(self, clause_text: str, policy_rule: str) -> Dict[str, Any]:
        self._load_model()

        messages = [
            {"role": "system", "content": (
                "You are a legal contract analyst. Given a contract clause and a policy rule, "
                "analyze the clause for compliance and generate a redline suggestion if needed. "
                "Respond ONLY with valid JSON: {\"risk_level\": \"LOW|MEDIUM|HIGH\", "
                "\"reasoning\": \"...\", \"redline_suggestion\": \"...\"}"
            )},
            {"role": "user", "content": (
                f"## Contract Clause\n{clause_text}\n\n"
                f"## Policy Rule\n{policy_rule}"
            )},
        ]

        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)

        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=True,
        )

        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response with fallback."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]+\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback: parse structured text
        return {
            "risk_level": "MEDIUM",
            "reasoning": response[:500],
            "redline_suggestion": "Review required — could not parse structured response.",
        }


class TemplateRedlineGenerator(IRedlineGenerator):
    """
    Template-based generator for offline / CPU-only environments.
    Uses rule matching instead of LLM inference (for local testing).
    """

    def generate(self, clause_text: str, policy_rule: str) -> Dict[str, Any]:
        clause_lower = clause_text.lower()

        # Simple heuristic risk assessment
        high_risk_keywords = ["unlimited liability", "irrevocable", "perpetual", "exclusive"]
        medium_risk_keywords = ["terminate", "assign", "change of control", "non-compete"]

        if any(kw in clause_lower for kw in high_risk_keywords):
            risk = "HIGH"
        elif any(kw in clause_lower for kw in medium_risk_keywords):
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "risk_level": risk,
            "reasoning": f"Clause assessed against policy: {policy_rule[:200]}",
            "redline_suggestion": "No changes needed." if risk == "LOW" else
                                  f"Review clause for compliance with: {policy_rule[:200]}",
        }


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class InternalDatasetPipeline:
    """
    Orchestrates internal dataset generation with batch support.
    Template Method: extract_clauses → match_policies → generate_redlines → save
    """

    def __init__(
        self,
        clause_source: IClauseSource,
        policy_loader: PolicyLoader,
        redline_generator: IRedlineGenerator,
        output_dir: Path,
    ):
        self.clause_source = clause_source
        self.policy_loader = policy_loader
        self.redline_generator = redline_generator
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_batch(self, start_index: int, batch_size: int) -> Dict[str, Any]:
        """Generate a single batch of redline examples."""
        batch_num = (start_index // batch_size) + 1
        logger.info(f"Generating batch {batch_num} (index {start_index}–{start_index + batch_size})…")

        # 1. Extract clauses
        clauses = self.clause_source.extract_clauses(start_index, batch_size)
        if not clauses:
            logger.warning("No clauses extracted. Check source data.")
            return {"batch": batch_num, "status": "empty", "count": 0}

        # 2. Generate redlines
        examples = []
        for i, clause in enumerate(tqdm(clauses, desc=f"Batch {batch_num}")):
            policy_rule = self.policy_loader.get_matching_rule(clause.get("clause_type", ""))
            result = self.redline_generator.generate(
                clause["clause_text"], policy_rule["rule_text"]
            )

            example = RedlineExample(
                clause_text=clause["clause_text"],
                policy_rule=policy_rule["rule_text"],
                risk_level=result.get("risk_level", "MEDIUM"),
                reasoning=result.get("reasoning", ""),
                redline_suggestion=result.get("redline_suggestion", ""),
                source_doc=clause.get("source_doc", ""),
                clause_type=clause.get("clause_type", ""),
                batch_id=batch_num,
                index=start_index + i,
            )
            examples.append(example)

        # 3. Save batch
        batch_file = self.output_dir / f"batch_{batch_num:03d}.jsonl"
        with jsonlines.open(str(batch_file), mode="w") as writer:
            writer.write_all([asdict(e) for e in examples])

        logger.info(f"✓ Batch {batch_num}: {len(examples)} examples → {batch_file}")

        # 4. Also save as ChatML for direct training use
        self._save_chatml(examples, batch_num)

        return {"batch": batch_num, "status": "success", "count": len(examples),
                "path": str(batch_file)}

    def _save_chatml(self, examples: List[RedlineExample], batch_num: int):
        """Convert to ChatML and save for training."""
        from training.scripts.format_datasets import ChatMLBuilder

        chatml_dir = self.output_dir / "chatml"
        chatml_dir.mkdir(parents=True, exist_ok=True)

        chatml_file = chatml_dir / f"batch_{batch_num:03d}.jsonl"
        chatml_examples = []

        for ex in examples:
            messages = ChatMLBuilder.build_messages(
                system=(
                    "You are a legal redline assistant. Given a contract clause and a "
                    "policy rule, assess compliance and suggest revisions if needed."
                ),
                user=(
                    f"## Contract Clause\n{ex.clause_text}\n\n"
                    f"## Policy Rule\n{ex.policy_rule}\n\n"
                    f"Analyze compliance and provide: risk level, reasoning, and redline suggestion."
                ),
                assistant=(
                    f"Risk Level: {ex.risk_level}\n"
                    f"Reasoning: {ex.reasoning}\n"
                    f"Redline Suggestion: {ex.redline_suggestion}"
                ),
            )
            chatml_examples.append({
                "messages": messages,
                "task": "redline_generation",
                "source": "internal",
            })

        with jsonlines.open(str(chatml_file), mode="w") as writer:
            writer.write_all(chatml_examples)

        logger.info(f"  ChatML saved: {chatml_file}")

    def merge_all_batches(self) -> Path:
        """Merge all batch files into a single training file with splits."""
        all_examples = []

        batch_files = sorted(self.output_dir.glob("batch_*.jsonl"))
        for bf in batch_files:
            with jsonlines.open(str(bf)) as reader:
                all_examples.extend(list(reader))

        logger.info(f"Merged {len(all_examples)} examples from {len(batch_files)} batches")

        # Save merged
        merged_path = self.output_dir / "merged.jsonl"
        with jsonlines.open(str(merged_path), mode="w") as writer:
            writer.write_all(all_examples)

        return merged_path

    def get_stats(self) -> Dict[str, Any]:
        """Get current dataset statistics."""
        batch_files = sorted(self.output_dir.glob("batch_*.jsonl"))
        total = 0
        batches = []
        for bf in batch_files:
            with jsonlines.open(str(bf)) as reader:
                count = sum(1 for _ in reader)
            total += count
            batches.append({"file": bf.name, "count": count})

        return {"total_examples": total, "num_batches": len(batches), "batches": batches}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate internal redline dataset")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to internal_dataset.yaml config")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--output-dir", type=str, default="./data/internal")
    parser.add_argument("--cuad-path", type=str, default="./data/raw/cuad",
                        help="Path to downloaded CUAD dataset")
    parser.add_argument("--use-llm", action="store_true",
                        help="Use LLM for generation (requires GPU)")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-7B-Instruct",
                        help="Teacher model for LLM generation")
    parser.add_argument("--merge", action="store_true",
                        help="Merge all existing batches into one file")
    parser.add_argument("--stats", action="store_true",
                        help="Show current dataset statistics")
    args = parser.parse_args()

    # Load config if provided
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)
        batch_size = config.get("generation", {}).get("batch_size", args.batch_size)
        start_index = config.get("generation", {}).get("start_index", args.start_index)
        output_dir = Path(config.get("generation", {}).get("output_dir", args.output_dir))
        model_name = config.get("model", {}).get("name", args.model)
    else:
        batch_size = args.batch_size
        start_index = args.start_index
        output_dir = Path(args.output_dir)
        model_name = args.model

    # Create components
    clause_source = CUADClauseSource(args.cuad_path)
    policy_loader = PolicyLoader()

    if args.use_llm:
        redline_generator = LLMRedlineGenerator(model_name)
    else:
        redline_generator = TemplateRedlineGenerator()

    pipeline = InternalDatasetPipeline(
        clause_source=clause_source,
        policy_loader=policy_loader,
        redline_generator=redline_generator,
        output_dir=output_dir,
    )

    if args.stats:
        stats = pipeline.get_stats()
        logger.info(json.dumps(stats, indent=2))
        return

    if args.merge:
        merged = pipeline.merge_all_batches()
        logger.info(f"Merged file: {merged}")
        return

    result = pipeline.generate_batch(start_index, batch_size)
    logger.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
