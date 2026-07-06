#!/usr/bin/env python3
"""
Download Tour de France historical data.

This script downloads and processes historical data for both the Tour de France
(men's race) and Tour de France Femmes (women's race) from the official websites.
"""

import asyncio
from pathlib import Path

from letourdataset.scraper import Scraper

REPO_ROOT = Path(__file__).resolve().parent.parent


async def main() -> None:
    """Download historical Tour de France data for both men's and women's races."""
    base_folder = REPO_ROOT / "data"
    men_folder = base_folder / "men"
    women_folder = base_folder / "women"

    for folder in (men_folder, women_folder):
        folder.mkdir(parents=True, exist_ok=True)

    print("Downloading Tour de France (Men's) historical data...")
    scraper = Scraper(history_page="https://www.letour.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(men_folder / "TDF_Riders_History.csv", index=False)
    df_stages.to_csv(men_folder / "TDF_Stages_History.csv", index=False)
    df_all_rankings.to_csv(men_folder / "TDF_All_Rankings_History.csv", index=False)

    print("Downloading Tour de France Femmes (Women's) historical data...")
    scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
    df_stages, df_rankings, df_all_rankings = await scraper.run()
    df_rankings.to_csv(women_folder / "TDFF_Riders_History.csv", index=False)
    df_stages.to_csv(women_folder / "TDFF_Stages_History.csv", index=False)
    df_all_rankings.to_csv(women_folder / "TDFF_All_Rankings_History.csv", index=False)

    print("Data download and processing completed!")


if __name__ == "__main__":
    asyncio.run(main())
