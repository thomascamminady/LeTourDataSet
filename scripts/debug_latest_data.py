#!/usr/bin/env python3
"""
Debug script to investigate why 2025 men's and 2024 women's data isn't being retrieved.
"""

import asyncio
import logging
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from letourdataset.scraper import Scraper


async def debug_latest_data():
    """Debug the latest data retrieval for both men and women."""

    # Enable detailed logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🔍 Debugging latest data retrieval...")
    print("=" * 60)

    # Test men's data (should include 2025)
    print("\n📊 Testing Men's Tour de France (2025 expected)...")
    print("-" * 40)

    try:
        men_scraper = Scraper(history_page="https://www.letour.fr/en/history")
        print(f"Found {len(men_scraper._links)} links for men's data")

        # Show the first few links (most recent years)
        print("First 5 links (most recent):")
        for i, link in enumerate(men_scraper._links[:5]):
            print(f"  {i+1}. {men_scraper._prefix + link}")

        # Test just the first (most recent) link
        if men_scraper._links:
            print(
                f"\n🔍 Testing most recent men's link: {men_scraper._prefix + men_scraper._links[0]}"
            )
            soup, year, distance = men_scraper._get_soup_year_distance(
                men_scraper._prefix + men_scraper._links[0]
            )
            print(f"✅ Parsed: Year={year}, Distance={distance}km")

            # Check if it's 2025
            if year == 2025:
                print("🎉 Found 2025 men's data!")
            else:
                print(f"⚠️  Expected 2025, but got {year}")

    except Exception as e:
        print(f"❌ Error with men's data: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)

    # Test women's data (should include 2024)
    print("\n📊 Testing Women's Tour de France (2024 expected)...")
    print("-" * 40)

    try:
        women_scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
        print(f"Found {len(women_scraper._links)} links for women's data")

        # Show the first few links (most recent years)
        print("First 5 links (most recent):")
        for i, link in enumerate(women_scraper._links[:5]):
            print(f"  {i+1}. {women_scraper._prefix + link}")

        # Test just the first (most recent) link
        if women_scraper._links:
            print(
                f"\n🔍 Testing most recent women's link: {women_scraper._prefix + women_scraper._links[0]}"
            )
            soup, year, distance = women_scraper._get_soup_year_distance(
                women_scraper._prefix + women_scraper._links[0]
            )
            print(f"✅ Parsed: Year={year}, Distance={distance}km")

            # Check if it's 2024
            if year == 2024:
                print("🎉 Found 2024 women's data!")
            else:
                print(f"⚠️  Expected 2024, but got {year}")

    except Exception as e:
        print(f"❌ Error with women's data: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🔍 Debug completed. Check output above for issues.")


if __name__ == "__main__":
    asyncio.run(debug_latest_data())
