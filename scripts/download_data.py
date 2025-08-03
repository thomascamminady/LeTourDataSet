#!/usr/bin/env python3
"""
Download Tour de France historical data.

This script downloads and processes historical data for both the Tour de France
(men's race) and Tour de France Femmes (women's race) from the official websites.
"""

import asyncio
import os

from src.letourdataset.scraper import Scraper


async def main():
    """Download historical Tour de France data for both men's and women's races."""
    base_folder = "data"
    men_folder = os.path.join(base_folder, "men")
    women_folder = os.path.join(base_folder, "women")

    # Create directories if they don't exist
    for folder in [base_folder, men_folder, women_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    print("Downloading Tour de France (Men's) historical data...")
    # Men
    scraper = Scraper(history_page="https://www.letour.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(os.path.join(men_folder, "TDF_Riders_History.csv"), index=False)
    df_stages.to_csv(os.path.join(men_folder, "TDF_Stages_History.csv"), index=False)
    df_all_rankings.to_csv(
        os.path.join(men_folder, "TDF_All_Rankings_History.csv"), index=False
    )

    print("Downloading Tour de France Femmes (Women's) historical data...")
    # Women
    scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(
        os.path.join(women_folder, "TDFF_Riders_History.csv"), index=False
    )
    df_stages.to_csv(os.path.join(women_folder, "TDFF_Stages_History.csv"), index=False)
    df_all_rankings.to_csv(
        os.path.join(women_folder, "TDFF_All_Rankings_History.csv"), index=False
    )

    print("Data download and processing completed!")


if __name__ == "__main__":
    asyncio.run(main())
