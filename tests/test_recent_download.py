#!/usr/bin/env python3
"""
Quick test to download just the most recent year for both men and women.
"""

import asyncio
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from letourdataset.scraper import Scraper


async def test_recent_download():
    """Test downloading just the most recent year data."""

    print("🔍 Testing download of most recent years...")
    print("=" * 60)

    # Test men's 2025 data
    print("\n📊 Testing Men's 2025 data download...")
    print("-" * 40)

    try:
        men_scraper = Scraper(history_page="https://www.letour.fr/en/history")
        # Only process the first (most recent) link
        original_links = men_scraper._links
        men_scraper._links = [original_links[0]]  # Only 2025

        df_stages, df_rankings, df_all_rankings = await men_scraper.run()

        print(f"✅ Men's data downloaded successfully!")
        print(f"   - Stages: {len(df_stages)} rows")
        print(f"   - Rankings: {len(df_rankings)} rows")
        print(f"   - All Rankings: {len(df_all_rankings)} rows")
        print(
            f"   - Year: {df_rankings['Year'].iloc[0] if len(df_rankings) > 0 else 'Unknown'}"
        )

    except Exception as e:
        print(f"❌ Error with men's data: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)

    # Test women's 2024 data
    print("\n📊 Testing Women's 2024 data download...")
    print("-" * 40)

    try:
        women_scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
        # Only process the first (most recent) link
        original_links = women_scraper._links
        women_scraper._links = [original_links[0]]  # Only 2024

        df_stages, df_rankings, df_all_rankings = await women_scraper.run()

        print(f"✅ Women's data downloaded successfully!")
        print(f"   - Stages: {len(df_stages)} rows")
        print(f"   - Rankings: {len(df_rankings)} rows")
        print(f"   - All Rankings: {len(df_all_rankings)} rows")
        print(
            f"   - Year: {df_rankings['Year'].iloc[0] if len(df_rankings) > 0 else 'Unknown'}"
        )

    except Exception as e:
        print(f"❌ Error with women's data: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎉 Recent download test completed!")


if __name__ == "__main__":
    asyncio.run(test_recent_download())
