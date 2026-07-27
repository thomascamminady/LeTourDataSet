#!/usr/bin/env python3
"""
Generate plots for Tour de France historical data.

Plot titles carry the covered year range, which comes from
`letourdataset.coverage` rather than being recomputed here, so a new
edition shows up in every title without any hand-editing.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from letourdataset.coverage import MEN, WOMEN, RaceCoverage, load_coverage
from letourdataset.visualizer import Visualizer

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class PlotSpec:
    """Where one race's riders data lives and what to draw from it."""

    riders_file: str
    pace_plot: str
    margin_plot: str
    pace_title: str
    margin_title: str

    def titles(self, coverage: RaceCoverage) -> tuple[str, str]:
        """Plot titles for this race, with the covered years appended."""
        years = f"{coverage.first_year} - {coverage.latest_year}"
        return f"{self.pace_title} {years}", f"{self.margin_title} {years}"


PLOT_SPECS: dict[str, PlotSpec] = {
    MEN: PlotSpec(
        riders_file="men/TDF_Riders_History.csv",
        pace_plot="TDF_Distance_And_Pace.png",
        margin_plot="TDF_Winning_Margin.png",
        pace_title="Tour de France",
        margin_title="How close was the race? Winning margin,",
    ),
    WOMEN: PlotSpec(
        riders_file="women/TDFF_Riders_History.csv",
        pace_plot="TDFF_Distance_And_Pace.png",
        margin_plot="TDFF_Winning_Margin.png",
        pace_title="Tour de France Femmes",
        margin_title="Tour de France Femmes winning margin,",
    ),
}


def main() -> None:
    """Generate every plot from the committed CSV data."""
    data_folder = REPO_ROOT / "data"
    plots_folder = data_folder / "plots"
    plots_folder.mkdir(parents=True, exist_ok=True)

    coverage = load_coverage(data_folder)
    visualizer = Visualizer()

    print("Generating plots for Tour de France data...")
    for key, spec in PLOT_SPECS.items():
        df = pd.read_csv(data_folder / spec.riders_file, low_memory=False)
        pace_title, margin_title = spec.titles(coverage[key])

        print(f"Creating {key}'s distance and pace plot...")
        visualizer.plot(df, saveas=str(plots_folder / spec.pace_plot), title=pace_title)
        print(f"Creating {key}'s winning margin plot...")
        visualizer.plot_winning_margin(
            df, saveas=str(plots_folder / spec.margin_plot), title=margin_title
        )

    print("Plot generation completed!")


if __name__ == "__main__":
    main()
