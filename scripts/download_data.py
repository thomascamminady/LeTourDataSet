#!/usr/bin/env python3
"""
Download Tour de France historical data.

This script downloads and processes historical data for both the Tour de France
(men's race) and Tour de France Femmes (women's race) from the official websites.
"""

import asyncio
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from letourdataset.scraper import Scraper
from letourdataset.visualizer import Visualizer


async def main():
    """Download historical Tour de France data for both men's and women's races."""
    save_folder = "../data"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    print("Downloading Tour de France (Men's) historical data...")
    # Men
    scraper = Scraper(history_page="https://www.letour.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(os.path.join(save_folder, "TDF_Riders_History.csv"))
    df_stages.to_csv(os.path.join(save_folder, "TDF_Stages_History.csv"))
    df_all_rankings.to_csv(os.path.join(save_folder, "TDF_All_Rankings_History.csv"))
    Visualizer().plot(
        df_rankings, saveas=os.path.join(save_folder, "TDF_Distance_And_Pace.png")
    )

    print("Downloading Tour de France Femmes (Women's) historical data...")
    # Women
    scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(os.path.join(save_folder, "TDFF_Riders_History.csv"))
    df_stages.to_csv(os.path.join(save_folder, "TDFF_Stages_History.csv"))
    df_all_rankings.to_csv(os.path.join(save_folder, "TDFF_All_Rankings_History.csv"))
    Visualizer().plot(
        df_rankings, saveas=os.path.join(save_folder, "TDFF_Distance_And_Pace.png")
    )

    print("Data download and processing completed!")


if __name__ == "__main__":
    asyncio.run(main())
