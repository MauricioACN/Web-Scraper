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


def comprehensive_page_analysis(driver):
    """Do a comprehensive analysis of all page content."""
    print("🔍 Comprehensive page analysis...")

    # Get all text content from the page
    analysis_script = """
        let analysis = {
            pageText: document.body.innerText,
            pageHTML: document.documentElement.innerHTML,
            gregMentions: [],
            returnPolicyMentions: [],
            allNames: [],
            reviewStructures: [],
            potentialReviews: []
        };
        
        // Search for Greg in all text
        const pageText = document.body.innerText.toLowerCase();
        const gregRegex = /greg/gi;
        let match;
        let offset = 0;
        while ((match = gregRegex.exec(pageText)) !== null) {
            const start = Math.max(0, match.index - 100);
            const end = Math.min(pageText.length, match.index + 100);
            analysis.gregMentions.push({
                position: match.index,
                context: pageText.substring(start, end)
            });
        }
        
        // Search for return policy mentions
        const returnTerms = ['return policy', 'return', 'refund', 'exchange'];
        for (let term of returnTerms) {
            const regex = new RegExp(term, 'gi');
            let termMatch;
            while ((termMatch = regex.exec(pageText)) !== null) {
                const start = Math.max(0, termMatch.index - 50);
                const end = Math.min(pageText.length, termMatch.index + 50);
                analysis.returnPolicyMentions.push({
                    term: term,
                    position: termMatch.index,
                    context: pageText.substring(start, end)
                });
            }
        }
        
        // Look for names in the text (capitalized words that could be names)
        const nameRegex = /\\b[A-Z][a-z]{2,}\\b/g;
        let nameMatch;
        while ((nameMatch = nameRegex.exec(document.body.innerText)) !== null) {
            if (nameMatch[0].length >= 3 && nameMatch[0].length <= 15) {
                analysis.allNames.push(nameMatch[0]);
            }
        }
        
        // Remove duplicates from names
        analysis.allNames = [...new Set(analysis.allNames)];
        
        // Look for review-like structures in DOM
        const reviewSelectors = [
            '*[class*="review"]',
            '*[data-review]',
            '*[class*="comment"]', 
            '*[class*="feedback"]',
            '*[class*="testimonial"]',
            '*[id*="review"]'
        ];
        
        for (let selector of reviewSelectors) {
            try {
                const elements = document.querySelectorAll(selector);
                for (let element of elements) {
                    if (element.textContent && element.textContent.length > 20) {
                        analysis.reviewStructures.push({
                            selector: selector,
                            text: element.textContent.substring(0, 200),
                            innerHTML: element.innerHTML.substring(0, 200)
                        });
                    }
                }
            } catch (e) {
                // Skip invalid selectors
            }
        }
        
        // Look for potential review patterns in text
        const reviewPatterns = [
            /\\b[A-Z][a-z]+\\s+(?:says?|wrote|posted|reviewed?)[:,.]?\\s*[\\s\\S]{10,200}/gi,
            /By\\s+[A-Z][a-z]+[\\s\\S]{10,200}/gi,
            /[A-Z][a-z]+\\s*[-–—]\\s*[\\s\\S]{10,200}/gi
        ];
        
        for (let pattern of reviewPatterns) {
            let patternMatch;
            while ((patternMatch = pattern.exec(document.body.innerText)) !== null) {
                analysis.potentialReviews.push({
                    pattern: pattern.toString(),
                    match: patternMatch[0].substring(0, 300)
                });
            }
        }
        
        return analysis;
    """

    result = driver.execute_script(analysis_script)

    # Print summary
    print(f"📊 Analysis Summary:")
    print(f"   Greg mentions: {len(result['gregMentions'])}")
    print(f"   Return policy mentions: {len(result['returnPolicyMentions'])}")
    print(f"   All names found: {len(result['allNames'])}")
    print(f"   Review structures: {len(result['reviewStructures'])}")
    print(f"   Potential reviews: {len(result['potentialReviews'])}")

    # Show some names found
    if result['allNames']:
        print(f"   Sample names: {result['allNames'][:10]}")

    return result


