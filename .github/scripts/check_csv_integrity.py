#!/usr/bin/env python3
"""
CSV Data Protection Script

Ensures the CSV files in data/ only grow over time:

1. Rows may be added; existing rows must not be removed or modified.
2. Columns may be added; existing columns must not be removed.

Rows are compared as multisets of canonicalised values over the columns
common to both versions, so re-sorting a file or reformatting a number
(e.g. '11.0' -> '11') does not count as a change. A modified row shows up
as one removed row plus one added row.

Legitimate corrections (fixing wrong values from the source site) are
allowed when a commit in the checked range carries a '[data-fix]' marker
in its message, or when ALLOW_DATA_FIX=1 is set; the check then reports
the changes but passes.
"""

import os
import subprocess
import sys
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

DATA_FIX_MARKER = "[data-fix]"


def run_git_command(args: list[str]) -> str | None:
    """Run a git command and return its stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: git {' '.join(args)}")
        print(f"Error: {e.stderr}")
        return None


def get_base_ref() -> str | None:
    """Determine the git ref to compare against."""
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        base_ref = os.environ.get("GITHUB_BASE_REF", "")
        if base_ref:
            return f"origin/{base_ref}"

    branches = run_git_command(["branch", "-r"]) or ""
    for candidate in ("origin/main", "origin/master"):
        if candidate in branches.split():
            return candidate
    return None


def data_fix_authorized(base_ref: str) -> bool:
    """Check whether data corrections are explicitly authorized."""
    if os.environ.get("ALLOW_DATA_FIX") == "1":
        return True
    messages = run_git_command(["log", f"{base_ref}..HEAD", "--format=%B"]) or ""
    return DATA_FIX_MARKER in messages


def get_csv_files_in_data() -> list[Path]:
    """Get all CSV files in the data/ directory and subdirectories."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return sorted(data_dir.glob("**/*.csv"))


def _canonical(value: Any) -> str:
    """Canonicalise a cell so formatting differences don't count as changes."""
    if pd.isna(value):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).strip()
    if number.is_integer():
        return str(int(number))
    return repr(number)


def canonical_rows(df: pd.DataFrame, columns: list[str]) -> Counter:
    """Multiset of canonicalised row tuples over the given columns."""
    return Counter(
        tuple(_canonical(value) for value in row)
        for row in df[columns].itertuples(index=False, name=None)
    )


def check_csv_integrity(csv_file: Path, base_ref: str) -> tuple[bool, str]:
    """
    Check that a CSV file only grew relative to the base ref.

    Returns:
        tuple: (is_valid, message)
    """
    show = subprocess.run(
        ["git", "show", f"{base_ref}:{csv_file.as_posix()}"],
        capture_output=True,
        text=True,
    )
    if show.returncode != 0:
        # File doesn't exist in the base ref (new file)
        return True, f"✅ {csv_file}: new file"

    try:
        old_df = pd.read_csv(StringIO(show.stdout), low_memory=False)
        new_df = pd.read_csv(csv_file, low_memory=False)
    except Exception as e:
        return False, f"❌ {csv_file}: error reading CSV: {e}"

    problems: list[str] = []

    removed_columns = [c for c in old_df.columns if c not in new_df.columns]
    if removed_columns:
        problems.append(f"columns removed: {', '.join(removed_columns)}")

    common_columns = [c for c in old_df.columns if c in new_df.columns]
    old_rows = canonical_rows(old_df, common_columns)
    new_rows = canonical_rows(new_df, common_columns)

    missing = old_rows - new_rows
    added = new_rows - old_rows

    if missing:
        n_missing = sum(missing.values())
        sample = " | ".join(next(iter(missing))[:6])
        problems.append(
            f"{n_missing} existing row(s) removed or modified (e.g. {sample} ...)"
        )

    if problems:
        return False, f"❌ {csv_file}: " + "; ".join(problems)

    notes: list[str] = []
    if added:
        notes.append(f"{sum(added.values())} row(s) added")
    added_columns = [c for c in new_df.columns if c not in old_df.columns]
    if added_columns:
        notes.append(f"columns added: {', '.join(added_columns)}")
    if not notes:
        notes.append("no changes")

    return True, f"✅ {csv_file}: " + ", ".join(notes)


def main() -> int:
    """Check all CSV files against the base ref."""
    print("🔍 Starting CSV Data Protection Check...")
    print("=" * 50)

    base_ref = get_base_ref()
    if base_ref is None:
        print("ℹ️  No base branch found to compare against; skipping check.")
        return 0
    print(f"Comparing against base ref: {base_ref}")
    print()

    csv_files = get_csv_files_in_data()
    if not csv_files:
        print("ℹ️  No CSV files found in data/ directory")
        return 0

    print(f"Found {len(csv_files)} CSV file(s) to check:")
    for csv_file in csv_files:
        print(f"  - {csv_file}")
    print()

    all_valid = True
    failed_messages: list[str] = []
    for csv_file in csv_files:
        is_valid, message = check_csv_integrity(csv_file, base_ref)
        print(f"  {message}")
        if not is_valid:
            all_valid = False
            failed_messages.append(message)

    print()
    print("=" * 50)

    if all_valid:
        print("🎉 All CSV files passed integrity checks!")
        print("✅ Data protection verified: only additions detected.")
        return 0

    if data_fix_authorized(base_ref):
        print("⚠️  Data changes detected, but they are authorized:")
        print(f"   a commit in {base_ref}..HEAD carries the {DATA_FIX_MARKER} marker")
        print("   (or ALLOW_DATA_FIX=1 is set). Review the changes above carefully.")
        return 0

    print("❌ CSV integrity check failed!")
    print()
    print("The following issues were detected:")
    for message in failed_messages:
        print(f"  {message}")
    print()
    print("💡 To fix these issues:")
    print("   - Ensure you're only adding new data, not modifying existing data")
    print("   - Add columns instead of removing them")
    print(
        f"   - For legitimate corrections, include '{DATA_FIX_MARKER}' in the "
        "commit message and describe why the data had to change"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
