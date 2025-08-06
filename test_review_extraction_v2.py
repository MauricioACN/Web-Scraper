#!/usr/bin/env python3
"""
Test script to validate review extraction with pagination
"""

import json
from review_scraper import setup_driver, click_on_review_count, wait_for_reviews_section_to_load, handle_review_pagination


def test_single_product_reviews():
    """Test review extraction on the specific product"""
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()

    try:
        print(f"🌐 Loading: {url}")
        driver.get(url)

        # Wait for page to load
        import time
        time.sleep(5)

        # Step 1: Click on review count to open reviews
        print("\n📍 Step 1: Opening reviews section...")
        if not click_on_review_count(driver):
            print("❌ Failed to open reviews section")
            return

        # Step 2: Wait for reviews to load
        print("\n📍 Step 2: Waiting for reviews to load...")
        if not wait_for_reviews_section_to_load(driver):
            print("❌ Reviews section didn't load properly")
            return

        # Step 3: Extract all reviews with pagination
        print("\n📍 Step 3: Extracting all reviews with pagination...")
        all_reviews = handle_review_pagination(driver, max_pages=15)

        # Results summary
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print(f"   Total reviews extracted: {len(all_reviews)}")

        if all_reviews:
            # Show structure of first review for debugging
            print(f"\n🔍 REVIEW STRUCTURE:")
            if all_reviews:
                first_review = all_reviews[0]
                print(f"   Keys: {list(first_review.keys())}")
                print(f"   Sample: {first_review}")

            # Show sample reviews
            print(f"\n📝 SAMPLE REVIEWS:")
            for i, review in enumerate(all_reviews[:5]):
                reviewer = review.get('author') or review.get(
                    'reviewer') or 'Unknown'
                rating = review.get('rating') or 0
                date = review.get('date') or 'Unknown date'
                title = review.get('title') or 'No title'
                verified = review.get('isVerifiedPurchaser') or review.get(
                    'verified_purchaser') or False

                print(f"   {i+1}. {reviewer} - {rating}/5 stars - {date}")
                print(f"      Title: {title}")
                if verified:
                    print(f"      ✓ Verified Purchaser")
                print(
                    f"      Content: {review.get('content', review.get('body', ''))[:100]}...")
                print()

            # Search for Greg specifically
            greg_reviews = []
            return_policy_reviews = []

            for review in all_reviews:
                reviewer = review.get('author') or review.get('reviewer') or ''
                content = review.get('content') or review.get('body') or ''

                if 'greg' in reviewer.lower():
                    greg_reviews.append(review)

                if 'return' in content.lower() and 'policy' in content.lower():
                    return_policy_reviews.append(review)

            print(f"🔍 SEARCH RESULTS:")
            print(f"   Reviews by Greg: {len(greg_reviews)}")
            print(
                f"   Reviews mentioning return policy: {len(return_policy_reviews)}")

            if greg_reviews:
                print(f"\n🎯 GREG'S REVIEWS:")
                for review in greg_reviews:
                    reviewer = review.get('author') or review.get(
                        'reviewer') or 'Unknown'
                    rating = review.get('rating') or 0
                    date = review.get('date') or 'Unknown date'
                    content = review.get('content') or review.get('body') or ''

                    print(f"   Author: {reviewer}")
                    print(f"   Rating: {rating}/5")
                    print(f"   Date: {date}")
                    print(f"   Content: {content}")
                    print()

            if return_policy_reviews:
                print(f"\n📋 RETURN POLICY MENTIONS:")
                for review in return_policy_reviews:
                    reviewer = review.get('author') or review.get(
                        'reviewer') or 'Unknown'
                    rating = review.get('rating') or 0
                    content = review.get('content') or review.get('body') or ''

                    print(f"   Author: {reviewer}")
                    print(f"   Rating: {rating}/5")
                    print(f"   Content: {content[:200]}...")
                    print()

            # Save results
            with open('test_reviews_extraction.json', 'w', encoding='utf-8') as f:
                json.dump(all_reviews, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to 'test_reviews_extraction.json'")

        else:
            print("❌ No reviews extracted")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_single_product_reviews()
