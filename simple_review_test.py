import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def simple_test():
    """Simple test to check if we can click on review count"""
    url = "https://www.canadiantire.ca/en/pdp/supercycle-reaction-hardtail-mountain-bike-for-all-ages-26-in-black-0710110p.html?rq=bikes"

    # Setup driver
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(5)

        # Look for review count and try to click it
        js_script = """
            const pageText = document.body.innerText;
            console.log("Page loaded, looking for review count...");
            
            // Look for patterns like "4.1 (11)" or "Read 11 Reviews"
            const reviewPatterns = [
                /\\(\\d+\\)/g,           // (11)
                /Read\\s+\\d+\\s+Reviews/gi,  // Read 11 Reviews
                /\\d+\\.\\d+.*\\(\\d+\\)/g     // 4.1 (11)
            ];
            
            let found = [];
            for (let pattern of reviewPatterns) {
                const matches = pageText.match(pattern);
                if (matches) {
                    found.push(...matches);
                }
            }
            
            // Try to find clickable elements
            const allElements = document.querySelectorAll('*');
            let clickableReviewElements = [];
            
            for (let element of allElements) {
                const text = element.textContent;
                if (text && (text.includes('(') && text.includes(')') && /\\d/.test(text) && text.includes('star'))) {
                    clickableReviewElements.push({
                        tag: element.tagName,
                        text: text.substring(0, 100),
                        clickable: element.tagName === 'A' || element.onclick !== null || element.style.cursor === 'pointer'
                    });
                }
            }
            
            return {
                foundPatterns: found,
                clickableElements: clickableReviewElements.slice(0, 5) // First 5
            };
        """

        result = driver.execute_script(js_script)

        print("Found patterns:", result['foundPatterns'])
        print("Clickable elements:", len(result['clickableElements']))

        for i, elem in enumerate(result['clickableElements']):
            print(
                f"  {i+1}. {elem['tag']}: {elem['text']} (clickable: {elem['clickable']})")

        # Try to click on the specific Bazaarvoice review count element
        click_script = """
            // Look for the specific Bazaarvoice element you found
            console.log('Looking for bv_numReviews_text element...');
            
            // Method 1: Direct class selector
            let reviewElement = document.querySelector('.bv_numReviews_text');
            if (reviewElement && reviewElement.textContent.includes('(11)')) {
                console.log('Found bv_numReviews_text element:', reviewElement.textContent);
                
                // Click the parent button element
                let button = reviewElement.closest('button');
                if (button) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    
                    // Wait a moment for scroll, then click
                    setTimeout(() => {
                        button.click();
                        console.log('Clicked button, now scrolling down to load reviews...');
                        
                        // Scroll down to trigger review loading
                        setTimeout(() => {
                            window.scrollBy(0, 500);
                            setTimeout(() => {
                                window.scrollBy(0, 500);
                            }, 1000);
                        }, 1000);
                    }, 1000);
                    
                    return 'Clicked button and initiated scroll: ' + reviewElement.textContent;
                } else {
                    // Try clicking the element itself
                    reviewElement.click();
                    return 'Clicked bv_numReviews_text directly: ' + reviewElement.textContent;
                }
            }
            
            // Method 2: Look for the button within the specific path you found
            const productWrapper = document.querySelector('#nl-product-information-wrapper');
            if (productWrapper) {
                const reviewButton = productWrapper.querySelector('div.nl-product-details-wrapper div.nl-product-card__reviews button');
                if (reviewButton) {
                    console.log('Found review button via path');
                    reviewButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    
                    setTimeout(() => {
                        reviewButton.click();
                        // Scroll down after click
                        setTimeout(() => {
                            window.scrollBy(0, 800);
                        }, 1500);
                    }, 1000);
                    
                    return 'Clicked review button via specific path and scrolled';
                }
            }
            
            // Method 3: Look for any button containing (11)
            const buttons = document.querySelectorAll('button');
            for (let button of buttons) {
                if (button.textContent && button.textContent.includes('(11)')) {
                    console.log('Found button with (11):', button.textContent.substring(0, 50));
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    
                    setTimeout(() => {
                        button.click();
                        // Scroll to trigger content loading
                        setTimeout(() => {
                            window.scrollBy(0, 600);
                        }, 1000);
                    }, 800);
                    
                    return 'Clicked button containing (11) and scrolled: ' + button.textContent.substring(0, 50);
                }
            }
            
            return 'Could not find the specific bv_numReviews_text element or button';
        """

        click_result = driver.execute_script(click_script)
        print(f"Click result: {click_result}")

        # Wait longer and check multiple times for content changes
        print("Waiting for reviews section to load...")
        for i in range(15):  # Check 15 times over 22.5 seconds
            time.sleep(1.5)

            # Check if reviews section appeared
            check_script = """
                const newText = document.body.innerText.toLowerCase();
                const hasContent = {
                    hasFilterReviews: newText.includes('filter reviews') || newText.includes('filter by'),
                    hasVerifiedPurchaser: newText.includes('verified purchaser') || newText.includes('verified'),
                    hasDaysAgo: newText.includes('days ago') || newText.includes('weeks ago') || newText.includes('months ago'),
                    hasSort: newText.includes('sort by') || newText.includes('most recent') || newText.includes('oldest'),
                    hasHelpful: newText.includes('helpful') || newText.includes('was this review helpful'),
                    hasReviewText: newText.includes('review text') || newText.includes('reviewer') || newText.includes('reviewed'),
                    hasStars: newText.includes('out of 5 stars') && newText.includes('review'),
                    hasShowMore: newText.includes('show more') || newText.includes('read more') || newText.includes('see all'),
                    hasReviewPagination: newText.includes('1 – 5 of') || newText.includes('reviews') && newText.includes('of'),
                    hasBazaarvoice: newText.includes('bazaarvoice') || newText.includes('bv-'),
                    textLength: newText.length,
                    hasGreg: newText.includes('greg'),
                    hasIndividualReviews: false
                };
                
                // Look for individual review patterns
                const lines = newText.split('\\n');
                for (let line of lines) {
                    if (line.includes('reviewed') || 
                        (line.includes('ago') && (line.includes('day') || line.includes('week') || line.includes('month'))) ||
                        line.includes('verified purchaser')) {
                        hasContent.hasIndividualReviews = true;
                        break;
                    }
                }
                
                // Look for any review-related content that might have appeared
                const reviewIndicators = hasContent.hasFilterReviews || hasContent.hasVerifiedPurchaser || 
                                       hasContent.hasDaysAgo || hasContent.hasSort || hasContent.hasHelpful ||
                                       hasContent.hasReviewText || hasContent.hasShowMore || 
                                       hasContent.hasReviewPagination || hasContent.hasIndividualReviews;
                
                return {
                    ...hasContent,
                    hasAnyReviewContent: reviewIndicators
                };
            """

            check_result = driver.execute_script(check_script)

            if check_result['hasAnyReviewContent']:
                print(f"✅ Reviews section loaded after {(i+1)*1.5} seconds!")
                print("Review indicators found:", {
                      k: v for k, v in check_result.items() if k != 'textLength' and v})

                if check_result['hasGreg']:
                    print("🎯 Found Greg in the reviews!")

                # Try to extract some review content
                extract_script = """
                    const text = document.body.innerText;
                    const lines = text.split('\\n');
                    let reviewLines = [];
                    
                    // Look for review-related content
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (line && (
                            line.toLowerCase().includes('greg') ||
                            line.includes('days ago') || line.includes('weeks ago') ||
                            line.includes('Verified Purchaser') ||
                            line.includes('out of 5 stars') ||
                            (line.includes('★') || line.includes('⭐')) ||
                            line.includes('return policy') ||
                            line.includes('Helpful')
                        )) {
                            // Also add context lines
                            if (i > 0) reviewLines.push('↳ ' + lines[i-1].trim());
                            reviewLines.push('→ ' + line);
                            if (i < lines.length - 1) reviewLines.push('↳ ' + lines[i+1].trim());
                        }
                    }
                    
                    return reviewLines.slice(0, 20); // First 20 relevant lines
                """

                review_content = driver.execute_script(extract_script)
                print("\n📝 Review content found:")
                for line in review_content:
                    if line.strip():
                        print(f"  {line}")

                break
            else:
                print(
                    f"  Checking {i+1}/10... Text length: {check_result['textLength']}")

        final_check = check_result
        print("After click check:", final_check)

        if final_check['hasFilterReviews'] or final_check['hasVerifiedPurchaser']:
            print("🎉 SUCCESS! Reviews section seems to have loaded!")
        else:
            print("❌ Reviews section did not load")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    simple_test()
