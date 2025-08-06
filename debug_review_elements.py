import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def debug_page_elements():
    """Debug to find the exact review elements"""
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

        # Find all elements that contain review-related text
        debug_script = """
            const allElements = document.querySelectorAll('*');
            let reviewElements = [];
            
            for (let element of allElements) {
                const text = element.textContent;
                
                // Look for elements containing our specific patterns
                if (text && (
                    (text.includes('4.1') && text.includes('(11)')) ||
                    (text.includes('Read') && text.includes('11') && text.includes('Reviews')) ||
                    text.includes('(11)') ||
                    (text.includes('stars') && text.includes('11'))
                )) {
                    // Only get direct elements, not huge containers
                    if (text.length < 500) {
                        reviewElements.push({
                            tag: element.tagName,
                            class: element.className,
                            id: element.id,
                            text: text.trim(),
                            isClickable: element.tagName === 'A' || element.onclick !== null || element.style.cursor === 'pointer' || element.getAttribute('role') === 'button',
                            hasHref: element.href || 'none',
                            parent: element.parentElement ? element.parentElement.tagName + (element.parentElement.className ? '.' + element.parentElement.className : '') : 'none'
                        });
                    }
                }
            }
            
            // Remove duplicates and sort by text length (shorter = more specific)
            const unique = reviewElements.filter((elem, index, self) => 
                index === self.findIndex(e => e.text === elem.text)
            ).sort((a, b) => a.text.length - b.text.length);
            
            return unique.slice(0, 10); // Top 10 most relevant
        """

        elements = driver.execute_script(debug_script)

        print(f"Found {len(elements)} relevant elements:")
        print("=" * 80)

        for i, elem in enumerate(elements):
            print(f"\n{i+1}. {elem['tag']} (clickable: {elem['isClickable']})")
            print(f"   Class: {elem['class']}")
            print(f"   ID: {elem['id']}")
            print(f"   Text: {elem['text']}")
            print(f"   Parent: {elem['parent']}")
            print(f"   Href: {elem['hasHref']}")

        # Now try to click on the most likely candidate
        print("\n" + "=" * 80)
        print("Attempting to click on most likely review element...")

        click_script = """
            // Strategy: Look for elements that are specifically clickable and contain review count
            const candidates = [];
            const allElements = document.querySelectorAll('*');
            
            for (let element of allElements) {
                const text = element.textContent;
                
                // Must contain review-related content and be short/specific
                if (text && text.length < 200 && (
                    (text.includes('4.1') && text.includes('(11)')) ||
                    (text.includes('Read') && text.includes('Reviews'))
                )) {
                    const isClickable = element.tagName === 'A' || 
                                      element.onclick !== null || 
                                      element.style.cursor === 'pointer' ||
                                      element.getAttribute('data-bv') ||
                                      element.getAttribute('role') === 'button';
                    
                    if (isClickable) {
                        candidates.push({
                            element: element,
                            text: text.trim(),
                            tag: element.tagName
                        });
                    }
                }
            }
            
            // Try to click the best candidate
            if (candidates.length > 0) {
                // Prefer 'A' tags, then others
                candidates.sort((a, b) => {
                    if (a.tag === 'A' && b.tag !== 'A') return -1;
                    if (b.tag === 'A' && a.tag !== 'A') return 1;
                    return a.text.length - b.text.length; // Shorter text preferred
                });
                
                const best = candidates[0];
                best.element.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                // Wait a moment then click
                setTimeout(() => {
                    best.element.click();
                }, 1000);
                
                return 'Clicked: ' + best.tag + ' - ' + best.text.substring(0, 100);
            } else {
                return 'No clickable review elements found';
            }
        """

        click_result = driver.execute_script(click_script)
        print(f"Click attempt: {click_result}")

        # Wait longer for any potential loading
        print("Waiting for reviews to load...")
        time.sleep(8)

        # Check if anything changed
        final_check = driver.execute_script("""
            const text = document.body.innerText.toLowerCase();
            const hasReviews = text.includes('filter reviews') || 
                             text.includes('verified purchaser') || 
                             text.includes('days ago') ||
                             text.includes('helpful') ||
                             text.includes('sort by');
            
            return {
                hasReviewIndicators: hasReviews,
                textLength: text.length,
                newContent: text.includes('filter') ? 'Found filter content' : 'No filter content'
            };
        """)

        print(f"Final check: {final_check}")

        if final_check['hasReviewIndicators']:
            print("🎉 SUCCESS! Reviews section loaded!")

            # Try to extract some review content
            reviews_script = """
                const text = document.body.innerText;
                const lines = text.split('\\n');
                let reviewLines = [];
                
                for (let line of lines) {
                    if (line.includes('greg') || line.includes('Greg') ||
                        line.includes('days ago') || line.includes('weeks ago') ||
                        line.includes('Verified Purchaser')) {
                        reviewLines.push(line.trim());
                    }
                }
                
                return reviewLines.slice(0, 10);
            """

            review_content = driver.execute_script(reviews_script)
            print("Review content found:")
            for line in review_content:
                print(f"  - {line}")
        else:
            print("❌ Reviews section still not loaded")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    debug_page_elements()
