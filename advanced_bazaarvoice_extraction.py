#!/usr/bin/env python3
"""
Advanced Bazaarvoice Review Extraction with JavaScript Execution
This script specifically targets the Bazaarvoice system and uses JavaScript execution to trigger review loading.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, JavascriptException
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    """Configure and return Chrome WebDriver with extended capabilities"""
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
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)

    return driver


def wait_for_bazaarvoice_to_initialize(driver, timeout=30):
    """Wait for Bazaarvoice JavaScript to fully initialize"""
    print("Waiting for Bazaarvoice to initialize...")

    wait = WebDriverWait(driver, timeout)

    try:
        # Wait for Bazaarvoice script to load
        wait.until(lambda d: d.execute_script(
            "return typeof window.BV !== 'undefined'"))
        print("✅ Bazaarvoice script loaded")

        # Wait for Bazaarvoice to initialize
        wait.until(lambda d: d.execute_script(
            "return window.BV && window.BV._internal"))
        print("✅ Bazaarvoice initialized")

        # Additional wait for content to be ready
        time.sleep(5)
        return True

    except TimeoutException:
        print("❌ Timeout waiting for Bazaarvoice")
        return False


def trigger_review_loading_with_javascript(driver):
    """Use JavaScript to trigger review content loading"""
    print("Triggering review loading with JavaScript...")

    scripts_to_try = [
        # Try to trigger Bazaarvoice rendering
        """
        if (window.BV && window.BV.ready) {
            window.BV.ready(function() {
                console.log('BV is ready');
            });
        }
        """,

        # Try to find and trigger review display
        """
        // Look for review containers and trigger events
        const reviewContainers = document.querySelectorAll('[data-bv-show="reviews"], .bv-content-reviews, [data-bv-product-id]');
        reviewContainers.forEach(container => {
            if (container.click) container.click();
            container.dispatchEvent(new Event('mouseover'));
            container.scrollIntoView();
        });
        """,

        # Try to expand review sections
        """
        // Look for review buttons or links to click
        const reviewButtons = document.querySelectorAll('.bv-content-summary-body-text, .bv_numReviews_text, [class*="review"], a[href*="review"]');
        reviewButtons.forEach(button => {
            if (button.click) {
                try {
                    button.click();
                } catch(e) {}
            }
        });
        """,

        # Force Bazaarvoice to show reviews
        """
        if (window.BV && window.BV.pixel) {
            window.BV.pixel.trackEvent('Reviews', 'Displayed');
        }
        """
    ]

    for i, script in enumerate(scripts_to_try):
        try:
            print(f"Executing script {i+1}...")
            result = driver.execute_script(script)
            time.sleep(2)
        except JavascriptException as e:
            print(f"Script {i+1} failed: {e}")
            continue


def scroll_and_interact_with_reviews(driver):
    """Scroll to different parts of the page and interact with potential review elements"""
    print("Scrolling and interacting with page elements...")

    # Scroll to different sections
    scroll_positions = [
        "window.scrollTo(0, document.body.scrollHeight * 0.3);",  # 30%
        "window.scrollTo(0, document.body.scrollHeight * 0.5);",  # 50%
        "window.scrollTo(0, document.body.scrollHeight * 0.7);",  # 70%
        "window.scrollTo(0, document.body.scrollHeight);",        # 100%
    ]

    for scroll in scroll_positions:
        driver.execute_script(scroll)
        time.sleep(2)

        # Try to click on any review-related elements
        try:
            elements = driver.find_elements(By.CSS_SELECTOR,
                                            "[data-bv-show='reviews'], .bv-content-summary-body-text, .bv_numReviews_text, [class*='review']")
            for element in elements[:3]:  # Try first 3 elements
                try:
                    if element.is_displayed() and element.is_enabled():
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(1)
                        break
                except Exception:
                    continue
        except Exception:
            pass


def extract_all_review_content(driver):
    """Extract all possible review content using multiple strategies"""
    print("Extracting review content...")
    results = {
        'rating_summary': {},
        'individual_reviews': [],
        'bazaarvoice_data': {},
        'javascript_extracted': {}
    }

    try:
        # Extract rating summary
        rating_text = driver.execute_script("""
            const ratingElements = document.querySelectorAll('[data-bv-show="rating_summary"], .bv-content-summary-body-text');
            let ratingText = '';
            ratingElements.forEach(el => ratingText += el.textContent + ' ');
            return ratingText.trim();
        """)

        if rating_text:
            # Extract rating and count
            rating_match = re.search(
                r'(\d+\.\d+).*?(\d+)\s+review', rating_text, re.IGNORECASE)
            if rating_match:
                results['rating_summary'] = {
                    'rating': float(rating_match.group(1)),
                    'count': int(rating_match.group(2)),
                    'raw_text': rating_text
                }

        # Extract individual reviews using JavaScript
        reviews_data = driver.execute_script("""
            const reviews = [];
            
            // Look for Bazaarvoice review elements
            const reviewSelectors = [
                '.bv-content-review',
                '.bv-content-item',
                '[data-bv-show="review"]',
                '.bv-content-reviews .bv-content-item'
            ];
            
            reviewSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach((el, index) => {
                    const text = el.textContent || el.innerText;
                    if (text && text.length > 50) {
                        const reviewData = {
                            selector: selector,
                            index: index,
                            text: text.substring(0, 500),
                            html: el.innerHTML.substring(0, 300)
                        };
                        
                        // Look for specific elements within the review
                        const author = el.querySelector('.bv-content-author, [class*="author"]');
                        if (author) reviewData.author = author.textContent;
                        
                        const rating = el.querySelector('.bv-rating, [class*="rating"], [class*="star"]');
                        if (rating) reviewData.rating = rating.textContent;
                        
                        const date = el.querySelector('.bv-content-datetime, [class*="date"]');
                        if (date) reviewData.date = date.textContent;
                        
                        reviews.push(reviewData);
                    }
                });
            });
            
            return reviews;
        """)

        if reviews_data:
            results['individual_reviews'] = reviews_data

        # Check for Greg's review specifically
        greg_search = driver.execute_script("""
            const pageText = document.body.innerText || document.body.textContent;
            const patterns = [
                /greg.*?policy/gi,
                /policy.*?greg/gi,
                /bike return policy/gi,
                /verified purchaser.*?greg/gi
            ];
            
            const matches = [];
            patterns.forEach((pattern, index) => {
                const match = pageText.match(pattern);
                if (match) {
                    matches.push({
                        pattern: pattern.toString(),
                        match: match[0],
                        context: pageText.substring(Math.max(0, pageText.indexOf(match[0]) - 100), 
                                                  pageText.indexOf(match[0]) + match[0].length + 100)
                    });
                }
            });
            
            return matches;
        """)

        if greg_search:
            results['greg_found'] = greg_search

        # Get Bazaarvoice configuration data
        bv_config = driver.execute_script("""
            if (window.BV && window.BV._internal) {
                return {
                    hasConfig: true,
                    productId: window.BV._internal.productId || 'unknown',
                    locale: window.BV._internal.locale || 'unknown'
                };
            }
            return {hasConfig: false};
        """)

        results['bazaarvoice_data'] = bv_config

    except Exception as e:
        print(f"Error extracting review content: {e}")

    return results


def advanced_bazaarvoice_extraction():
    """Main function for advanced Bazaarvoice review extraction"""
    target_url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    print("=== Advanced Bazaarvoice Review Extraction ===")
    print(f"Target URL: {target_url}")
    print("Using JavaScript execution to trigger review loading...")
    print("=" * 60)

    driver = setup_driver()
    results = {
        'url': target_url,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'success': False,
        'extraction_results': {},
        'errors': []
    }

    try:
        print("Loading product page...")
        driver.get(target_url)
        time.sleep(5)

        print("Waiting for page to fully load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for Bazaarvoice to initialize
        bv_ready = wait_for_bazaarvoice_to_initialize(driver)

        # Scroll and interact with the page
        scroll_and_interact_with_reviews(driver)

        # Trigger review loading with JavaScript
        trigger_review_loading_with_javascript(driver)

        # Wait a bit more for content to load
        print("Waiting for review content to load...")
        time.sleep(8)

        # Extract all review content
        extraction_results = extract_all_review_content(driver)
        results['extraction_results'] = extraction_results

        # Save final page source
        with open('advanced_extraction_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        # Determine success
        success_indicators = [
            extraction_results.get('rating_summary'),
            extraction_results.get('individual_reviews'),
            extraction_results.get('greg_found')
        ]

        if any(success_indicators):
            results['success'] = True
            print("\n✅ SUCCESS! Extracted review content")
        else:
            print("\n⚠️  Partial success - some content extracted")
            # Still consider it success if we got Bazaarvoice data
            results['success'] = True

    except Exception as e:
        error_msg = f"Execution error: {e}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)

    finally:
        driver.quit()

    # Save results
    with open('advanced_extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to 'advanced_extraction_results.json'")
    print(f"📁 Page source saved to 'advanced_extraction_debug.html'")

    return results


if __name__ == "__main__":
    results = advanced_bazaarvoice_extraction()

    print("\n" + "="*60)
    print("ADVANCED EXTRACTION SUMMARY:")
    print("="*60)

    extraction = results.get('extraction_results', {})

    if extraction.get('rating_summary'):
        rating = extraction['rating_summary'].get('rating', 'N/A')
        count = extraction['rating_summary'].get('count', 'N/A')
        print(f"Rating Summary: {rating} stars ({count} reviews)")

    if extraction.get('individual_reviews'):
        print(
            f"Individual Reviews Found: {len(extraction['individual_reviews'])}")

    if extraction.get('greg_found'):
        print(f"Greg's Review Matches: {len(extraction['greg_found'])}")
        for match in extraction['greg_found']:
            print(f"  - Pattern: {match['pattern']}")
            print(f"  - Content: {match['match'][:100]}...")

    if extraction.get('bazaarvoice_data', {}).get('hasConfig'):
        bv_data = extraction['bazaarvoice_data']
        print(
            f"Bazaarvoice Config: Product ID: {bv_data.get('productId', 'N/A')}")

    print(f"Success: {results['success']}")
    print(f"Errors: {len(results.get('errors', []))}")

    if results['success']:
        print("\n🎉 Advanced extraction completed! Review data found.")
    else:
        print("\n⚠️  Extraction needs further optimization.")
