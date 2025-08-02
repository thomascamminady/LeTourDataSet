#!/usr/bin/env python3
"""
Post-process Tour de France data files.

This script runs the postprocessor to sort and organize all CSV data files.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from letourdataset.postprocessor import DataPostProcessor


def main():
    """Run the data post-processor."""
    print("🔄 Post-processing Tour de France data files...")
    
    # Change to project root directory
    script_dir = os.path.dirname(__file__)
    project_root = os.path.join(script_dir, "..")
    data_root = os.path.join(project_root, "data")
    
    # Initialize and run post-processor
    processor = DataPostProcessor(data_root)
    processor.process_all_files()
    
    print("✅ Post-processing completed!")


if __name__ == "__main__":
    main()
