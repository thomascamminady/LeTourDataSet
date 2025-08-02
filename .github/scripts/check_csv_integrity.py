#!/usr/bin/env python3
"""
CSV Data Protection Script

This script ensures that CSV files in the data/ directory only grow over time.
It checks that:
1. No rows are deleted (row count can only increase or stay the same)
2. No columns are deleted (column count can only increase or stay the same)
3. Existing data is not modified (data integrity is maintained)

The script compares CSV files between the current commit and the base branch.
"""

import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
import tempfile


def run_git_command(command):
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {command}")
        print(f"Error: {e.stderr}")
        return None


def get_base_branch():
    """Determine the base branch to compare against."""
    event_name = os.environ.get('GITHUB_EVENT_NAME', '')
    
    if event_name == 'pull_request':
        # For pull requests, use the base branch
        base_ref = os.environ.get('GITHUB_BASE_REF', '')
        if base_ref:
            return f"origin/{base_ref}"
    
    # For push events or fallback, use main or master
    branches = run_git_command("git branch -r")
    if branches:
        if "origin/main" in branches:
            return "origin/main"
        elif "origin/master" in branches:
            return "origin/master"
    
    # Last resort
    return "HEAD~1"


def get_csv_files_in_data():
    """Get all CSV files in the data/ directory."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    
    return list(data_dir.glob("*.csv"))


def check_csv_integrity(csv_file, base_branch):
    """
    Check if the CSV file maintains integrity (only grows, no deletions).
    
    Args:
        csv_file (Path): Path to the CSV file
        base_branch (str): Base branch to compare against
        
    Returns:
        tuple: (is_valid, message)
    """
    print(f"Checking integrity of {csv_file}...")
    
    # Create temporary directory for old version
    with tempfile.TemporaryDirectory() as temp_dir:
        old_file_path = Path(temp_dir) / csv_file.name
        
        # Get the old version of the file
        git_command = f"git show {base_branch}:{csv_file}"
        result = subprocess.run(
            git_command, shell=True, capture_output=True, text=True
        )
        
        if result.returncode != 0:
            # File doesn't exist in base branch (new file)
            print(f"  ✅ {csv_file.name} is a new file")
            return True, f"New file: {csv_file.name}"
        
        # Write old version to temporary file
        with open(old_file_path, 'w') as f:
            f.write(result.stdout)
        
        try:
            # Load both versions (suppress dtype warnings for mixed columns)
            old_df = pd.read_csv(old_file_path, low_memory=False)
            new_df = pd.read_csv(csv_file, low_memory=False)
            
            # Check row count
            old_rows = len(old_df)
            new_rows = len(new_df)
            
            if new_rows < old_rows:
                return False, f"❌ {csv_file.name}: Row count decreased from {old_rows} to {new_rows}"
            
            # Check column count and names
            old_columns = set(old_df.columns)
            new_columns = set(new_df.columns)
            
            if len(new_columns) < len(old_columns):
                return False, f"❌ {csv_file.name}: Column count decreased from {len(old_columns)} to {len(new_columns)}"
            
            # Check if any columns were removed
            removed_columns = old_columns - new_columns
            if removed_columns:
                return False, f"❌ {csv_file.name}: Columns removed: {', '.join(removed_columns)}"
            
            # If we have the same number of rows, check for data modifications
            if new_rows == old_rows:
                # Check if existing data was modified
                common_columns = old_columns.intersection(new_columns)
                
                # Compare common columns for the overlapping rows
                for col in common_columns:
                    if not old_df[col].equals(new_df[col]):
                        # More detailed check to find which rows changed
                        differences = old_df[col] != new_df[col]
                        if differences.any():
                            changed_indices = differences[differences].index.tolist()
                            return False, f"❌ {csv_file.name}: Data modified in column '{col}' at rows: {changed_indices[:5]}{'...' if len(changed_indices) > 5 else ''}"
            
            # All checks passed
            added_rows = new_rows - old_rows
            added_columns = new_columns - old_columns
            
            message_parts = []
            if added_rows > 0:
                message_parts.append(f"{added_rows} rows added")
            if added_columns:
                message_parts.append(f"columns added: {', '.join(added_columns)}")
            
            if message_parts:
                message = f"✅ {csv_file.name}: " + ", ".join(message_parts)
            else:
                message = f"✅ {csv_file.name}: No changes detected"
            
            return True, message
            
        except Exception as e:
            return False, f"❌ {csv_file.name}: Error reading CSV file: {str(e)}"


def main():
    """Main function to check all CSV files."""
    print("🔍 Starting CSV Data Protection Check...")
    print("=" * 50)
    
    # Get base branch for comparison
    base_branch = get_base_branch()
    print(f"Comparing against base branch: {base_branch}")
    print()
    
    # Get all CSV files in data directory
    csv_files = get_csv_files_in_data()
    
    if not csv_files:
        print("ℹ️  No CSV files found in data/ directory")
        return 0
    
    print(f"Found {len(csv_files)} CSV file(s) to check:")
    for csv_file in csv_files:
        print(f"  - {csv_file}")
    print()
    
    # Check each CSV file
    all_valid = True
    results = []
    
    for csv_file in csv_files:
        is_valid, message = check_csv_integrity(csv_file, base_branch)
        results.append((csv_file.name, is_valid, message))
        
        if not is_valid:
            all_valid = False
        
        print(f"  {message}")
    
    print()
    print("=" * 50)
    
    if all_valid:
        print("🎉 All CSV files passed integrity checks!")
        print("✅ Data protection verified: Only additions detected, no deletions.")
        return 0
    else:
        print("❌ CSV integrity check failed!")
        print()
        print("The following issues were detected:")
        for filename, is_valid, message in results:
            if not is_valid:
                print(f"  {message}")
        
        print()
        print("💡 To fix these issues:")
        print("   - Ensure you're only adding new data, not modifying existing data")
        print("   - If you need to fix data, consider adding corrected rows rather than modifying existing ones")
        print("   - Add columns instead of removing them")
        print("   - Contact the repository maintainer if you believe this is a false positive")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
