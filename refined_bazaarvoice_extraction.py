import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re


def setup_driver():
    """Configure Chrome driver for testing."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Use webdriver-manager to get the correct ChromeDriver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for_bazaarvoice_complete(driver, timeout=30):
    """Wait for Bazaarvoice to fully load and initialize."""
    print("🔄 Waiting for Bazaarvoice to fully initialize...")

    try:
        # Wait for the basic Bazaarvoice object to exist
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return typeof BV !== 'undefined'")
        )
        print("✅ Bazaarvoice object detected")

        # Wait a bit for initialization
        time.sleep(3)

        # Check if reviews are loaded
        bv_status = driver.execute_script("""
            return {
                bvExists: typeof BV !== 'undefined',
                configExists: typeof BV.configure !== 'undefined',
                hasRatingData: document.querySelector('[data-bv-show="rating_summary"]') !== null,
                hasReviewContainer: document.querySelector('[data-bv-show="reviews"]') !== null
            };
        """)

        print(f"📊 Bazaarvoice status: {bv_status}")
        return True

    except TimeoutException:
        print("⚠️ Bazaarvoice initialization timeout")
        return False


def trigger_review_display(driver):
    """Trigger review display using JavaScript and scrolling."""
    print("🎯 Triggering review display...")

    # First scroll to reviews area
    try:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(2)
    except:
        pass

    # Try to find and trigger review display
    js_script = """
        // Try multiple approaches to show reviews
        let triggered = false;
        
        // Method 1: Look for review link/button and click it
        const reviewLinks = document.querySelectorAll('a[href*="review"], button[data-bv*="review"], [data-bv-show*="review"]');
        for (let link of reviewLinks) {
            if (link.textContent.includes('review') || link.textContent.includes('Review')) {
                link.click();
                triggered = true;
                break;
            }
        }
        
        // Method 2: Try Bazaarvoice API if available
        if (typeof BV !== 'undefined' && !triggered) {
            try {
                if (BV.ui && BV.ui.showReviews) {
                    BV.ui.showReviews();
                    triggered = true;
                }
            } catch (e) {
                console.log('BV API method failed:', e);
            }
        }
        
        // Method 3: Check if reviews container exists but is hidden, try to show it
        const reviewsContainer = document.querySelector('[data-bv-show="reviews"]');
        if (reviewsContainer && !triggered) {
            reviewsContainer.style.display = 'block';
            reviewsContainer.style.visibility = 'visible';
            triggered = true;
        }
        
        return {
            triggered: triggered,
            foundLinks: reviewLinks.length,
            hasReviewsContainer: !!reviewsContainer
        };
    """

    result = driver.execute_script(js_script)
    print(f"📋 Review trigger result: {result}")

    # Wait a bit for any triggered actions to take effect
    time.sleep(3)

    return result


def extract_rating_with_text_selectors(driver):
    """Extract rating information using more specific text-based selectors."""
    print("⭐ Extracting rating data with refined selectors...")

    js_script = """
        let ratingData = {
            rating: null,
            count: null,
            text_content: null
        };
        
        // Look for rating text patterns
        const allText = document.body.innerText;
        
        // Pattern 1: "4.4 out of 5 stars" or "4.4/5"
        const ratingMatch = allText.match(/(\\d+\\.\\d+)\\s*(?:out of|\\/)\\s*(?:5|5\\.0)\\s*(?:stars?)?/i);
        if (ratingMatch) {
            ratingData.rating = parseFloat(ratingMatch[1]);
        }
        
        // Pattern 2: Look for review count - "7 reviews" or "Based on 7 reviews"
        const countMatch = allText.match(/(?:based on\\s+)?(\\d+)\\s+reviews?/i);
        if (countMatch) {
            ratingData.count = parseInt(countMatch[1]);
        }
        
        // Try to get text from specific Bazaarvoice elements
        const ratingElement = document.querySelector('[data-bv-show="rating_summary"]');
        if (ratingElement) {
            ratingData.text_content = ratingElement.innerText || ratingElement.textContent;
        }
        
        // Alternative: look for schema.org microdata
        const ratingMeta = document.querySelector('[itemprop="ratingValue"]');
        if (ratingMeta && !ratingData.rating) {
            ratingData.rating = parseFloat(ratingMeta.content || ratingMeta.textContent);
        }
        
        const countMeta = document.querySelector('[itemprop="reviewCount"]');
        if (countMeta && !ratingData.count) {
            ratingData.count = parseInt(countMeta.content || countMeta.textContent);
        }
        
        return ratingData;
    """

    result = driver.execute_script(js_script)
    print(f"📊 Extracted rating data: {result}")
    return result


def extract_individual_reviews(driver):
    """Extract individual review content."""
    print("💬 Extracting individual reviews...")

    js_script = """
        let reviews = [];
        
        // Look for various review selectors
        const reviewSelectors = [
            '[data-bv-show="reviews"] .bv-content-review',
            '.bv-content-review',
            '.review-item',
            '.review',
            '[class*="review"]',
            '[data-review]'
        ];
        
        let reviewElements = [];
        for (let selector of reviewSelectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                reviewElements = elements;
                break;
            }
        }
        
        // If we found review elements, extract their content
        for (let element of reviewElements) {
            let review = {
                text: '',
                rating: null,
                author: '',
                date: ''
            };
            
            // Extract text content
            review.text = element.innerText || element.textContent || '';
            
            // Look for rating within the review
            const ratingEl = element.querySelector('[class*="rating"], [class*="star"]');
            if (ratingEl) {
                const ratingText = ratingEl.textContent;
                const ratingMatch = ratingText.match(/(\\d+(?:\\.\\d+)?)/);
                if (ratingMatch) {
                    review.rating = parseFloat(ratingMatch[1]);
                }
            }
            
            // Look for author
            const authorEl = element.querySelector('[class*="author"], [class*="reviewer"], [class*="name"]');
            if (authorEl) {
                review.author = authorEl.textContent.trim();
            }
            
            // Look for date
            const dateEl = element.querySelector('[class*="date"], [class*="time"]');
            if (dateEl) {
                review.date = dateEl.textContent.trim();
            }
            
            if (review.text.length > 10) {  // Only add substantial reviews
                reviews.push(review);
            }
        }
        
        return {
            reviews: reviews,
            searchedSelectors: reviewSelectors,
            foundElements: reviewElements.length
        };
    """

    result = driver.execute_script(js_script)
    print(f"💬 Found {len(result['reviews'])} reviews")
    return result


def search_for_greg_review(driver):
    """Search specifically for Greg's review about return policy."""
    print("🔍 Searching for Greg's review...")

    js_script = """
        const allText = document.body.innerText.toLowerCase();
        const pageSource = document.documentElement.innerHTML.toLowerCase();
        
        let gregFindings = {
            foundGreg: false,
            foundReturnPolicy: false,
            gregLocations: [],
            returnPolicyLocations: [],
            combinedFindings: []
        };
        
        // Search for "greg" in text
        if (allText.includes('greg')) {
            gregFindings.foundGreg = true;
            const gregIndex = allText.indexOf('greg');
            gregFindings.gregLocations.push({
                type: 'text',
                position: gregIndex,
                context: allText.substring(gregIndex - 50, gregIndex + 50)
            });
        }
        
        // Search for return policy mentions
        const returnPolicyTerms = ['return policy', 'return', 'policy', 'exchange'];
        for (let term of returnPolicyTerms) {
            if (allText.includes(term)) {
                gregFindings.foundReturnPolicy = true;
                const termIndex = allText.indexOf(term);
                gregFindings.returnPolicyLocations.push({
                    term: term,
                    position: termIndex,
                    context: allText.substring(termIndex - 50, termIndex + 50)
                });
            }
        }
        
        // Look for combined mentions
        const sentences = allText.split(/[.!?]/);
        for (let i = 0; i < sentences.length; i++) {
            const sentence = sentences[i];
            if (sentence.includes('greg') && (sentence.includes('return') || sentence.includes('policy'))) {
                gregFindings.combinedFindings.push(sentence.trim());
            }
        }
        
        return gregFindings;
    """

    result = driver.execute_script(js_script)
    print(f"🔍 Greg search results: {result}")
    return result


