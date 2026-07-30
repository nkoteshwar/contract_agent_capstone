"""
Dataset Download Pipeline
Strategy Pattern — each dataset has its own downloader strategy.
Reuses the IClauseExtractionStrategy pattern from clause_extraction_agent.py.

Usage:
    python -m training.scripts.download_datasets
    python -m training.scripts.download_datasets --datasets cuad ledgar
    python -m training.scripts.download_datasets --dry-run
"""

import argparse
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

from datasets import load_dataset, DatasetDict
from tqdm import tqdm

from training.scripts.utils import setup_training_logging, get_logger, Registry

# ---------------------------------------------------------------------------
# Logging – reuses the structured-logging convention from backend/shared/utils
# ---------------------------------------------------------------------------
setup_training_logging()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Strategy interface (mirrors IClauseExtractionStrategy in existing codebase)
# ---------------------------------------------------------------------------

class IDatasetDownloader(ABC):
    """Strategy interface for dataset downloading — Single Responsibility."""

    @abstractmethod
    def download(self, output_dir: Path) -> Dict[str, Any]:
        """Download dataset and return metadata."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """Return dataset name, description, and HuggingFace ID."""
        pass


# ---------------------------------------------------------------------------
# Concrete strategies — one per dataset (Open/Closed: add new datasets
# by adding a new class, never modifying existing ones)
# ---------------------------------------------------------------------------

class CUADDownloader(IDatasetDownloader):
    """CUAD — clause extraction & risk span identification."""

    def download(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Downloading CUAD dataset…")
        dataset = load_dataset("theatticusproject/cuad-qa", trust_remote_code=True)
        save_path = output_dir / "cuad"
        save_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(save_path))
        return {"name": "cuad", "path": str(save_path), "splits": list(dataset.keys()),
                "total_examples": sum(len(dataset[s]) for s in dataset)}

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "cuad",
            "hf_id": "theatticusproject/cuad-qa",
            "description": "510 contracts, 13K annotations for 41 clause types (SQuAD-style)"
        }


class LEDGARDownloader(IDatasetDownloader):
    """LEDGAR — clause classification (100 provision types)."""

    def download(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Downloading LEDGAR dataset…")
        dataset = load_dataset("lex_glue", "ledgar", trust_remote_code=True)
        save_path = output_dir / "ledgar"
        save_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(save_path))
        return {"name": "ledgar", "path": str(save_path), "splits": list(dataset.keys()),
                "total_examples": sum(len(dataset[s]) for s in dataset)}

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "ledgar",
            "hf_id": "lex_glue/ledgar",
            "description": "80K+ provisions from SEC filings, 100 provision-type labels"
        }


class ContractNLIDownloader(IDatasetDownloader):
    """ContractNLI — entailment & evidence detection."""

    def download(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Downloading ContractNLI dataset…")
        dataset = load_dataset("kiddothe2b/contract-nli", trust_remote_code=True)
        save_path = output_dir / "contract_nli"
        save_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(save_path))
        return {"name": "contract_nli", "path": str(save_path), "splits": list(dataset.keys()),
                "total_examples": sum(len(dataset[s]) for s in dataset)}

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "contract_nli",
            "hf_id": "kiddothe2b/contract-nli",
            "description": "607 NDAs, 10K annotations — entailment with evidence spans"
        }


class MAUDDownloader(IDatasetDownloader):
    """MAUD — advanced M&A contract comprehension."""

    def download(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Downloading MAUD dataset…")
        dataset = load_dataset("theatticusproject/maud", trust_remote_code=True)
        save_path = output_dir / "maud"
        save_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(save_path))
        return {"name": "maud", "path": str(save_path), "splits": list(dataset.keys()),
                "total_examples": sum(len(dataset[s]) for s in dataset)}

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "maud",
            "hf_id": "theatticusproject/maud",
            "description": "39K annotations on M&A contracts — complex comprehension"
        }


class LegalBenchDownloader(IDatasetDownloader):
    """LegalBench — evaluation-only benchmark."""

    def download(self, output_dir: Path) -> Dict[str, Any]:
        logger.info("Downloading LegalBench dataset…")
        dataset = load_dataset("nguha/legalbench", "contract_qa", trust_remote_code=True)
        save_path = output_dir / "legalbench"
        save_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(save_path))
        return {"name": "legalbench", "path": str(save_path), "splits": list(dataset.keys()),
                "total_examples": sum(len(dataset[s]) for s in dataset)}

    def get_info(self) -> Dict[str, str]:
        return {
            "name": "legalbench",
            "hf_id": "nguha/legalbench",
            "description": "Legal reasoning benchmark — evaluation only"
        }


# ---------------------------------------------------------------------------
# Registry + Factory (uses generic Registry from utils — DRY)
# ---------------------------------------------------------------------------

def create_default_registry() -> Registry[IDatasetDownloader]:
    """Factory method — creates registry with all supported datasets."""
    registry = Registry[IDatasetDownloader]()
    registry.register("cuad", CUADDownloader())
    registry.register("ledgar", LEDGARDownloader())
    registry.register("contract_nli", ContractNLIDownloader())
    registry.register("maud", MAUDDownloader())
    registry.register("legalbench", LegalBenchDownloader())
    return registry


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class DownloadPipeline:
    """
    Orchestrates dataset downloads using the registry.
    Single Responsibility: only handles download orchestration.
    """

    def __init__(self, registry: Registry[IDatasetDownloader], output_dir: Path):
        self.registry = registry
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_all(self, dataset_names: Optional[List[str]] = None,
                     dry_run: bool = False) -> List[Dict[str, Any]]:
        """Download specified datasets (or all if none specified)."""
        names = dataset_names or self.registry.list_all()
        results = []

        for name in names:
            downloader = self.registry.get(name)
            if not downloader:
                logger.warning(f"Unknown dataset: {name}. Skipping.")
                continue

            info = downloader.get_info()
            if dry_run:
                logger.info(f"[DRY-RUN] Would download: {info['name']} ({info['hf_id']})")
                results.append({"name": info["name"], "status": "dry-run", "info": info})
                continue

            try:
                result = downloader.download(self.output_dir)
                result["status"] = "success"
                results.append(result)
                logger.info(f"✓ Downloaded {name}: {result.get('total_examples', '?')} examples")
            except Exception as e:
                logger.error(f"✗ Failed to download {name}: {e}")
                results.append({"name": name, "status": "error", "error": str(e)})

        # Save manifest
        manifest_path = self.output_dir / "download_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Manifest saved to {manifest_path}")

        return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download training datasets")
    parser.add_argument("--datasets", nargs="+", default=None,
                        help="Specific datasets to download (default: all)")
    parser.add_argument("--output-dir", type=str, default="./data/raw",
                        help="Output directory for raw datasets")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded without downloading")
    args = parser.parse_args()

    registry = create_default_registry()

    if args.dry_run:
        logger.info("Available datasets:")
        for name in registry.list_all():
            info = registry.get(name).get_info()
            logger.info(f"  {info['name']:20s} — {info['description']}")

    pipeline = DownloadPipeline(registry, Path(args.output_dir))
    results = pipeline.download_all(args.datasets, dry_run=args.dry_run)

    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Download complete: {success_count}/{len(results)} succeeded")


if __name__ == "__main__":
    main()
