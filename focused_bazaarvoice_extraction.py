#!/usr/bin/env python3
"""
Focused Bazaarvoice Review Extraction
Specifically targets Bazaarvoice review content to extract the individual reviews like Greg's review about return policy.
"""

import time
import json
import re
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
    """Configure and return Chrome WebDriver with extended timeouts"""
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
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)

    return driver


def wait_for_bazaarvoice_load(driver, timeout=20):
    """Wait specifically for Bazaarvoice content to fully load"""
    print("Waiting for Bazaarvoice content to load...")
    wait = WebDriverWait(driver, timeout)

    try:
        # First, wait for any Bazaarvoice container
        bazaarvoice_containers = [
            "[data-bv-show='reviews']",
            ".bv-content-container",
            ".bv-content-reviews",
            ".bv-content-reviews-container",
            "[data-bv-product-id]"
        ]

        container_found = False
        for selector in bazaarvoice_containers:
            try:
                element = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)))
                print(f"Found Bazaarvoice container: {selector}")
                container_found = True
                break
            except TimeoutException:
                continue

        if not container_found:
            print("No Bazaarvoice container found")
            return False

        # Wait for actual review content (not just the container)
        print("Waiting for review content to load...")
        time.sleep(8)  # Give extra time for dynamic content

        return True

    except Exception as e:
        print(f"Error waiting for Bazaarvoice: {e}")
        return False


def extract_rating_summary(driver):
    """Extract rating summary with specific focus on the format we expect"""
    print("Extracting rating summary...")
    summary = {}

    try:
        # Look for the specific text pattern we found
        page_text = driver.page_source

        # Pattern for "X.X out of 5 stars, average rating value. Read X Reviews"
        rating_pattern = r'(\d+\.\d+)\s+out\s+of\s+5\s+stars.*?Read\s+(\d+)\s+Reviews?'
        rating_match = re.search(rating_pattern, page_text, re.IGNORECASE)

        if rating_match:
            summary['rating'] = float(rating_match.group(1))
            summary['review_count'] = int(rating_match.group(2))
            print(
                f"Found rating: {summary['rating']} stars with {summary['review_count']} reviews")

        # Alternative pattern for "X.X (Y)" format
        alt_pattern = r'(\d+\.\d+)\s*\((\d+)\)'
        alt_match = re.search(alt_pattern, page_text)

        if alt_match and not rating_match:
            summary['rating'] = float(alt_match.group(1))
            summary['review_count'] = int(alt_match.group(2))
            print(
                f"Found alternative format: {summary['rating']} ({summary['review_count']})")

    except Exception as e:
        print(f"Error extracting rating summary: {e}")

    return summary


def click_reviews_to_load(driver):
    """Click on reviews section to trigger loading of review content"""
    print("Attempting to click reviews section to load content...")

    clickable_elements = [
        "[data-bv-show='reviews']",
        ".bv-content-summary-body-text",
        ".bv_numReviews_text",
        "[class*='review']",
        "a[href*='review']"
    ]

    for selector in clickable_elements:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        print(f"Clicking element: {selector}")
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                        return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def extract_bazaarvoice_reviews(driver):
    """Extract individual reviews from Bazaarvoice system"""
    print("Extracting Bazaarvoice reviews...")
    reviews = []

    try:
        # Scroll down to trigger more content loading
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Look for Bazaarvoice review containers
        bv_selectors = [
            ".bv-content-review",
            ".bv-content-item",
            "[data-bv-show='review']",
            ".BVRRContainer .BVRRReviewDisplay",
            ".bv-content-reviews .bv-content-item"
        ]

        review_elements = []
        for selector in bv_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    review_elements.extend(elements)
                    print(
                        f"Found {len(elements)} reviews with selector: {selector}")
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue

        if not review_elements:
            print("No review elements found, searching in page source...")
            # Search for review content in page source
            page_source = driver.page_source

            # Look for patterns that match review content
            review_patterns = [
                r'Bike Return Policy.*?Greg.*?Verified Purchaser.*?(\d+)\s+days?\s+ago',
                r'(\d+)\s+out\s+of\s+5\s+stars.*?Greg.*?Verified Purchaser',
                r'Greg.*?Verified Purchaser.*?(\d+)\s+days?\s+ago.*?policy'
            ]

            for pattern in review_patterns:
                matches = re.findall(pattern, page_source,
                                     re.IGNORECASE | re.DOTALL)
                if matches:
                    print(f"Found review pattern: {pattern}")
                    reviews.append({
                        'method': 'regex_extraction',
                        'pattern': pattern,
                        'matches': matches,
                        'found': True
                    })

        # Extract from found elements
        for i, element in enumerate(review_elements[:10]):  # Limit to first 10
            try:
                review_data = {}

                # Get text content
                text_content = element.get_attribute(
                    'textContent') or element.text
                if text_content and len(text_content.strip()) > 50:
                    review_data['index'] = i
                    review_data['text'] = text_content.strip()

                    # Look for specific review components
                    try:
                        # Rating
                        rating_elem = element.find_element(
                            By.CSS_SELECTOR, "[class*='rating'], [class*='star']")
                        if rating_elem:
                            review_data['rating_text'] = rating_elem.get_attribute(
                                'textContent')
                    except:
                        pass

                    try:
                        # Author
                        author_elem = element.find_element(
                            By.CSS_SELECTOR, "[class*='author'], [class*='name'], .bv-content-author")
                        if author_elem:
                            review_data['author'] = author_elem.get_attribute(
                                'textContent')
                    except:
                        pass

                    try:
                        # Date
                        date_elem = element.find_element(
                            By.CSS_SELECTOR, "[class*='date'], [class*='time'], .bv-content-datetime")
                        if date_elem:
                            review_data['date'] = date_elem.get_attribute(
                                'textContent')
                    except:
                        pass

                    # Check if this looks like Greg's review
                    if 'greg' in text_content.lower() and 'policy' in text_content.lower():
                        review_data['is_greg_review'] = True
                        print(f"Found Greg's review! Index: {i}")

                    reviews.append(review_data)

            except StaleElementReferenceException:
                print(f"Stale element at index {i}")
                continue
            except Exception as e:
                print(f"Error extracting review {i}: {e}")
                continue

    except Exception as e:
        print(f"Error in extract_bazaarvoice_reviews: {e}")

    return reviews


