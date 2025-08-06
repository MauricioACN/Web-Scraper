import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
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

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def find_and_click_reviews_tab(driver):
    """Find and click on the Reviews tab or link."""
    print("🔍 Looking for Reviews tab/link...")

    # Possible selectors for reviews tab
    review_tab_selectors = [
        "a[href*='#reviews']",
        "button[aria-controls*='review']",
        "*[id*='review'][role='tab']",
        "a:contains('Reviews')",
        "button:contains('Reviews')",
        "a:contains('Ratings')",
        ".tab:contains('Review')",
        "[data-tab='reviews']",
        "[aria-label*='Review']"
    ]

    # JavaScript to find and click review-related elements
    js_click_reviews = """
        let clicked = false;
        let clickedElement = null;
        
        // Method 1: Look for "Read X Reviews" links
        const allElements = document.querySelectorAll('a, button, div, span');
        for (let element of allElements) {
            const text = element.textContent;
            if (text && (text.includes('Read') && text.includes('Review')) || 
                       (text.includes('Ratings') && text.includes('Review'))) {
                try {
                    element.click();
                    clicked = true;
                    clickedElement = text.substring(0, 100);
                    break;
                } catch (e) {
                    continue;
                }
            }
        }
        
        // Method 2: Look for tabs with review-related content
        if (!clicked) {
            const tabs = document.querySelectorAll('[role="tab"], .tab, [data-tab]');
            for (let tab of tabs) {
                const text = tab.textContent.toLowerCase();
                if (text.includes('review') || text.includes('rating')) {
                    try {
                        tab.click();
                        clicked = true;
                        clickedElement = tab.textContent.substring(0, 100);
                        break;
                    } catch (e) {
                        continue;
                    }
                }
            }
        }
        
        // Method 3: Look for elements with review-related IDs or classes
        if (!clicked) {
            const reviewElements = document.querySelectorAll('[id*="review"], [class*="review"], [data-bv*="review"]');
            for (let element of reviewElements) {
                if (element.tagName === 'A' || element.tagName === 'BUTTON') {
                    try {
                        element.click();
                        clicked = true;
                        clickedElement = element.outerHTML.substring(0, 100);
                        break;
                    } catch (e) {
                        continue;
                    }
                }
            }
        }
        
        return {
            clicked: clicked,
            elementClicked: clickedElement
        };
    """

    result = driver.execute_script(js_click_reviews)

    if result['clicked']:
        print(f"✅ Clicked reviews element: {result['elementClicked']}")
        time.sleep(5)  # Wait for content to load
        return True
    else:
        print("⚠️ No reviews element found to click")
        return False


