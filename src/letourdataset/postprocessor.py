#!/usr/bin/env python3
"""
Post-processor for Tour de France data files.

This module handles the final sorting and organization of CSV data files
to ensure consistent structure and ordering across all datasets.
"""

import pandas as pd
from pathlib import Path
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataPostProcessor:
    """Post-processor for Tour de France CSV data files."""
    
    def __init__(self, data_root: str = "data"):
        """
        Initialize the post-processor.
        
        Args:
            data_root: Root directory containing the data folders
        """
        self.data_root = Path(data_root)
        self.men_dir = self.data_root / "men"
        self.women_dir = self.data_root / "women"
    
    def _cast_numeric_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Cast specified columns to numeric, handling errors gracefully.
        
        Args:
            df: DataFrame to process
            columns: List of column names to cast to numeric
            
        Returns:
            DataFrame with numeric columns
        """
        df_copy = df.copy()
        for col in columns:
            if col in df_copy.columns:
                # Convert to numeric, coercing errors to NaN
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                logger.debug(f"Cast column '{col}' to numeric")
        return df_copy
    
    def _reorder_columns(self, df: pd.DataFrame, priority_columns: List[str]) -> pd.DataFrame:
        """
        Reorder DataFrame columns with priority columns first.
        
        Args:
            df: DataFrame to reorder
            priority_columns: Columns to place first (in order)
            
        Returns:
            DataFrame with reordered columns
        """
        # Get existing priority columns (in case some don't exist)
        existing_priority = [col for col in priority_columns if col in df.columns]
        
        # Get remaining columns
        remaining_columns = [col for col in df.columns if col not in existing_priority]
        
        # Create new column order
        new_order = existing_priority + remaining_columns
        
        return df[new_order]
    
    def process_all_rankings_history(self, file_path: Path) -> None:
        """
        Process TDFF_All_Rankings_History.csv file.
        
        Sorts by: Year (numeric), Stages (numeric), Rank (numeric)
        Priority columns: Year, Stages, Rank
        
        Args:
            file_path: Path to the CSV file
        """
        logger.info(f"Processing All Rankings History: {file_path.name}")
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            original_shape = df.shape
            logger.debug(f"Original shape: {original_shape}")
            
            # Cast numeric columns
            numeric_columns = ["Year", "Stages", "Rank"]
            df = self._cast_numeric_columns(df, numeric_columns)
            
            # Reorder columns (Year, Stages, Rank first)
            priority_columns = ["Year", "Stages", "Rank"]
            df = self._reorder_columns(df, priority_columns)
            
            # Sort by Year, then Stages, then Rank
            sort_columns = []
            for col in ["Year", "Stages", "Rank"]:
                if col in df.columns:
                    sort_columns.append(col)
            
            if sort_columns:
                df = df.sort_values(sort_columns, ascending=True)
                logger.debug(f"Sorted by: {sort_columns}")
            
            # Reset index
            df = df.reset_index(drop=True)
            
            # Save back to file
            df.to_csv(file_path, index=False)
            logger.info(f"✅ Processed {file_path.name}: {original_shape[0]} rows, sorted by {sort_columns}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
    
    def process_riders_history(self, file_path: Path) -> None:
        """
        Process TDFF_Riders_History.csv file.
        
        Sorts by: Year (numeric), Rank (numeric)
        Priority columns: Year, Rank
        
        Args:
            file_path: Path to the CSV file
        """
        logger.info(f"Processing Riders History: {file_path.name}")
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            original_shape = df.shape
            logger.debug(f"Original shape: {original_shape}")
            
            # Cast numeric columns
            numeric_columns = ["Year", "Rank"]
            df = self._cast_numeric_columns(df, numeric_columns)
            
            # Reorder columns (Year, Rank first)
            priority_columns = ["Year", "Rank"]
            df = self._reorder_columns(df, priority_columns)
            
            # Sort by Year, then Rank
            sort_columns = []
            for col in ["Year", "Rank"]:
                if col in df.columns:
                    sort_columns.append(col)
            
            if sort_columns:
                df = df.sort_values(sort_columns, ascending=True)
                logger.debug(f"Sorted by: {sort_columns}")
            
            # Reset index
            df = df.reset_index(drop=True)
            
            # Save back to file
            df.to_csv(file_path, index=False)
            logger.info(f"✅ Processed {file_path.name}: {original_shape[0]} rows, sorted by {sort_columns}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
    
    def process_stages_history(self, file_path: Path) -> None:
        """
        Process TDFF_Stages_History.csv file.
        
        Sorts by: Year (numeric), Rank (numeric)
        Priority columns: Year, Rank
        
        Args:
            file_path: Path to the CSV file
        """
        logger.info(f"Processing Stages History: {file_path.name}")
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            original_shape = df.shape
            logger.debug(f"Original shape: {original_shape}")
            
            # Cast numeric columns
            numeric_columns = ["Year", "Rank"]
            df = self._cast_numeric_columns(df, numeric_columns)
            
            # Reorder columns (Year, Rank first)
            priority_columns = ["Year", "Rank"]
            df = self._reorder_columns(df, priority_columns)
            
            # Sort by Year, then Rank
            sort_columns = []
            for col in ["Year", "Rank"]:
                if col in df.columns:
                    sort_columns.append(col)
            
            if sort_columns:
                df = df.sort_values(sort_columns, ascending=True)
                logger.debug(f"Sorted by: {sort_columns}")
            
            # Reset index
            df = df.reset_index(drop=True)
            
            # Save back to file
            df.to_csv(file_path, index=False)
            logger.info(f"✅ Processed {file_path.name}: {original_shape[0]} rows, sorted by {sort_columns}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
    
    def process_all_files(self) -> None:
        """Process all data files in both men's and women's directories."""
        logger.info("🔄 Starting post-processing of all data files...")
        
        # Process women's files (main focus based on user request)
        women_files = {
            "TDFF_All_Rankings_History.csv": self.process_all_rankings_history,
            "TDFF_Riders_History.csv": self.process_riders_history,
            "TDFF_Stages_History.csv": self.process_stages_history,
        }
        
        for filename, processor_func in women_files.items():
            file_path = self.women_dir / filename
            processor_func(file_path)
        
        # Process men's files with same logic (adapt naming)
        men_files = {
            "TDF_All_Rankings_History.csv": self.process_all_rankings_history,
            "TDF_Riders_History.csv": self.process_riders_history,
            "TDF_Stages_History.csv": self.process_stages_history,
        }
        
        for filename, processor_func in men_files.items():
            file_path = self.men_dir / filename
            processor_func(file_path)
        
        logger.info("✅ Post-processing completed for all data files!")


def main():
    """Main entry point for the post-processor."""
    import sys
    
    # Set up argument parsing for data directory
    data_root = "data"
    if len(sys.argv) > 1:
        data_root = sys.argv[1]
    
    # Initialize and run post-processor
    processor = DataPostProcessor(data_root)
    processor.process_all_files()


if __name__ == "__main__":
    main()
