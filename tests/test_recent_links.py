#!/usr/bin/env python3
"""
Test the last few links to see what the most recent years are.
"""

import asyncio
import logging
from letourdataset.scraper import Scraper


async def test_recent_links():
    """Test the last few links to see the most recent years."""

    print("🔍 Testing the most recent links...")
    print("=" * 60)

    # Test men's data - check last 5 links
    print("\n📊 Testing Men's Tour de France - Last 5 links...")
    print("-" * 40)

    try:
        men_scraper = Scraper(history_page="https://www.letour.fr/en/history")
        print(f"Total links found: {len(men_scraper._links)}")

        # Test the last 5 links (most recent should be at the end)
        for i in range(min(5, len(men_scraper._links))):
            link_idx = -(i + 1)  # Start from the end
            link = men_scraper._links[link_idx]
            print(f"\nTesting link {link_idx} (from end): {men_scraper._prefix + link}")
            try:
                soup, year, distance = men_scraper._get_soup_year_distance(
                    men_scraper._prefix + link
                )
                print(f"  ✅ Year={year}, Distance={distance}km")
            except Exception as e:
                print(f"  ❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error with men's data: {e}")

    print("\n" + "=" * 60)

    # Test women's data - check all links since there are only 3
    print("\n📊 Testing Women's Tour de France - All links...")
    print("-" * 40)

    try:
        women_scraper = Scraper(history_page="https://www.letourfemmes.fr/en/history")
        print(f"Total links found: {len(women_scraper._links)}")

        # Test all links
        for i, link in enumerate(women_scraper._links):
            print(f"\nTesting link {i}: {women_scraper._prefix + link}")
            try:
                soup, year, distance = women_scraper._get_soup_year_distance(
                    women_scraper._prefix + link
                )
                print(f"  ✅ Year={year}, Distance={distance}km")
            except Exception as e:
                print(f"  ❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error with women's data: {e}")

    print("\n" + "=" * 60)
    print("🔍 Link order analysis completed.")


if __name__ == "__main__":
    asyncio.run(test_recent_links())
