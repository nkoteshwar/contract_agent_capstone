"""
Dataset Format Conversion Pipeline
Strategy Pattern — each dataset has its own formatter strategy that converts
raw HuggingFace data into Qwen2.5 ChatML format.

Reuses the Strategy pattern from clause_extraction_agent.py and the
Template Method from cuad_classifier_agent.py.

Usage:
    python -m training.scripts.format_datasets
    python -m training.scripts.format_datasets --datasets cuad ledgar
"""

import argparse
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import jsonlines
from datasets import load_from_disk, Dataset
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from training.scripts.utils import setup_training_logging, get_logger, Registry

setup_training_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# ChatML builder — DRY: single place to build Qwen2.5 chat format
# ---------------------------------------------------------------------------

class ChatMLBuilder:
    """
    Builds Qwen2.5 ChatML-formatted conversation strings.
    Single Responsibility: only handles format conversion.
    """

    @staticmethod
    def build(system: str, user: str, assistant: str) -> str:
        return (
            f"<|im_start|>system\n{system.strip()}<|im_end|>\n"
            f"<|im_start|>user\n{user.strip()}<|im_end|>\n"
            f"<|im_start|>assistant\n{assistant.strip()}<|im_end|>"
        )

    @staticmethod
    def build_messages(system: str, user: str, assistant: str) -> List[Dict[str, str]]:
        """Return as message list (for TRL SFTTrainer)."""
        return [
            {"role": "system", "content": system.strip()},
            {"role": "user", "content": user.strip()},
            {"role": "assistant", "content": assistant.strip()},
        ]


# ---------------------------------------------------------------------------
# Strategy interface for dataset formatting
# ---------------------------------------------------------------------------

class IDatasetFormatter(ABC):
    """Strategy interface — mirrors IClauseExtractionStrategy."""

    @abstractmethod
    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single raw example into ChatML format. Return None to skip."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Task-specific system prompt."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Concrete formatters — one per dataset (Open/Closed)
# ---------------------------------------------------------------------------

class CUADFormatter(IDatasetFormatter):
    """Format CUAD for clause extraction (SQuAD-style → ChatML)."""

    def get_name(self) -> str:
        return "cuad"

    def get_system_prompt(self) -> str:
        return (
            "You are a legal contract analyst specializing in clause extraction. "
            "Given a contract passage and a question about a specific clause type, "
            "extract the exact text span from the passage that answers the question. "
            "If the clause is not present, respond with 'Not found in this passage.'"
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        context = example.get("context", "")
        question = example.get("question", "")
        answers = example.get("answers", {})

        if not context or not question:
            return None

        # Extract answer text
        answer_texts = answers.get("text", [])
        if answer_texts and answer_texts[0]:
            assistant_response = answer_texts[0]
        else:
            assistant_response = "Not found in this passage."

        # Skip very short contexts
        if len(context) < 50:
            return None

        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"## Contract Passage\n{context[:2000]}\n\n## Question\n{question}",
            assistant=assistant_response
        )
        return {"messages": messages, "task": "clause_extraction", "source": "cuad"}


class CUADSimpleFormatter(IDatasetFormatter):
    """Simplified CUAD for Student — only straightforward extractions."""

    def get_name(self) -> str:
        return "cuad_simple"

    def get_system_prompt(self) -> str:
        return (
            "You are a contract clause identifier. Given a contract passage and a "
            "clause type question, extract the relevant text span. "
            "If not found, respond with 'Not found.'"
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        context = example.get("context", "")
        question = example.get("question", "")
        answers = example.get("answers", {})

        answer_texts = answers.get("text", [])
        if not answer_texts or not answer_texts[0]:
            return None  # Student only trains on found clauses

        if len(context) < 50 or len(answer_texts[0]) < 10:
            return None

        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"Passage:\n{context[:1500]}\n\nClause type: {question}",
            assistant=answer_texts[0]
        )
        return {"messages": messages, "task": "clause_extraction_simple", "source": "cuad"}


