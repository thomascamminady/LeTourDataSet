#!/usr/bin/env python3
"""
Post-process Tour de France data files.

This script runs the postprocessor to sort and organize all CSV data files.
"""

import logging
from pathlib import Path

from letourdataset.postprocessor import DataPostProcessor

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Run the data post-processor."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    print("🔄 Post-processing Tour de France data files...")
    processor = DataPostProcessor(REPO_ROOT / "data")
    processor.process_all_files()
    print("✅ Post-processing completed!")


if __name__ == "__main__":
    main()