def wait_for_reviews_to_load(driver, timeout=15):
    """Wait for review content to appear."""
    print("⏳ Waiting for reviews to load...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check if review content appeared
        check_script = """
            const pageText = document.body.innerText.toLowerCase();
            return {
                hasMoreReviewContent: pageText.length > 20000,
                hasReviewText: pageText.includes('reviewer') || pageText.includes('customer') || pageText.includes('purchase'),
                hasNames: /\\b[A-Z][a-z]{3,}\\s+(?:says|wrote|posted|reviewed?)/i.test(document.body.innerText),
                pageLength: pageText.length
            };
        """

        result = driver.execute_script(check_script)

        if result['hasNames'] or (result['hasMoreReviewContent'] and result['hasReviewText']):
            print(f"✅ Reviews loaded! Page length: {result['pageLength']}")
            return True

        time.sleep(1)

    print("⚠️ Timeout waiting for reviews to load")
    return False


def extract_all_reviews_content(driver):
    """Extract all review content after reviews are loaded."""
    print("📖 Extracting all review content...")

    extraction_script = """
        const pageText = document.body.innerText;
        
        let analysis = {
            gregFound: false,
            gregMentions: [],
            reviewerNames: [],
            reviewTexts: [],
            returnPolicyMentions: []
        };
        
        // Search for Greg (case insensitive)
        const gregRegex = /greg/gi;
        let match;
        while ((match = gregRegex.exec(pageText)) !== null) {
            analysis.gregFound = true;
            const start = Math.max(0, match.index - 200);
            const end = Math.min(pageText.length, match.index + 200);
            analysis.gregMentions.push({
                position: match.index,
                context: pageText.substring(start, end)
            });
        }
        
        // Search for reviewer names (patterns like "John says:", "By Mary", etc.)
        const reviewerPatterns = [
            /\\b([A-Z][a-z]{2,15})\\s+(?:says?|wrote|posted|reviewed?):/gi,
            /By\\s+([A-Z][a-z]{2,15})\\b/gi,
            /([A-Z][a-z]{2,15})\\s*[-–—]\\s*\\d/gi,
            /Reviewer:\\s*([A-Z][a-z]{2,15})/gi
        ];
        
        for (let pattern of reviewerPatterns) {
            let match;
            while ((match = pattern.exec(pageText)) !== null) {
                if (match[1] && match[1].length >= 3 && match[1].length <= 15) {
                    analysis.reviewerNames.push({
                        name: match[1],
                        context: match[0],
                        fullContext: pageText.substring(Math.max(0, match.index - 100), Math.min(pageText.length, match.index + 300))
                    });
                }
            }
        }
        
        // Look for return policy mentions
        const returnTerms = ['return policy', 'return', 'refund', 'exchange', 'warranty'];
        for (let term of returnTerms) {
            const regex = new RegExp(term, 'gi');
            let termMatch;
            while ((termMatch = regex.exec(pageText)) !== null) {
                analysis.returnPolicyMentions.push({
                    term: term,
                    position: termMatch.index,
                    context: pageText.substring(Math.max(0, termMatch.index - 100), Math.min(pageText.length, termMatch.index + 100))
                });
            }
        }
        
        // Remove duplicates from reviewer names
        const uniqueNames = {};
        analysis.reviewerNames = analysis.reviewerNames.filter(item => {
            if (uniqueNames[item.name]) {
                return false;
            }
            uniqueNames[item.name] = true;
            return true;
        });
        
        return analysis;
    """

    result = driver.execute_script(extraction_script)

    print(f"📊 Extraction results:")
    print(f"   Greg found: {result['gregFound']}")
    print(f"   Greg mentions: {len(result['gregMentions'])}")
    print(f"   Reviewer names found: {len(result['reviewerNames'])}")
    print(f"   Return policy mentions: {len(result['returnPolicyMentions'])}")

    if result['reviewerNames']:
        names = [item['name'] for item in result['reviewerNames'][:10]]
        print(f"   Sample reviewer names: {names}")

    return result


def main():
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()
    results = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "greg_found": False,
        "greg_mentions": [],
        "reviewer_names": [],
        "return_policy_mentions": [],
        "actions_taken": [],
        "errors": []
    }

    try:
        print(f"🌐 Loading URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Step 1: Try to click on reviews tab/link
        reviews_clicked = find_and_click_reviews_tab(driver)
        results["actions_taken"].append(
            f"reviews_tab_clicked: {reviews_clicked}")

        # Step 2: Wait for reviews to load
        if reviews_clicked:
            reviews_loaded = wait_for_reviews_to_load(driver)
            results["actions_taken"].append(
                f"reviews_loaded: {reviews_loaded}")

        # Step 3: Extract all review content
        extraction = extract_all_reviews_content(driver)

        results["greg_found"] = extraction["gregFound"]
        results["greg_mentions"] = extraction["gregMentions"]
        results["reviewer_names"] = extraction["reviewerNames"]
        results["return_policy_mentions"] = extraction["returnPolicyMentions"]

        # Save full page content after clicking reviews
        full_text = driver.execute_script("return document.body.innerText;")
        with open("full_reviews_page_content.txt", 'w', encoding='utf-8') as f:
            f.write(full_text)

        results["actions_taken"].append("saved_full_reviews_content")

        if extraction["gregFound"] or len(extraction["reviewerNames"]) > 0:
            results["success"] = True
            print("✅ SUCCESS! Found review content")
        else:
            print("⚠️ No Greg or reviewer names found")

    except Exception as e:
        error_msg = f"Error during final review extraction: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    finally:
        driver.quit()

    # Save results
    output_file = "final_review_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📁 Results saved to {output_file}")

    # Print final summary
    if results["success"]:
        print(f"📊 Final Summary:")
        print(f"   🎯 Greg found: {results['greg_found']}")
        print(f"   👥 Reviewer names: {len(results['reviewer_names'])}")
        print(
            f"   🔄 Return policy mentions: {len(results['return_policy_mentions'])}")

        if results["greg_found"]:
            print(f"   🎉 GREG FOUND! Check the results for his context.")
            for mention in results["greg_mentions"]:
                print(f"      Context: {mention['context'][:150]}...")


if __name__ == "__main__":
    main()