class LEDGARFormatter(IDatasetFormatter):
    """Format LEDGAR for clause classification."""

    # LEDGAR label map from lex_glue
    LABEL_NAMES = [
        "Adjustments", "Agreements", "Amendments", "Anti-Corruption Laws",
        "Applicable Laws", "Approvals", "Arbitration", "Assignments",
        "Audits", "Base Coverage and Limits", "Benefits",
        "Binding Effects", "Books", "Brokers", "Capitalization",
        "Change In Control", "Closings", "Compliance With Laws",
        "Conditions", "Confidentiality", "Consent To Jurisdiction",
        "Consequences", "Cooperation", "Costs", "Counterparts",
        "Death", "Decrement Table", "Defined Terms", "Definitions",
        "Disability", "Disclosures", "Dividends", "Effectiveness",
        "Employees", "Enforceability", "Entire Agreements",
        "Erisa", "Escrow", "Events", "Fees", "Financial Statements",
        "Forfeitures", "Further Assurances", "General", "Governing Laws",
        "Guarantees", "Headings", "Holders", "Indemnifications",
        "Insurances", "Integration", "Intellectual Property",
        "Interests", "Interpretations", "Jurisdictions", "Liens",
        "Limitations Of Liability", "Loans", "Mergers",
        "Miscellaneous", "Modifications", "No Conflicts",
        "No Defaults", "No Waivers", "Non-Disparagement",
        "Notices", "Organizations", "Participations", "Payments",
        "Penalties", "Powers", "Procedures", "Qualifications",
        "Receivables", "Records", "Redemptions", "Registration",
        "Releases", "Remedies", "Rent", "Reorganizations",
        "Representations", "Resignations", "Restrictions",
        "Returns", "Rights", "Sanctions", "Severability",
        "Solvency", "Expenses", "Subrogation", "Successors",
        "Survival", "Taxes", "Terminations", "Terms",
        "Titles", "Transactions With Affiliates", "Use Of Proceeds",
        "Vesting", "Waivers", "Warranties"
    ]

    def get_name(self) -> str:
        return "ledgar"

    def get_system_prompt(self) -> str:
        return (
            "You are a legal provision classifier. Classify the given contract "
            "provision into its correct legal category. Respond with only the "
            "category name."
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        text = example.get("text", "")
        label = example.get("label", -1)

        if not text or len(text) < 20 or label < 0 or label >= len(self.LABEL_NAMES):
            return None

        label_name = self.LABEL_NAMES[label]
        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"Classify this contract provision:\n\n{text[:1500]}",
            assistant=f"Category: {label_name}"
        )
        return {"messages": messages, "task": "clause_classification", "source": "ledgar"}


class ContractNLIFormatter(IDatasetFormatter):
    """Format ContractNLI for legal reasoning / entailment."""

    LABEL_MAP = {0: "Entailment", 1: "Contradiction", 2: "Not Mentioned"}

    def get_name(self) -> str:
        return "contract_nli"

    def get_system_prompt(self) -> str:
        return (
            "You are a legal reasoning expert. Given a contract clause (premise) and "
            "a legal hypothesis, determine whether the clause entails the hypothesis, "
            "contradicts it, or does not mention the topic. Provide your reasoning and "
            "cite specific evidence from the clause."
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        premise = example.get("premise", "")
        hypothesis = example.get("hypothesis", "")
        label = example.get("label", -1)

        if not premise or not hypothesis or label not in self.LABEL_MAP:
            return None

        label_name = self.LABEL_MAP[label]

        # Build reasoning response
        spans = example.get("spans", [])
        evidence = "; ".join(spans[:3]) if spans else "No specific span identified."
        assistant_text = (
            f"Determination: {label_name}\n"
            f"Evidence: {evidence}\n"
            f"Reasoning: The clause {'supports' if label == 0 else 'contradicts' if label == 1 else 'does not address'} "
            f"the hypothesis based on the identified evidence spans."
        )

        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"## Clause (Premise)\n{premise[:2000]}\n\n## Hypothesis\n{hypothesis}",
            assistant=assistant_text
        )
        return {"messages": messages, "task": "legal_reasoning", "source": "contract_nli"}


