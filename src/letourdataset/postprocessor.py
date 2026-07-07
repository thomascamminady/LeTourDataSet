#!/usr/bin/env python3
"""
Post-processor for Tour de France data files.

Sorts the CSV data files numerically and normalises integer column
representations (e.g. rider numbers written as '11', not '11.0') without
changing any values or the column order.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileSpec:
    """Sorting and typing rules for one CSV data file."""

    sort_columns: tuple[str, ...]
    integer_columns: tuple[str, ...] = ()
    # Stage numbers are integers except for split stages (e.g. 13.1, 13.2),
    # so they get a mixed int/float representation instead of Int64.
    stage_number_columns: tuple[str, ...] = ()


RIDERS_SPEC = FileSpec(
    sort_columns=("Year", "Rank"),
    integer_columns=("Year", "Rank", "Rider No."),
)
STAGES_SPEC = FileSpec(
    sort_columns=("Year", "Stages"),
    integer_columns=("Year",),
    stage_number_columns=("Stages",),
)
ALL_RANKINGS_SPEC = FileSpec(
    sort_columns=("Year", "Stages", "Rank"),
    integer_columns=("Year",),
    stage_number_columns=("Stages",),
)


def _format_stage_number(value: float) -> int | float | None:
    if pd.isna(value):
        return None
    if float(value).is_integer():
        return int(value)
    return value


class DataPostProcessor:
    """Post-processor for Tour de France CSV data files."""

    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root)
        self.men_dir = self.data_root / "men"
        self.women_dir = self.data_root / "women"

    def process_file(self, file_path: Path, spec: FileSpec) -> None:
        """Sort and normalise a single CSV file in place."""
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return

        df = pd.read_csv(file_path, low_memory=False)

        for col in spec.integer_columns:
            if col not in df.columns:
                continue
            numeric = pd.to_numeric(df[col], errors="coerce")
            coercion_lossless = numeric.notna().eq(df[col].notna()).all()
            if coercion_lossless and (numeric.dropna() % 1 == 0).all():
                df[col] = numeric.astype("Int64")
            else:
                logger.warning(
                    "Column '%s' in %s contains non-integer values; left as is.",
                    col,
                    file_path.name,
                )

        for col in spec.stage_number_columns:
            if col not in df.columns:
                continue
            # The explicit object dtype keeps the mixed int/float values;
            # letting pandas infer would coerce the ints back to floats and
            # write '1.0' again.
            numeric = pd.to_numeric(df[col], errors="coerce")
            df[col] = pd.Series(
                [_format_stage_number(value) for value in numeric],
                index=df.index,
                dtype=object,
            )

        # Sort on numeric keys so e.g. rank 10 comes after rank 2 even if a
        # column arrives as strings; the original values stay untouched.
        sort_columns = [col for col in spec.sort_columns if col in df.columns]
        if sort_columns:
            key_names = [f"__sort_{col}" for col in sort_columns]
            for col, key in zip(sort_columns, key_names):
                df[key] = pd.to_numeric(df[col], errors="coerce")
            df = (
                df.sort_values(key_names, ascending=True, kind="stable")
                .drop(columns=key_names)
                .reset_index(drop=True)
            )

        df.to_csv(file_path, index=False)
        logger.info(
            "✅ Processed %s: %d rows, sorted by %s",
            file_path.name,
            len(df),
            sort_columns,
        )

    def process_all_files(self) -> None:
        """Process all data files in both men's and women's directories."""
        logger.info("🔄 Starting post-processing of all data files...")

        file_specs = {
            "{}_Riders_History.csv": RIDERS_SPEC,
            "{}_Stages_History.csv": STAGES_SPEC,
            "{}_All_Rankings_History.csv": ALL_RANKINGS_SPEC,
        }

        failures: list[str] = []
        for directory, prefix in ((self.men_dir, "TDF"), (self.women_dir, "TDFF")):
            for pattern, spec in file_specs.items():
                file_path = directory / pattern.format(prefix)
                try:
                    self.process_file(file_path, spec)
                except Exception:
                    logger.exception("Error processing %s", file_path)
                    failures.append(str(file_path))

        if failures:
            raise RuntimeError(f"Post-processing failed for: {', '.join(failures)}")
        logger.info("✅ Post-processing completed for all data files!")
