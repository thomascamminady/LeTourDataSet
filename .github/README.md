# CSV Data Protection Workflow

This directory contains GitHub workflows and scripts to ensure data integrity in the LeTourDataSet repository.

## Overview

The CSV Data Protection workflow automatically checks that changes to CSV files in the `data/` directory only add content and never delete or modify existing data. This ensures the historical integrity of the Tour de France dataset.

## Files

-   `csv-data-protection.yml`: GitHub Actions workflow that triggers on changes to CSV files
-   `check_csv_integrity.py`: Python script that performs the actual integrity checks

## What it checks

1. **Row Count**: Ensures the number of rows only increases or stays the same
2. **Column Count**: Ensures the number of columns only increases or stays the same
3. **Column Names**: Ensures no existing columns are removed
4. **Data Integrity**: Ensures existing data is not modified
5. **New Content**: Allows addition of new rows and columns

## When it runs

-   On pull requests that modify files in `data/*.csv`
-   On pushes to `main`/`master` branch that modify files in `data/*.csv`

## What happens if the check fails

If the workflow detects data deletion or modification:

1. The GitHub check will fail with a ❌ status
2. Pull requests will be blocked from merging
3. Detailed error messages will show exactly what data was deleted/modified
4. Suggestions for fixing the issues will be provided

## Bypassing the check

If you need to legitimately modify historical data (e.g., fixing a critical error):

1. Contact the repository maintainer
2. Document the reason for the change
3. Consider adding corrected data as new rows rather than modifying existing ones
4. The maintainer can override the check if necessary

## Example output

### ✅ Successful check (additions only)

```
🔍 Starting CSV Data Protection Check...
Found 6 CSV file(s) to check:
  - TDF_Riders_History.csv
  - TDF_Stages_History.csv
  - TDFF_Riders_History.csv

✅ TDF_Riders_History.csv: 5 rows added
✅ TDF_Stages_History.csv: 21 rows added
✅ TDFF_Riders_History.csv: 1 rows added

🎉 All CSV files passed integrity checks!
```

### ❌ Failed check (deletion detected)

```
❌ CSV integrity check failed!

The following issues were detected:
  ❌ TDF_Riders_History.csv: Row count decreased from 115 to 114
  ❌ TDF_Stages_History.csv: Columns removed: Distance_km

💡 To fix these issues:
   - Ensure you're only adding new data, not modifying existing data
   - Add columns instead of removing them
```

## Technical details

The script compares CSV files between the current branch and the base branch (usually `main`/`master`) using:

-   Git commands to retrieve historical versions
-   Pandas for CSV analysis and comparison
-   Detailed row-by-row and column-by-column validation

This ensures that the Tour de France historical dataset maintains its integrity and continues to grow over time without losing valuable historical information.
