import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def setup_driver():
    """Configure Chrome driver with optimized options"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Uncomment the following line if you want it to run without a window
    # options.add_argument("--headless")

    # Use WebDriver Manager to automatically download the correct version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def click_on_review_count(driver):
    """Click on the review count number to open reviews section and extract rating info"""
    print("🔍 Looking for review count to click and extracting rating info...")

    # Enhanced script that both clicks and extracts rating information
    js_click_script = """
        let result = {
            success: false, 
            text: '', 
            average_rating: null, 
            total_reviews: null
        };
        
        // Look for the specific bv_numReviews_text element
        let reviewElement = document.querySelector('.bv_numReviews_text');
        if (reviewElement && reviewElement.textContent.includes('(')) {
            let button = reviewElement.closest('button');
            if (button) {
                // Extract review count from the review element
                const fullText = reviewElement.textContent;
                result.text = fullText;
                
                // Extract review count from parentheses
                const reviewMatch = fullText.match(/\\((\\d+)\\)/);
                if (reviewMatch) {
                    result.total_reviews = parseInt(reviewMatch[1]);
                }
                
                // Look for the average rating in the specific bv_avgRating_component_container
                const ratingElement = document.querySelector('.bv_avgRating_component_container');
                if (ratingElement) {
                    const ratingText = ratingElement.textContent.trim();
                    const ratingValue = parseFloat(ratingText);
                    if (!isNaN(ratingValue) && ratingValue >= 0 && ratingValue <= 5) {
                        result.average_rating = ratingValue;
                    }
                }
                
                // If still no rating found, try alternative selectors
                if (!result.average_rating) {
                    const altRatingSelectors = [
                        '.bv-rating-value',
                        '[data-rating]',
                        '.rating-value',
                        '.average-rating'
                    ];
                    
                    for (let selector of altRatingSelectors) {
                        const altElement = document.querySelector(selector);
                        if (altElement) {
                            const altText = altElement.textContent.trim() || altElement.getAttribute('data-rating');
                            const altValue = parseFloat(altText);
                            if (!isNaN(altValue) && altValue >= 0 && altValue <= 5) {
                                result.average_rating = altValue;
                                break;
                            }
                        }
                    }
                }
                
                button.click();
                result.success = true;
                return result;
            }
        }
        
        // Fallback: Look for any element with review count pattern
        const allElements = document.querySelectorAll('*');
        for (let element of allElements) {
            const text = element.textContent;
            if (text && /\\(\\d+\\)/.test(text) && text.includes('star')) {
                let button = element.closest('button');
                if (button) {
                    result.text = text.substring(0, 50);
                    
                    // Extract review count
                    const reviewMatch = text.match(/\\((\\d+)\\)/);
                    if (reviewMatch) {
                        result.total_reviews = parseInt(reviewMatch[1]);
                    }
                    
                    // Look for the average rating in the specific container
                    const ratingElement = document.querySelector('.bv_avgRating_component_container');
                    if (ratingElement) {
                        const ratingText = ratingElement.textContent.trim();
                        const ratingValue = parseFloat(ratingText);
                        if (!isNaN(ratingValue) && ratingValue >= 0 && ratingValue <= 5) {
                            result.average_rating = ratingValue;
                        }
                    }
                    
                    button.click();
                    result.success = true;
                    return result;
                }
            }
        }
        
        result.text = 'No review count button found';
        return result;
    """

    try:
        result = driver.execute_script(js_click_script)
        if result['success']:
            print(f"✅ Clicked review count: {result['text']}")
            if result['average_rating']:
                print(
                    f"⭐ Found average rating: {result['average_rating']} stars")
            if result['total_reviews']:
                print(f"📊 Found total reviews: {result['total_reviews']}")

            time.sleep(3)  # Wait a bit

            # Now expand the reviews accordion if we're on mobile view
            print("🔍 Checking if we need to expand reviews accordion...")
            accordion_script = """
                // Look for the reviews accordion button
                let reviewsAccordionButton = document.querySelector('#BVRRContainer-mobile .nl-accordion__button');
                if (reviewsAccordionButton) {
                    let isExpanded = reviewsAccordionButton.getAttribute('aria-expanded') === 'true';
                    if (!isExpanded) {
                        reviewsAccordionButton.click();
                        return { success: true, action: 'expanded_accordion' };
                    }
                    return { success: true, action: 'already_expanded' };
                }
                
                // If no accordion, check for desktop reviews container
                let desktopContainer = document.querySelector('#BVRRContainer');
                if (desktopContainer) {
                    return { success: true, action: 'desktop_view' };
                }
                
                return { success: false, action: 'no_container_found' };
            """

            accordion_result = driver.execute_script(accordion_script)
            print(f"📱 Accordion action: {accordion_result['action']}")

            time.sleep(3)  # Wait for expansion
            return True, result
        else:
            print(f"⚠️ {result['text']}")
            return False, result
    except Exception as e:
        print(f"❌ Error clicking review count: {e}")
        return False, {'average_rating': None, 'total_reviews': None}


def wait_for_reviews_section_to_load(driver, timeout=30):
    """Wait for the reviews section to load after clicking"""
    print("⏳ Waiting for reviews section to load...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check for reviews_container first (desktop/expanded mobile)
            reviews_container = driver.find_element(By.ID, "reviews_container")
            reviews = reviews_container.find_elements(
                By.CSS_SELECTOR, "section[id^='bv-review-']")
            if reviews:
                print(f"✅ Found {len(reviews)} reviews in reviews_container")
                return True

        except:
            pass

        try:
            # Check for mobile BVRRContainer that's expanded
            mobile_container = driver.find_element(
                By.ID, "BVRRContainer-mobile")
            accordion_panel = mobile_container.find_element(
                By.CSS_SELECTOR, ".nl-accordion__panel:not(.nl-accordion__panel--hidden)")
            # If we found an expanded accordion panel, that's good
            print("✅ Found expanded mobile reviews accordion")
            return True

        except:
            pass

        try:
            # Check for any Bazaarvoice review content
            bv_elements = driver.find_elements(
                By.CSS_SELECTOR, "[class*='bv-'], [id*='BV']")
            review_elements = [el for el in bv_elements if 'review' in el.get_attribute(
                'class').lower() or 'review' in el.get_attribute('id').lower()]
            if len(review_elements) > 3:
                print(
                    f"✅ Found {len(review_elements)} Bazaarvoice review elements")
                return True

        except:
            pass

        # Check for review text indicators
        try:
            page_text = driver.execute_script(
                "return document.body.innerText.toLowerCase();")
            indicators = ["verified purchaser", "days ago",
                          "weeks ago", "months ago", "helpful", "filter reviews"]
            found_indicators = sum(
                1 for indicator in indicators if indicator in page_text)

            if found_indicators >= 2:
                print(f"✅ Found {found_indicators} review text indicators")
                return True

        except:
            pass

        time.sleep(1)

    print("⚠️ Timeout waiting for reviews section")

    # Debug: Save page content
    try:
        with open('debug_after_accordion.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("📄 Page source saved to debug_after_accordion.html")
    except:
        pass

    return False


def extract_individual_reviews(driver):
    """Extract individual reviews from the #reviews_container"""
    print("📝 Extracting reviews from reviews_container...")

    # JavaScript to extract reviews directly from the reviews container
    extraction_script = """
        const reviewsContainer = document.querySelector('#reviews_container');
        if (!reviewsContainer) {
            return { error: 'reviews_container not found', reviews: [] };
        }
        
        // Get all review sections
        const reviewSections = reviewsContainer.querySelectorAll('section[id^="bv-review-"]');
        let reviews = [];
        
        reviewSections.forEach((section, index) => {
            try {
                const review = {
                    reviewId: section.id,
                    position: index + 1,
                    rating: null,
                    title: null,
                    author: null,
                    date: null,
                    content: null,
                    isVerifiedPurchaser: false,
                    helpfulCount: 0
                };
                
                // Extract rating from aria-label
                const ratingElement = section.querySelector('[role="img"][aria-label*="out of 5 stars"]');
                if (ratingElement) {
                    const ratingText = ratingElement.getAttribute('aria-label');
                    const ratingMatch = ratingText.match(/(\\d+)\\s+out of 5 stars/);
                    if (ratingMatch) {
                        review.rating = parseInt(ratingMatch[1]);
                    }
                }
                
                // Extract title (h3 element)
                const titleElement = section.querySelector('h3');
                if (titleElement) {
                    review.title = titleElement.textContent.trim();
                }
                
                // Extract author name from button
                const authorButton = section.querySelector('button[aria-label*="See"][aria-label*="profile"]');
                if (authorButton) {
                    review.author = authorButton.textContent.trim();
                }
                
                // Extract date
                const dateElement = section.querySelector('.bv-rnr__g3jej5-1');
                if (dateElement) {
                    review.date = dateElement.textContent.trim();
                }
                
                // Extract review content
                const contentElement = section.querySelector('.bv-rnr__sc-16dr7i1-3');
                if (contentElement) {
                    review.content = contentElement.textContent.trim();
                }
                
                // Check if verified purchaser
                const verifiedElement = section.querySelector('[title*="purchased the product"]');
                review.isVerifiedPurchaser = !!verifiedElement;
                
                // Extract helpful count
                const helpfulButton = section.querySelector('button[aria-label*="people found this review"]');
                if (helpfulButton) {
                    const helpfulText = helpfulButton.getAttribute('aria-label');
                    const helpfulMatch = helpfulText.match(/(\\d+)\\s+people found/);
                    if (helpfulMatch) {
                        review.helpfulCount = parseInt(helpfulMatch[1]);
                    }
                }
                
                reviews.push(review);
                
            } catch (error) {
                console.log('Error processing review:', error);
            }
        });
        
        return {
            reviews: reviews,
            totalFound: reviews.length,
            containerExists: true
        };
    """

    try:
        result = driver.execute_script(extraction_script)

        if result.get('error'):
            print(f"❌ {result['error']}")
            return []

        reviews = result['reviews']
        print(f"✅ Extracted {len(reviews)} reviews from current page")

        # Convert to expected format and add product URL
        current_url = driver.current_url
        formatted_reviews = []
        for review in reviews:
            formatted_reviews.append({
                "review_id": review.get('reviewId'),
                "product_url": current_url,
                "rating": review.get('rating'),
                "title": review.get('title'),
                "body": review.get('content', ''),
                "date": review.get('date', ''),
                "reviewer": review.get('author', ''),
                "verified_purchaser": review.get('isVerifiedPurchaser', False),
                "helpful_count": review.get('helpfulCount', 0)
            })

        return formatted_reviews

    except Exception as e:
        print(f"❌ Error extracting reviews: {e}")
        return []


