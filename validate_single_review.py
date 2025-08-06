#!/usr/bin/env python3
"""
Single Product Review Validation Script
Tests if we can extract reviews from a specific Canadian Tire product using scroll and click interactions.
Target: https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes
Expected: 11 reviews, 4.1 rating, first review from Greg about return policy
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    """Configure and return Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def scroll_to_reviews_section(driver):
    """Scroll to the reviews section of the page"""
    try:
        # Look for reviews section indicators
        review_selectors = [
            "div[data-bv-show='reviews']",
            ".nl-reviews__list",
            ".nl-product-card__reviews",
            "[id*='reviews']",
            "[class*='review']",
            ".bv-content-container"
        ]

        for selector in review_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    print(f"Found reviews section with selector: {selector}")
                    driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(3)
                    return element
            except NoSuchElementException:
                continue

        # If no specific review section found, scroll down to trigger loading
        print("No specific review section found, scrolling down...")
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        return None

    except Exception as e:
        print(f"Error scrolling to reviews: {e}")
        return None


def wait_for_reviews_to_load(driver, timeout=15):
    """Wait for reviews to load dynamically"""
    print("Waiting for reviews to load...")

    # Wait for Bazaarvoice content to load
    wait = WebDriverWait(driver, timeout)

    try:
        # Wait for any review content indicators
        review_indicators = [
            ".bv-content-reviews",
            ".bv-content-reviews-container",
            ".bv-content-item",
            ".nl-reviews__list",
            "[data-bv-show='reviews']",
            ".bv-content-summary-body-text"
        ]

        for indicator in review_indicators:
            try:
                element = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, indicator)))
                print(f"Reviews loaded! Found indicator: {indicator}")
                time.sleep(2)  # Extra wait for full content loading
                return True
            except TimeoutException:
                continue

        print("No review indicators found, checking for any review content...")
        time.sleep(5)  # Give more time for dynamic loading
        return False

    except Exception as e:
        print(f"Error waiting for reviews: {e}")
        return False


def extract_review_summary(driver):
    """Extract overall review summary (rating, count)"""
    summary = {}

    try:
        # Look for rating and review count
        rating_selectors = [
            ".bv-rating-stars-container .bv-rating-stars-filled",
            ".bv-content-summary-body-text",
            "[class*='rating']",
            "[data-bv-show='rating']"
        ]

        count_selectors = [
            ".bv-content-summary-body-text",
            "[class*='review-count']",
            "[data-bv-show='reviews']"
        ]

        # Try to find rating
        for selector in rating_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.get_attribute('textContent') or element.text
                    if text and any(char.isdigit() for char in text):
                        summary['rating_element'] = text.strip()
                        print(f"Found rating element: {text.strip()}")
                        break
                if 'rating_element' in summary:
                    break
            except Exception:
                continue

        # Try to find review count
        for selector in count_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.get_attribute('textContent') or element.text
                    if text and 'review' in text.lower():
                        summary['count_element'] = text.strip()
                        print(f"Found count element: {text.strip()}")
                        break
                if 'count_element' in summary:
                    break
            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting summary: {e}")

    return summary


