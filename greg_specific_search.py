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


def scroll_and_find_reviews_section(driver):
    """Scroll down and look for reviews section."""
    print("🔍 Scrolling to find reviews section...")

    # Try multiple scroll positions to find reviews
    scroll_positions = [0.5, 0.6, 0.7, 0.8, 0.9]

    for position in scroll_positions:
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight * {position});")
        time.sleep(2)

        # Look for review-related text in viewport
        js_check = """
            const viewportText = window.getSelection().toString() || document.body.innerText;
            const lowerText = viewportText.toLowerCase();
            
            return {
                hasReviewKeywords: lowerText.includes('review') || lowerText.includes('customer'),
                hasRatingText: lowerText.includes('stars') || lowerText.includes('rating'),
                visibleText: viewportText.substring(0, 500)
            };
        """

        result = driver.execute_script(js_check)
        print(
            f"📍 Position {position}: Review keywords={result['hasReviewKeywords']}, Rating text={result['hasRatingText']}")

        if result['hasReviewKeywords'] and result['hasRatingText']:
            print(f"🎯 Found reviews section at position {position}")
            return True

    return False


def click_to_expand_reviews(driver):
    """Try to click on review-related elements to expand them."""
    print("👆 Attempting to click and expand reviews...")

    # Possible selectors for review links/buttons
    review_selectors = [
        "a[href*='review']",
        "button[data-bv*='review']",
        "a[data-bv*='review']",
        "a:contains('Read')",
        "a:contains('Review')",
        "button:contains('Review')",
        "[data-bv-show='reviews']",
        ".bv-content-review-display-toggle",
        ".review-toggle",
        ".reviews-link",
        "a[href*='#reviews']"
    ]

    clicked_elements = []

    for selector in review_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements[:3]:  # Try first 3 matches
                try:
                    if element.is_displayed() and element.is_enabled():
                        # Scroll to element first
                        driver.execute_script(
                            "arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)

                        # Try clicking
                        element.click()
                        clicked_elements.append(selector)
                        print(f"✅ Clicked element: {selector}")
                        time.sleep(2)
                        break
                except Exception as e:
                    print(f"⚠️ Could not click {selector}: {e}")
                    continue
        except Exception as e:
            print(f"⚠️ Error with selector {selector}: {e}")
            continue

    # Also try JavaScript click on review links
    js_click = """
        const reviewLinks = document.querySelectorAll('a, button');
        let clicked = [];
        
        for (let link of reviewLinks) {
            const text = link.textContent.toLowerCase();
            const href = link.href || '';
            
            if (text.includes('review') || text.includes('read') || href.includes('review')) {
                try {
                    link.click();
                    clicked.push(text.substring(0, 50));
                    break; // Only click first one
                } catch (e) {
                    continue;
                }
            }
        }
        
        return clicked;
    """

    js_clicked = driver.execute_script(js_click)
    if js_clicked:
        print(f"✅ JavaScript clicked: {js_clicked}")
        clicked_elements.extend(js_clicked)

    return clicked_elements


def extract_reviews_after_expansion(driver):
    """Extract reviews after potentially expanding them."""
    print("📝 Extracting reviews after expansion...")

    # Wait a bit for any dynamic content to load
    time.sleep(3)

    # Get page text and search for review patterns
    js_extraction = """
        const pageText = document.body.innerText;
        const lines = pageText.split('\\n');
        
        let reviews = [];
        let foundGreg = false;
        let gregContext = '';
        
        // Look for Greg specifically
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].toLowerCase();
            if (line.includes('greg')) {
                foundGreg = true;
                // Get context around Greg mention
                const start = Math.max(0, i - 3);
                const end = Math.min(lines.length, i + 4);
                gregContext = lines.slice(start, end).join('\\n');
                break;
            }
        }
        
        // Look for review patterns
        const reviewPatterns = [
            /([A-Z][a-z]+)\\s*(?:says?|wrote|reviewed?).*?([1-5](?:\\.[0-9])?)[^\\n]*(?:star|out of)/gi,
            /By\\s+([A-Z][a-z]+).*?([1-5](?:\\.[0-9])?)[^\\n]*star/gi,
            /([A-Z][a-z]+).*?([1-5](?:\\.[0-9])?)[^\\n]*out of 5/gi
        ];
        
        for (let pattern of reviewPatterns) {
            let match;
            while ((match = pattern.exec(pageText)) !== null) {
                if (match[1] && match[2]) {
                    reviews.push({
                        author: match[1],
                        rating: parseFloat(match[2]),
                        context: match[0]
                    });
                }
            }
        }
        
        // Also search for return policy mentions
        const returnPolicyMentions = [];
        const returnPattern = /([^\\n]*return[^\\n]*policy[^\\n]*)/gi;
        let returnMatch;
        while ((returnMatch = returnPattern.exec(pageText)) !== null) {
            returnPolicyMentions.push(returnMatch[1]);
        }
        
        return {
            foundGreg: foundGreg,
            gregContext: gregContext,
            reviews: reviews,
            returnPolicyMentions: returnPolicyMentions,
            totalLines: lines.length
        };
    """

    result = driver.execute_script(js_extraction)
    print(
        f"📊 Extraction results: Found Greg={result['foundGreg']}, Reviews={len(result['reviews'])}, Return mentions={len(result['returnPolicyMentions'])}")

    return result


def simulate_show_more_reviews(driver):
    """Try to find and click 'Show more' or pagination for reviews."""
    print("📄 Looking for 'Show more' or pagination...")

    # Common "show more" selectors
    show_more_selectors = [
        "button:contains('Show more')",
        "button:contains('Load more')",
        "a:contains('Show more')",
        "a:contains('Load more')",
        ".show-more",
        ".load-more",
        ".pagination a",
        ".bv-content-pagination a",
        "[data-bv*='show']",
        "[data-bv*='load']",
        "[data-bv*='more']"
    ]

    clicked_something = False

    for selector in show_more_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    print(f"✅ Clicked show more: {selector}")
                    clicked_something = True
                    time.sleep(3)
                    break
        except Exception as e:
            continue

    # JavaScript approach for show more
    js_show_more = """
        const buttons = document.querySelectorAll('button, a');
        for (let btn of buttons) {
            const text = btn.textContent.toLowerCase();
            if (text.includes('show') && text.includes('more') || 
                text.includes('load') && text.includes('more') ||
                text.includes('view') && text.includes('all')) {
                try {
                    btn.click();
                    return true;
                } catch (e) {
                    continue;
                }
            }
        }
        return false;
    """

    js_result = driver.execute_script(js_show_more)
    if js_result:
        print("✅ JavaScript clicked show more")
        clicked_something = True
        time.sleep(3)

    return clicked_something


def main():
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()
    results = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "extraction_results": {
            "greg_found": False,
            "greg_context": "",
            "reviews": [],
            "return_policy_mentions": [],
            "actions_taken": []
        },
        "errors": []
    }

    try:
        print(f"🌐 Loading URL: {url}")
        driver.get(url)
        time.sleep(5)

        actions_taken = []

        # Step 1: Scroll to find reviews
        found_reviews_section = scroll_and_find_reviews_section(driver)
        actions_taken.append(f"scroll_to_reviews: {found_reviews_section}")

        # Step 2: Try clicking to expand reviews
        clicked_elements = click_to_expand_reviews(driver)
        actions_taken.append(f"clicked_elements: {clicked_elements}")

        # Step 3: Try show more/pagination
        show_more_clicked = simulate_show_more_reviews(driver)
        actions_taken.append(f"show_more_clicked: {show_more_clicked}")

        # Step 4: Extract reviews after all attempts
        extraction_result = extract_reviews_after_expansion(driver)

        # Store results
        results["extraction_results"]["greg_found"] = extraction_result["foundGreg"]
        results["extraction_results"]["greg_context"] = extraction_result["gregContext"]
        results["extraction_results"]["reviews"] = extraction_result["reviews"]
        results["extraction_results"]["return_policy_mentions"] = extraction_result["returnPolicyMentions"]
        results["extraction_results"]["actions_taken"] = actions_taken

        if extraction_result["foundGreg"] or len(extraction_result["reviews"]) > 0:
            results["success"] = True
            print("✅ SUCCESS! Found review content")
        else:
            print("⚠️ No Greg or substantial reviews found")

    except Exception as e:
        error_msg = f"Error during extraction: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    finally:
        driver.quit()

    # Save results
    output_file = "greg_search_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📁 Results saved to {output_file}")

    # Print summary
    if results["success"]:
        greg_found = results["extraction_results"]["greg_found"]
        reviews_count = len(results["extraction_results"]["reviews"])
        return_mentions = len(
            results["extraction_results"]["return_policy_mentions"])

        print(f"📊 Summary:")
        print(f"   Greg found: {greg_found}")
        print(f"   Reviews extracted: {reviews_count}")
        print(f"   Return policy mentions: {return_mentions}")

        if greg_found:
            print(
                f"   Greg context: {results['extraction_results']['greg_context'][:200]}...")


if __name__ == "__main__":
    main()
