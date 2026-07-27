#!/usr/bin/env python3
"""What the dataset covers, derived from the CSV files themselves.

The riders history files are the single source of truth for which editions
exist. Every year that appears in the README, on the docs page or in a plot
title is computed from them, so finishing an edition never means editing a
year by hand: `make update` scrapes the new edition and everything else
follows from the data.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

MEN = "men"
WOMEN = "women"

RIDERS_FILES: dict[str, tuple[str, str]] = {
    MEN: ("Men's Tour de France", "men/TDF_Riders_History.csv"),
    WOMEN: (
        "Women's Tour de France (Tour de France Femmes avec Zwift)",
        "women/TDFF_Riders_History.csv",
    ),
}


@dataclass(frozen=True)
class RaceCoverage:
    """Which editions of one race the dataset covers."""

    name: str
    first_year: int
    latest_year: int
    editions: int

    @property
    def span_years(self) -> int:
        """Years from the first edition to the latest one.

        The Tour skipped both world wars, so this is deliberately larger
        than `editions`.
        """
        return self.latest_year - self.first_year


def race_coverage(riders_file: Path, name: str) -> RaceCoverage:
    """Derive one race's coverage from its riders history file."""
    years = pd.read_csv(riders_file, low_memory=False, usecols=["Year"])["Year"]
    years = pd.to_numeric(years, errors="coerce").dropna()
    if years.empty:
        raise ValueError(f"{riders_file} has no usable Year values.")
    return RaceCoverage(
        name=name,
        first_year=int(years.min()),
        latest_year=int(years.max()),
        editions=int(years.nunique()),
    )


def load_coverage(data_root: str | Path = "data") -> dict[str, RaceCoverage]:
    """Derive the coverage of both races from the data directory."""
    root = Path(data_root)
    coverage: dict[str, RaceCoverage] = {}
    for key, (name, relative) in RIDERS_FILES.items():
        path = root / relative
        if not path.exists():
            raise FileNotFoundError(
                f"Missing riders history file: {path}. Run 'make update' first."
            )
        coverage[key] = race_coverage(path, name)
    return coverage
