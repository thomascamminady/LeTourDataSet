#!/usr/bin/env python3
"""
Generate plots for Tour de France historical data.

This script creates visualizations for both men's and women's Tour de France data.
"""

from pathlib import Path

import pandas as pd

from letourdataset.visualizer import Visualizer

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Generate plots for Tour de France data."""
    base_folder = REPO_ROOT / "data"
    men_folder = base_folder / "men"
    women_folder = base_folder / "women"
    plots_folder = base_folder / "plots"

    plots_folder.mkdir(parents=True, exist_ok=True)

    print("Generating plots for Tour de France data...")

    # Men's plots
    men_riders_file = men_folder / "TDF_Riders_History.csv"
    if men_riders_file.exists():
        print("Creating men's distance and pace plot...")
        df_men = pd.read_csv(men_riders_file)
        Visualizer().plot(
            df_men, saveas=str(plots_folder / "TDF_Distance_And_Pace.png")
        )
    else:
        print(f"Warning: {men_riders_file} not found. Run 'make update' first.")

    # Women's plots
    women_riders_file = women_folder / "TDFF_Riders_History.csv"
    if women_riders_file.exists():
        print("Creating women's distance and pace plot...")
        df_women = pd.read_csv(women_riders_file)
        Visualizer().plot(
            df_women,
            saveas=str(plots_folder / "TDFF_Distance_And_Pace.png"),
            title=(
                "Tour de France Femmes "
                f"{df_women['Year'].min()} - {df_women['Year'].max()}"
            ),
        )
    else:
        print(f"Warning: {women_riders_file} not found. Run 'make update' first.")

    print("Plot generation completed!")


if __name__ == "__main__":
    main()