def handle_review_pagination(driver, max_pages=10):
    """Handle pagination to get all reviews using the specific Next Reviews button"""
    print(f"📄 Handling pagination (max {max_pages} pages)...")

    all_reviews = []
    page_count = 0

    while page_count < max_pages:
        # Extract reviews from current page
        page_reviews = extract_individual_reviews(driver)

        if page_reviews:
            all_reviews.extend(page_reviews)
            print(
                f"   Page {page_count + 1}: Found {len(page_reviews)} reviews")

            # Show sample reviewer names from this page
            reviewer_names = [r['reviewer']
                              for r in page_reviews if r['reviewer']]
            if reviewer_names:
                print(
                    f"   Reviewers: {', '.join(reviewer_names[:3])}{'...' if len(reviewer_names) > 3 else ''}")
        else:
            print(f"   Page {page_count + 1}: No reviews found")

        # Look for pagination info
        pagination_info = driver.execute_script("""
            const paginationElement = document.querySelector('.bv-rnr__sc-11r39gb-2');
            if (paginationElement) {
                return paginationElement.textContent.trim();
            }
            return null;
        """)

        if pagination_info:
            print(f"   Pagination: {pagination_info}")

        # Look for Next button using the specific structure you provided
        next_clicked = driver.execute_script("""
            // Look for the specific Next Reviews button structure
            const nextButton = document.querySelector('a.next[role="button"]');
            if (nextButton && !nextButton.disabled && nextButton.href) {
                // Scroll to button and click
                nextButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                nextButton.click();
                return true;
            }
            
            // Fallback: Look for any Next button
            const allButtons = document.querySelectorAll('a, button');
            for (let button of allButtons) {
                const text = button.textContent.toLowerCase();
                if (text.includes('next') && text.includes('review')) {
                    if (!button.disabled && button.style.display !== 'none') {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            return false;
        """)

        if next_clicked:
            print("   ✅ Clicked Next Reviews button")
            time.sleep(4)  # Wait for next page to load
            page_count += 1
        else:
            print("   ⚠️ No more pages - pagination complete")
            break

    print(
        f"📄 Pagination complete: {len(all_reviews)} total reviews from {page_count + 1} pages")

    return all_reviews


