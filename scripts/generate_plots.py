#!/usr/bin/env python3
"""
Generate plots for Tour de France historical data.

This script creates visualizations for both men's and women's Tour de France data.
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from letourdataset.visualizer import Visualizer


def main():
    """Generate plots for Tour de France data."""
    base_folder = "../data"
    men_folder = os.path.join(base_folder, "men")
    women_folder = os.path.join(base_folder, "women")
    plots_folder = os.path.join(base_folder, "plots")
    
    # Create plots directory if it doesn't exist
    if not os.path.exists(plots_folder):
        os.makedirs(plots_folder)

    print("Generating plots for Tour de France data...")
    
    # Men's plots
    men_riders_file = os.path.join(men_folder, "TDF_Riders_History.csv")
    if os.path.exists(men_riders_file):
        print("Creating men's distance and pace plot...")
        df_men = pd.read_csv(men_riders_file)
        Visualizer().plot(
            df_men, saveas=os.path.join(plots_folder, "TDF_Distance_And_Pace.png")
        )
    else:
        print(f"Warning: {men_riders_file} not found. Run 'make update' first.")

    # Women's plots
    women_riders_file = os.path.join(women_folder, "TDFF_Riders_History.csv")
    if os.path.exists(women_riders_file):
        print("Creating women's distance and pace plot...")
        df_women = pd.read_csv(women_riders_file)
        Visualizer().plot(
            df_women, saveas=os.path.join(plots_folder, "TDFF_Distance_And_Pace.png")
        )
    else:
        print(f"Warning: {women_riders_file} not found. Run 'make update' first.")

    print("Plot generation completed!")


if __name__ == "__main__":
    main()