def search_for_greg_review_in_source(driver):
    """Search specifically for Greg's review in page source"""
    print("Searching for Greg's review in page source...")

    try:
        page_source = driver.page_source

        # Search for Greg's review specifically
        greg_patterns = [
            r'(Bike Return Policy.*?Greg.*?Verified Purchaser.*?[\d\w\s]{1,200}policy)',
            r'(Greg.*?Verified Purchaser.*?[\d\w\s]{1,200}policy.*?Canadian tire)',
            r'(1 out of 5 stars.*?Bike Return Policy.*?Greg)',
        ]

        found_reviews = []
        for pattern in greg_patterns:
            matches = re.findall(pattern, page_source,
                                 re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    found_reviews.append({
                        'pattern_used': pattern,
                        'content': match.strip()[:500],  # First 500 chars
                        'method': 'source_search'
                    })
                    print(f"Found Greg's review with pattern!")

        return found_reviews

    except Exception as e:
        print(f"Error searching for Greg's review: {e}")
        return []


def extract_reviews_focused():
    """Main function focused on extracting the specific reviews we're looking for"""
    target_url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    print("=== Focused Bazaarvoice Review Extraction ===")
    print(f"Target URL: {target_url}")
    print("Looking specifically for Greg's review about return policy...")
    print("=" * 50)

    driver = setup_driver()
    results = {
        'url': target_url,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'success': False,
        'rating_summary': {},
        'reviews': [],
        'greg_search_results': [],
        'errors': []
    }

    try:
        print("Loading product page...")
        driver.get(target_url)
        time.sleep(5)

        print("Scrolling to reviews section...")
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)

        print("Waiting for Bazaarvoice to load...")
        bv_loaded = wait_for_bazaarvoice_load(driver)

        if bv_loaded:
            print("Clicking to load review content...")
            click_reviews_to_load(driver)
            time.sleep(5)

        # Extract rating summary
        summary = extract_rating_summary(driver)
        results['rating_summary'] = summary

        # Extract reviews
        reviews = extract_bazaarvoice_reviews(driver)
        results['reviews'] = reviews

        # Search specifically for Greg's review
        greg_results = search_for_greg_review_in_source(driver)
        results['greg_search_results'] = greg_results

        # Save page source for analysis
        with open('focused_review_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        if summary or reviews or greg_results:
            results['success'] = True
            print(f"\n✅ SUCCESS!")
            print(
                f"Rating: {summary.get('rating', 'N/A')} ({summary.get('review_count', 'N/A')} reviews)")
            print(f"Reviews found: {len(reviews)}")
            print(f"Greg search results: {len(greg_results)}")
        else:
            print("\n❌ No content found")

    except Exception as e:
        error_msg = f"Execution error: {e}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)

    finally:
        driver.quit()

    # Save results
    with open('focused_review_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to 'focused_review_results.json'")
    print(f"📁 Page source saved to 'focused_review_debug.html'")

    return results


if __name__ == "__main__":
    results = extract_reviews_focused()

    print("\n" + "="*50)
    print("FOCUSED EXTRACTION SUMMARY:")
    print("="*50)

    if results['rating_summary']:
        rating = results['rating_summary'].get('rating', 'N/A')
        count = results['rating_summary'].get('review_count', 'N/A')
        print(f"Rating Summary: {rating} stars ({count} reviews)")

    if results['reviews']:
        print(f"Reviews extracted: {len(results['reviews'])}")
        greg_reviews = [r for r in results['reviews']
                        if r.get('is_greg_review')]
        if greg_reviews:
            print(f"Greg's review found in extracted reviews: YES")
        else:
            print(f"Greg's review found in extracted reviews: NO")

    if results['greg_search_results']:
        print(
            f"Greg's review found in source search: YES ({len(results['greg_search_results'])} matches)")
    else:
        print(f"Greg's review found in source search: NO")

    print(f"Success: {results['success']}")
    print(f"Errors: {len(results.get('errors', []))}")

    if results['success']:
        print("\n🎉 We have review extraction capability!")
    else:
        print("\n⚠️  Need to refine extraction method.")