def scroll_through_entire_page(driver):
    """Scroll through the entire page slowly to trigger any lazy loading."""
    print("📜 Scrolling through entire page...")

    # Get initial page height
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll in increments
    scroll_pause_time = 2
    scroll_increment = 300

    current_position = 0
    max_scrolls = 20  # Prevent infinite scrolling
    scroll_count = 0

    while scroll_count < max_scrolls:
        # Scroll down by increment
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        time.sleep(scroll_pause_time)

        current_position += scroll_increment

        # Check if we've reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        if current_position >= new_height:
            break

        scroll_count += 1

    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    print(f"📜 Completed {scroll_count} scroll increments")
    return scroll_count


def check_for_dynamic_content(driver):
    """Check if any content loaded dynamically during scrolling."""
    print("🔄 Checking for dynamic content...")

    # Check for AJAX requests or dynamic loading indicators
    dynamic_check = """
        return {
            hasSpinners: document.querySelectorAll('[class*="loading"], [class*="spinner"]').length,
            hasLazyElements: document.querySelectorAll('[data-lazy], [loading="lazy"]').length,
            totalElements: document.querySelectorAll('*').length,
            textLength: document.body.innerText.length
        };
    """

    initial_state = driver.execute_script(dynamic_check)

    # Wait a bit
    time.sleep(5)

    final_state = driver.execute_script(dynamic_check)

    print(f"🔄 Dynamic content check:")
    print(
        f"   Elements: {initial_state['totalElements']} → {final_state['totalElements']}")
    print(
        f"   Text length: {initial_state['textLength']} → {final_state['textLength']}")

    return {
        'initial': initial_state,
        'final': final_state,
        'content_changed': final_state['textLength'] != initial_state['textLength']
    }


def save_full_page_content(driver, filename="full_page_content.txt"):
    """Save the full page content for manual review."""
    print(f"💾 Saving full page content to {filename}...")

    try:
        full_text = driver.execute_script("return document.body.innerText;")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"✅ Saved {len(full_text)} characters to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving page content: {e}")
        return False


def main():
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    driver = setup_driver()
    results = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "comprehensive_analysis": {},
        "dynamic_content_check": {},
        "actions_taken": [],
        "errors": []
    }

    try:
        print(f"🌐 Loading URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Step 1: Scroll through entire page
        scroll_count = scroll_through_entire_page(driver)
        results["actions_taken"].append(f"scrolled_{scroll_count}_times")

        # Step 2: Check for dynamic content
        dynamic_check = check_for_dynamic_content(driver)
        results["dynamic_content_check"] = dynamic_check

        # Step 3: Comprehensive analysis
        analysis = comprehensive_page_analysis(driver)
        results["comprehensive_analysis"] = analysis

        # Step 4: Save full page content
        content_saved = save_full_page_content(driver)
        results["actions_taken"].append(f"content_saved: {content_saved}")

        # Determine success
        greg_found = len(analysis['gregMentions']) > 0
        has_content = len(analysis['allNames']) > 0 or len(
            analysis['potentialReviews']) > 0

        if greg_found or has_content:
            results["success"] = True
            print("✅ SUCCESS! Found relevant content")
        else:
            print("⚠️ No Greg or substantial review content found")

    except Exception as e:
        error_msg = f"Error during comprehensive analysis: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    finally:
        driver.quit()

    # Save results
    output_file = "comprehensive_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📁 Results saved to {output_file}")

    # Print final summary
    if results["success"]:
        analysis = results["comprehensive_analysis"]
        greg_mentions = len(analysis.get("gregMentions", []))
        names_found = len(analysis.get("allNames", []))
        potential_reviews = len(analysis.get("potentialReviews", []))

        print(f"📊 Final Summary:")
        print(f"   Greg mentions: {greg_mentions}")
        print(f"   Total names found: {names_found}")
        print(f"   Potential reviews: {potential_reviews}")

        if greg_mentions > 0:
            print(f"   🎯 GREG FOUND! Check the results file for context.")


if __name__ == "__main__":
    main()