def main():
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()
    results = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "extraction_results": {
            "rating_summary": {},
            "individual_reviews": [],
            "greg_search": {},
            "bazaarvoice_status": {}
        },
        "errors": []
    }

    try:
        print(f"🌐 Loading URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Wait for Bazaarvoice to load
        bv_loaded = wait_for_bazaarvoice_complete(driver)
        results["extraction_results"]["bazaarvoice_status"]["loaded"] = bv_loaded

        # Trigger review display
        trigger_result = trigger_review_display(driver)
        results["extraction_results"]["bazaarvoice_status"]["trigger_result"] = trigger_result

        # Extract rating data with refined approach
        rating_data = extract_rating_with_text_selectors(driver)
        results["extraction_results"]["rating_summary"] = rating_data

        # Extract individual reviews
        reviews_data = extract_individual_reviews(driver)
        results["extraction_results"]["individual_reviews"] = reviews_data["reviews"]
        results["extraction_results"]["bazaarvoice_status"]["review_extraction"] = {
            "searched_selectors": reviews_data["searchedSelectors"],
            "found_elements": reviews_data["foundElements"]
        }

        # Search for Greg specifically
        greg_data = search_for_greg_review(driver)
        results["extraction_results"]["greg_search"] = greg_data

        # Check if we got meaningful data
        if rating_data["rating"] is not None or len(reviews_data["reviews"]) > 0:
            results["success"] = True
            print("✅ SUCCESS! Extracted review content")
        else:
            print("⚠️ No substantial review data extracted")

    except Exception as e:
        error_msg = f"Error during extraction: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    finally:
        driver.quit()

    # Save results
    output_file = "refined_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📁 Results saved to {output_file}")

    # Print summary
    if results["success"]:
        rating = results["extraction_results"]["rating_summary"].get("rating")
        count = results["extraction_results"]["rating_summary"].get("count")
        reviews = len(results["extraction_results"]["individual_reviews"])
        greg_found = results["extraction_results"]["greg_search"].get(
            "foundGreg", False)

        print(f"📊 Summary:")
        print(f"   Rating: {rating} stars")
        print(f"   Count: {count} reviews")
        print(f"   Individual reviews found: {reviews}")
        print(f"   Greg mentioned: {greg_found}")


if __name__ == "__main__":
    main()