def extract_individual_reviews(driver):
    """Extract individual review content"""
    reviews = []

    try:
        # Look for review containers
        review_container_selectors = [
            ".bv-content-item",
            ".bv-content-review",
            "[data-bv-show='review']",
            ".nl-reviews__list .review-item",
            ".review-container",
            "[class*='review-item']"
        ]

        review_containers = []
        for selector in review_container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    review_containers.extend(elements)
                    print(
                        f"Found {len(elements)} review containers with selector: {selector}")
            except Exception:
                continue

        if not review_containers:
            print("No review containers found, looking for any review-like content...")
            # Look for any divs that might contain review content
            all_divs = driver.find_elements(By.TAG_NAME, "div")
            for div in all_divs:
                text = div.get_attribute('textContent') or div.text
                if text and len(text) > 50 and any(word in text.lower() for word in ['review', 'stars', 'verified', 'helpful']):
                    review_containers.append(div)

        print(f"Total review containers found: {len(review_containers)}")

        # Extract data from each container
        # Limit to first 5 for testing
        for i, container in enumerate(review_containers[:5]):
            try:
                review_data = {}
                text_content = container.get_attribute(
                    'textContent') or container.text

                if text_content and len(text_content.strip()) > 20:
                    review_data['container_index'] = i
                    review_data['raw_text'] = text_content.strip()[
                        :500]  # First 500 chars
                    review_data['html_snippet'] = container.get_attribute(
                        'innerHTML')[:300] if container.get_attribute('innerHTML') else None

                    # Look for specific review elements within container
                    try:
                        # Rating
                        rating_elements = container.find_elements(
                            By.CSS_SELECTOR, "[class*='star'], [class*='rating']")
                        if rating_elements:
                            review_data['rating_found'] = True

                        # Author
                        author_elements = container.find_elements(
                            By.CSS_SELECTOR, "[class*='author'], [class*='name'], [class*='user']")
                        if author_elements:
                            review_data['author_found'] = True

                        # Date
                        date_elements = container.find_elements(
                            By.CSS_SELECTOR, "[class*='date'], [class*='time']")
                        if date_elements:
                            review_data['date_found'] = True

                    except Exception as inner_e:
                        review_data['extraction_error'] = str(inner_e)

                    reviews.append(review_data)
                    print(f"Extracted review {i+1}: {text_content[:100]}...")

            except StaleElementReferenceException:
                print(f"Stale element at index {i}, skipping...")
                continue
            except Exception as e:
                print(f"Error extracting review {i}: {e}")
                continue

    except Exception as e:
        print(f"Error in extract_individual_reviews: {e}")

    return reviews


def check_for_load_more_button(driver):
    """Check if there's a 'Load More' or pagination button"""
    load_more_selectors = [
        ".bv-content-btn-pages-load-more",
        "[class*='load-more']",
        "[class*='show-more']",
        ".bv-content-pagination",
        "button[class*='more']",
        "a[class*='more']"
    ]

    for selector in load_more_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"Found load more button: {selector}")
                        return element
        except Exception:
            continue

    return None


def validate_single_product_reviews():
    """Main function to validate review extraction from a single product"""
    target_url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    print("=== Canadian Tire Single Product Review Validation ===")
    print(f"Target URL: {target_url}")
    print("Expected: 11 reviews, 4.1 rating, first review from Greg about return policy")
    print("=" * 60)

    driver = setup_driver()
    results = {
        'url': target_url,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'success': False,
        'summary': {},
        'reviews': [],
        'errors': []
    }

    try:
        print("Loading product page...")
        driver.get(target_url)
        time.sleep(5)

        print("Page loaded, looking for reviews...")

        # Step 1: Scroll to reviews section
        reviews_section = scroll_to_reviews_section(driver)

        # Step 2: Wait for reviews to load
        reviews_loaded = wait_for_reviews_to_load(driver)

        # Step 3: Extract review summary
        print("Extracting review summary...")
        summary = extract_review_summary(driver)
        results['summary'] = summary

        # Step 4: Extract individual reviews
        print("Extracting individual reviews...")
        reviews = extract_individual_reviews(driver)
        results['reviews'] = reviews

        # Step 5: Check for load more functionality
        load_more_btn = check_for_load_more_button(driver)
        if load_more_btn:
            print("Found load more button, attempting to click...")
            try:
                driver.execute_script("arguments[0].click();", load_more_btn)
                time.sleep(3)
                additional_reviews = extract_individual_reviews(driver)
                results['additional_reviews'] = additional_reviews
            except Exception as e:
                print(f"Error clicking load more: {e}")

        # Step 6: Save page source for debugging
        with open('single_product_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        if reviews or summary:
            results['success'] = True
            print(f"\n✅ SUCCESS! Found {len(reviews)} review containers")
            if summary:
                print(f"Summary data: {summary}")
        else:
            print("\n❌ No reviews or summary found")

    except Exception as e:
        error_msg = f"Main execution error: {e}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)

    finally:
        driver.quit()

    # Save results
    with open('single_review_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to 'single_review_validation_results.json'")
    print(f"📁 Page source saved to 'single_product_debug.html'")

    return results


if __name__ == "__main__":
    results = validate_single_product_reviews()

    print("\n" + "="*60)
    print("VALIDATION SUMMARY:")
    print("="*60)
    print(f"Success: {results['success']}")
    print(f"Reviews found: {len(results.get('reviews', []))}")
    print(f"Summary data: {'Yes' if results.get('summary') else 'No'}")
    print(f"Errors: {len(results.get('errors', []))}")

    if results['success']:
        print("\n🎉 Validation successful! We can proceed with review extraction.")
    else:
        print("\n⚠️  Validation failed. Need to investigate further.")