def extract_reviews_from_product(driver, product_url):
    """Extract all reviews from a product page using the specific Canadian Tire flow"""
    print(f"Extracting reviews from: {product_url}")
    driver.get(product_url)

    # Wait for the page to load
    time.sleep(5)

    reviews = []
    product_rating_summary = {
        'average_rating': None,
        'total_reviews': None,
        'has_reviews': False
    }

    try:
        # Step 1: Click on the review count and extract rating info in one step
        review_section_opened, rating_data = click_on_review_count(driver)

        # Store the rating information we got from clicking
        if rating_data.get('total_reviews') or rating_data.get('average_rating'):
            product_rating_summary = {
                'average_rating': rating_data.get('average_rating'),
                'total_reviews': rating_data.get('total_reviews'),
                'has_reviews': True
            }

        if not review_section_opened:
            print("❌ Could not open reviews section")
            # Still return the product rating summary even if we can't get individual reviews
            return reviews, product_rating_summary

        # Step 2: Wait for reviews section to load
        reviews_loaded = wait_for_reviews_section_to_load(driver)

        if not reviews_loaded:
            print("❌ Reviews section did not load properly")
            return reviews, product_rating_summary

        # Step 3: Extract reviews with pagination
        reviews = handle_review_pagination(driver, max_pages=3)

        # Add product URL to each review
        for review in reviews:
            review['product_url'] = product_url

        print(f"✅ Successfully extracted {len(reviews)} reviews")

        # Log any Greg mentions
        greg_reviews = [r for r in reviews if r.get('greg_mention', False)]
        if greg_reviews:
            print(f"🎯 Found {len(greg_reviews)} reviews mentioning Greg!")
            for review in greg_reviews:
                print(
                    f"   Greg review by {review['reviewer']}: {review['body'][:100]}...")

    except Exception as e:
        print(f"❌ Error in extract_reviews_from_product: {e}")

    return reviews, product_rating_summary


