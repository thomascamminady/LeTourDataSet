# CSV Data Protection Workflow

This directory contains GitHub workflows and scripts to ensure data integrity in the LeTourDataSet repository.

## Overview

The CSV Data Protection workflow automatically checks that changes to CSV files in the `data/` directory only add content and never delete or modify existing data. This ensures the historical integrity of the Tour de France dataset.

## Files

-   `workflows/csv-data-protection.yml`: GitHub Actions workflow that triggers on changes to CSV files
-   `scripts/check_csv_integrity.py`: Python script that performs the actual integrity checks

## What it checks

Rows are compared as **multisets of canonicalised values** between the base
branch and the current version, so the check is robust against re-sorting a
file and against pure formatting changes (`11.0` vs `11`):

1. **Row protection**: every row present in the base version must still be
   present (a modified row counts as a removed row plus an added row)
2. **Column protection**: existing columns must not be removed
3. **New content**: adding rows and columns is always allowed

## When it runs

-   On pull requests that modify files in `data/**/*.csv`
-   On pushes to `main`/`master` that modify files in `data/**/*.csv`
-   Locally via `make check-csv` (and as an informational step of `make update`)

## Fixing genuinely wrong data

Historical values sometimes need corrections (e.g. the source site fixed a
result). To make such a change:

1. Put the marker `[data-fix]` in the commit message
2. Explain in the commit message why the data had to change
3. The check will report the modified rows but pass

Alternatively, run the script with `ALLOW_DATA_FIX=1` for local
verification of a planned correction.

## Example output

### ✅ Successful check (additions only)

```
✅ data/men/TDF_Riders_History.csv: 160 row(s) added
✅ data/men/TDF_Stages_History.csv: 21 row(s) added
✅ data/women/TDFF_Riders_History.csv: no changes

🎉 All CSV files passed integrity checks!
```

### ❌ Failed check (deletion or modification detected)

```
❌ data/men/TDF_Riders_History.csv: 3 existing row(s) removed or modified (e.g. 1 | TADEJ POGACAR | ... )

💡 To fix these issues:
   - Ensure you're only adding new data, not modifying existing data
   - For legitimate corrections, include '[data-fix]' in the commit message
```

## Technical details

The script compares each CSV file between the working tree and the base ref
(the PR base branch, else `origin/main`/`origin/master`) using `git show`
and pandas. Cell values are canonicalised (whitespace-trimmed, numbers
normalised) and rows compared as multisets over the columns common to both
versions, which makes the check independent of row order and column order.