class MAUDFormatter(IDatasetFormatter):
    """Format MAUD for advanced contract comprehension."""

    def get_name(self) -> str:
        return "maud"

    def get_system_prompt(self) -> str:
        return (
            "You are an expert M&A contract analyst. Given a contract passage and a "
            "question about merger agreement terms, provide a detailed analysis with "
            "your reasoning."
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # MAUD format: context, question, answer, category
        context = example.get("text", example.get("context", ""))
        question = example.get("question", "")
        answer = example.get("answer", "")

        if not context or not question or not answer:
            return None

        if len(context) < 50:
            return None

        category = example.get("category", "general")
        assistant_text = f"Answer: {answer}\nCategory: {category}"

        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"## M&A Contract Section\n{context[:2000]}\n\n## Question\n{question}",
            assistant=assistant_text
        )
        return {"messages": messages, "task": "contract_comprehension", "source": "maud"}


class RiskRoutingFormatter(IDatasetFormatter):
    """
    Generate risk-routing labels from CUAD annotations.
    Maps clause characteristics to LOW / MEDIUM / HIGH risk.
    """

    HIGH_RISK_TYPES = {
        "Uncapped Liability", "Ip Ownership Assignment", "Non-Compete",
        "Change Of Control", "Liquidated Damages", "Covenant Not To Sue"
    }
    MEDIUM_RISK_TYPES = {
        "Termination For Convenience", "Anti-Assignment", "Exclusivity",
        "Revenue/Customer Sharing", "Cap On Liability", "Audit Rights"
    }

    def get_name(self) -> str:
        return "risk_routing"

    def get_system_prompt(self) -> str:
        return (
            "You are a contract risk router. Given a contract clause, determine its "
            "risk level: LOW, MEDIUM, or HIGH. LOW-risk clauses are standard "
            "boilerplate. MEDIUM-risk clauses need careful review. HIGH-risk clauses "
            "require legal expert escalation."
        )

    def format_example(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        context = example.get("context", "")
        question = example.get("question", "")
        answers = example.get("answers", {})

        if not context or not question:
            return None

        answer_texts = answers.get("text", [])
        has_clause = bool(answer_texts and answer_texts[0])

        # Determine risk from CUAD clause type
        clause_type = question.replace("Highlight the parts (if any) of this contract related to ", "").rstrip(".")
        if clause_type in self.HIGH_RISK_TYPES:
            risk = "HIGH"
        elif clause_type in self.MEDIUM_RISK_TYPES:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if not has_clause:
            risk = "LOW"  # Missing clause = no active risk

        messages = ChatMLBuilder.build_messages(
            system=self.get_system_prompt(),
            user=f"Assess the risk level of this contract passage:\n\n{context[:1500]}",
            assistant=f"Risk Level: {risk}\nClause Type: {clause_type}\nClause Present: {'Yes' if has_clause else 'No'}"
        )
        return {"messages": messages, "task": "risk_routing", "source": "cuad"}


# ---------------------------------------------------------------------------
# Formatter registry (uses generic Registry from utils — DRY)
# ---------------------------------------------------------------------------

def create_default_formatter_registry() -> Registry[IDatasetFormatter]:
    registry = Registry[IDatasetFormatter]()
    registry.register("cuad", CUADFormatter())
    registry.register("cuad_simple", CUADSimpleFormatter())
    registry.register("ledgar", LEDGARFormatter())
    registry.register("contract_nli", ContractNLIFormatter())
    registry.register("maud", MAUDFormatter())
    registry.register("risk_routing", RiskRoutingFormatter())
    return registry


# ---------------------------------------------------------------------------
# Format pipeline — Template Method pattern
# ---------------------------------------------------------------------------

class FormatPipeline:
    """
    Orchestrates dataset formatting with train/val/test splitting.
    Template Method: load → format → filter → split → save.
    """

    def __init__(self, raw_dir: Path, output_dir: Path, registry: Registry[IDatasetFormatter]):
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.registry = registry

    def process_dataset(self, dataset_name: str, formatter_name: Optional[str] = None,
                        max_examples: Optional[int] = None) -> Dict[str, Any]:
        """Process a single dataset through the format pipeline."""
        fmt_name = formatter_name or dataset_name
        formatter = self.registry.get(fmt_name)
        if not formatter:
            logger.error(f"No formatter registered for: {fmt_name}")
            return {"name": fmt_name, "status": "error", "error": "Unknown formatter"}

        # Load raw dataset
        raw_path = self.raw_dir / dataset_name
        if not raw_path.exists():
            # For derived datasets (cuad_simple, risk_routing), use source dataset
            source_map = {"cuad_simple": "cuad", "risk_routing": "cuad"}
            source_name = source_map.get(dataset_name, dataset_name)
            raw_path = self.raw_dir / source_name
            if not raw_path.exists():
                logger.error(f"Raw dataset not found: {raw_path}")
                return {"name": fmt_name, "status": "error", "error": f"Not found: {raw_path}"}

        logger.info(f"Loading raw dataset from {raw_path}…")
        raw_dataset = load_from_disk(str(raw_path))

        # Format all examples
        formatted = []
        split_to_use = "train" if "train" in raw_dataset else list(raw_dataset.keys())[0]
        data_split = raw_dataset[split_to_use]

        for example in tqdm(data_split, desc=f"Formatting {fmt_name}"):
            result = formatter.format_example(example)
            if result:
                formatted.append(result)
            if max_examples and len(formatted) >= max_examples:
                break

        if not formatted:
            logger.warning(f"No valid examples formatted for {fmt_name}")
            return {"name": fmt_name, "status": "empty", "count": 0}

        # Split: 80/10/10
        train_data, temp_data = train_test_split(formatted, test_size=0.2, random_state=42)
        val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

        # Save as JSONL
        out_path = self.output_dir / fmt_name
        out_path.mkdir(parents=True, exist_ok=True)

        for split_name, split_data in [("train", train_data), ("validation", val_data), ("test", test_data)]:
            file_path = out_path / f"{split_name}.jsonl"
            with jsonlines.open(str(file_path), mode="w") as writer:
                writer.write_all(split_data)
            logger.info(f"  {split_name}: {len(split_data)} examples → {file_path}")

        return {
            "name": fmt_name,
            "status": "success",
            "train": len(train_data),
            "validation": len(val_data),
            "test": len(test_data),
            "total": len(formatted),
        }

    def process_all(self, dataset_names: Optional[List[str]] = None,
                    max_examples: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process all (or specified) datasets."""
        names = dataset_names or self.registry.list_all()
        results = []
        for name in names:
            result = self.process_dataset(name, max_examples=max_examples)
            results.append(result)

        # Save manifest
        manifest_path = self.output_dir / "format_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=2)
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Format datasets to ChatML")
    parser.add_argument("--datasets", nargs="+", default=None,
                        help="Specific datasets to format")
    parser.add_argument("--raw-dir", type=str, default="./data/raw",
                        help="Directory with raw downloaded datasets")
    parser.add_argument("--output-dir", type=str, default="./data/processed",
                        help="Output directory for formatted datasets")
    parser.add_argument("--max-examples", type=int, default=None,
                        help="Max examples per dataset (for testing)")
    args = parser.parse_args()

    registry = create_default_formatter_registry()
    pipeline = FormatPipeline(Path(args.raw_dir), Path(args.output_dir), registry)
    results = pipeline.process_all(args.datasets, args.max_examples)

    for r in results:
        if r["status"] == "success":
            logger.info(f"✓ {r['name']}: {r['total']} total ({r['train']} train / {r['validation']} val / {r['test']} test)")
        else:
            logger.warning(f"✗ {r['name']}: {r['status']}")


if __name__ == "__main__":
    main()