def save_reviews_to_file(all_reviews, filename="product_reviews.json"):
    """Save reviews to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)
        print(f"Reviews saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews: {e}")


def save_product_ratings_to_file(product_ratings, filename="product_ratings_summary.json"):
    """Save product rating summaries to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(product_ratings, f, ensure_ascii=False, indent=2)
        print(f"Product ratings summary saved to {filename}")
    except Exception as e:
        print(f"Error saving product ratings: {e}")


def load_existing_product_ratings(filename="product_ratings_summary.json"):
    """Load existing product ratings from JSON file if it exists"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No existing {filename} found. Starting fresh.")
        return {}
    except Exception as e:
        print(f"Error loading existing product ratings: {e}")
        return {}


def load_existing_reviews(filename="product_reviews.json"):
    """Load existing reviews from JSON file if it exists"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No existing {filename} found. Starting fresh.")
        return []
    except Exception as e:
        print(f"Error loading existing reviews: {e}")
        return []


def main():
    """Main function to extract reviews from all products"""
    # Load existing products
    try:
        with open("productos_scraped_v0.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: productos_scraped_v0.json not found. Please run the product scraper first.")
        return

    # Load existing reviews and product ratings (in case we're resuming)
    all_reviews = load_existing_reviews()
    product_ratings = load_existing_product_ratings()

    # Get URLs that have already been processed
    processed_urls = set([review["product_url"] for review in all_reviews])

    driver = setup_driver()

    try:
        print(f"Processing {len(products)} products for reviews...")
        if processed_urls:
            print(
                f"Found {len(processed_urls)} already processed products. Continuing from where we left off...")

        # Process each product
        for i, product in enumerate(products):
            product_url = product["product_url"]

            # Skip if already processed
            if product_url in processed_urls:
                print(
                    f"\n=== Skipping product {i+1}/{len(products)} (already processed) ===")
                print(f"Product: {product['title']}")
                continue

            print(f"\n=== Processing product {i+1}/{len(products)} ===")
            print(f"Product: {product['title']}")

            # Extract reviews and rating summary from product page
            reviews, rating_summary = extract_reviews_from_product(
                driver, product_url)

            # Store the product rating summary
            if rating_summary.get('has_reviews'):
                product_ratings[product_url] = {
                    'product_title': product['title'],
                    'product_url': product_url,
                    'average_rating': rating_summary.get('average_rating'),
                    'total_reviews': rating_summary.get('total_reviews'),
                    'rating_distribution': rating_summary.get('rating_distribution', {}),
                    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }

            # Add new reviews to the collection
            all_reviews.extend(reviews)

            print(f"Found {len(reviews)} individual reviews for this product")
            if rating_summary.get('has_reviews'):
                print(
                    f"Product rating: {rating_summary.get('average_rating')} stars ({rating_summary.get('total_reviews')} total reviews)")
            print(f"Total reviews so far: {len(all_reviews)}")

            # Save after each product to avoid data loss
            save_reviews_to_file(all_reviews)
            save_product_ratings_to_file(product_ratings)

            # Small pause between products
            time.sleep(2)

        print(f"\n=== REVIEW EXTRACTION COMPLETED ===")
        print(f"Total individual reviews extracted: {len(all_reviews)}")
        print(f"Total products with rating summaries: {len(product_ratings)}")
        print(f"Results saved to: product_reviews.json and product_ratings_summary.json")

    except Exception as e:
        print(f"Error in main process: {e}")
        # Save whatever we have collected so far
        save_reviews_to_file(all_reviews)
        save_product_ratings_to_file(product_ratings)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
