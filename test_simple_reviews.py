#!/usr/bin/env python3
"""
Simple test script to validate review extraction
"""

import json
from review_scraper import setup_driver, click_on_review_count, wait_for_reviews_section_to_load, handle_review_pagination


def test_simple_reviews():
    """Simple test for review extraction"""
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()

    try:
        print(f"🌐 Loading: {url}")
        driver.get(url)

        import time
        time.sleep(5)

        print("\n📍 Step 1: Opening reviews section...")
        if not click_on_review_count(driver):
            print("❌ Failed to open reviews section")
            return

        print("\n📍 Step 2: Waiting for reviews to load...")
        if not wait_for_reviews_section_to_load(driver):
            print("❌ Reviews section didn't load properly")
            return

        print("\n📍 Step 3: Extracting all reviews with pagination...")
        all_reviews = handle_review_pagination(driver, max_pages=15)

        print(f"\n🎉 EXTRACTION COMPLETE!")
        print(f"   Total reviews extracted: {len(all_reviews)}")

        if all_reviews:
            print(f"\n🔍 REVIEW STRUCTURE:")
            first_review = all_reviews[0]
            print(f"   Keys: {list(first_review.keys())}")
            print(f"   Sample: {first_review}")
            print(
                f"   Product URL: {first_review.get('product_url', 'Not available')}")

            # Save to file
            with open('simple_reviews_extraction.json', 'w', encoding='utf-8') as f:
                json.dump(all_reviews, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to 'simple_reviews_extraction.json'")

            # Simple search for Greg
            print(f"\n🔍 SEARCHING FOR GREG:")
            for i, review in enumerate(all_reviews):
                author = str(review.get('author', ''))
                if 'greg' in author.lower():
                    print(f"   Found Greg at position {i+1}")
                    print(f"   Author: {author}")
                    print(f"   Rating: {review.get('rating', 'N/A')}")
                    print(
                        f"   Product URL: {review.get('product_url', 'N/A')}")
                    print(f"   Content: {review.get('content', 'N/A')}")
                    print(f"   Title: {review.get('title', 'N/A')}")

        else:
            print("❌ No reviews extracted")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()


if __name__ == "__main__":
    test_simple_reviews()
