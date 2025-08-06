import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import queue
import os


class ThreadSafeReviewScraper:
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.all_reviews = []
        self.product_ratings = {}
        self.processed_urls = set()
        self.lock = threading.Lock()
        self.results_queue = queue.Queue()
        self.error_count = 0
        self.success_count = 0

    def setup_driver(self):
        """Configure Chrome driver with optimized options for parallel processing"""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")  # Always headless for parallel
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        # Unique user data dir for each thread
        options.add_argument(
            f"--user-data-dir=/tmp/chrome_profile_{threading.current_thread().ident}")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)  # Reduced wait time
        return driver

    def click_on_review_count(self, driver):
        """Click on the review count number to open reviews section and extract rating info"""
        print(
            f"🔍 [Thread {threading.current_thread().ident}] Looking for review count...")

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
                    const fullText = reviewElement.textContent;
                    result.text = fullText;
                    
                    // Extract review count from parentheses
                    const reviewMatch = fullText.match(/\\((\\d+)\\)/);
                    if (reviewMatch) {
                        result.total_reviews = parseInt(reviewMatch[1]);
                    }
                    
                    // Look for the average rating
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
            
            result.text = 'No review count button found';
            return result;
        """

        try:
            result = driver.execute_script(js_click_script)
            if result['success']:
                time.sleep(2)  # Reduced wait time
                return True, result
            else:
                return False, result
        except Exception as e:
            print(
                f"❌ [Thread {threading.current_thread().ident}] Error clicking review count: {e}")
            return False, {'average_rating': None, 'total_reviews': None}

    def extract_individual_reviews(self, driver):
        """Extract individual reviews from the #reviews_container"""
        extraction_script = """
            const reviewsContainer = document.querySelector('#reviews_container');
            if (!reviewsContainer) {
                return { error: 'reviews_container not found', reviews: [] };
            }
            
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
                    
                    // Extract title
                    const titleElement = section.querySelector('h3');
                    if (titleElement) {
                        review.title = titleElement.textContent.trim();
                    }
                    
                    // Extract author name
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
                return []

            reviews = result['reviews']
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
            print(
                f"❌ [Thread {threading.current_thread().ident}] Error extracting reviews: {e}")
            return []

    def process_single_product(self, product, thread_id):
        """Process a single product - this is what gets parallelized"""
        product_url = product["product_url"]
        product_title = product.get('title', 'Unknown Product')

        print(f"🔄 [Thread {thread_id}] Starting: {product_title[:50]}...")

        driver = self.setup_driver()
        try:
            # Navigate to product page
            driver.get(product_url)
            time.sleep(3)  # Reduced wait time

            reviews = []
            product_rating_summary = {
                'average_rating': None,
                'total_reviews': None,
                'has_reviews': False
            }

            # Step 1: Click on review count and extract rating info
            review_section_opened, rating_data = self.click_on_review_count(
                driver)

            if rating_data.get('total_reviews') or rating_data.get('average_rating'):
                product_rating_summary = {
                    'average_rating': rating_data.get('average_rating'),
                    'total_reviews': rating_data.get('total_reviews'),
                    'has_reviews': True
                }

            if review_section_opened:
                # Wait for reviews section to load
                time.sleep(3)

                # Extract reviews (simplified pagination for parallel processing)
                reviews = self.extract_individual_reviews(driver)

                # Add product URL to each review
                for review in reviews:
                    review['product_url'] = product_url

            result = {
                'product_url': product_url,
                'product_title': product_title,
                'reviews': reviews,
                'rating_summary': product_rating_summary,
                'thread_id': thread_id,
                'success': True
            }

            print(
                f"✅ [Thread {thread_id}] Completed: {product_title[:50]} - {len(reviews)} reviews")
            return result

        except Exception as e:
            print(
                f"❌ [Thread {thread_id}] Error processing {product_title}: {e}")
            return {
                'product_url': product_url,
                'product_title': product_title,
                'reviews': [],
                'rating_summary': {'has_reviews': False},
                'thread_id': thread_id,
                'success': False,
                'error': str(e)
            }
        finally:
            driver.quit()

    def merge_results(self, result):
        """Thread-safe merge of results"""
        with self.lock:
            if result['success']:
                self.all_reviews.extend(result['reviews'])

                if result['rating_summary'].get('has_reviews'):
                    self.product_ratings[result['product_url']] = {
                        'product_title': result['product_title'],
                        'product_url': result['product_url'],
                        'average_rating': result['rating_summary'].get('average_rating'),
                        'total_reviews': result['rating_summary'].get('total_reviews'),
                        'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'thread_id': result['thread_id']
                    }

                self.processed_urls.add(result['product_url'])
                self.success_count += 1
            else:
                self.error_count += 1

    def save_progress(self):
        """Save current progress to files"""
        with self.lock:
            # Save reviews
            try:
                with open("product_reviews_parallel.json", "w", encoding="utf-8") as f:
                    json.dump(self.all_reviews, f,
                              ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving reviews: {e}")

            # Save product ratings
            try:
                with open("product_ratings_parallel.json", "w", encoding="utf-8") as f:
                    json.dump(self.product_ratings, f,
                              ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving ratings: {e}")

    def load_existing_data(self):
        """Load existing data to resume processing"""
        try:
            with open("product_reviews_parallel.json", "r", encoding="utf-8") as f:
                self.all_reviews = json.load(f)
                self.processed_urls = set(
                    [review["product_url"] for review in self.all_reviews])
                print(f"📂 Loaded {len(self.all_reviews)} existing reviews")
        except FileNotFoundError:
            print("📂 No existing reviews found, starting fresh")

        try:
            with open("product_ratings_parallel.json", "r", encoding="utf-8") as f:
                self.product_ratings = json.load(f)
                print(
                    f"📂 Loaded {len(self.product_ratings)} existing product ratings")
        except FileNotFoundError:
            print("📂 No existing product ratings found, starting fresh")

    def parallel_scrape(self, products):
        """Main parallel scraping function"""
        print(f"🚀 Starting parallel scraping with {self.max_workers} workers")
        print(f"📊 Total products to process: {len(products)}")

        # Load existing data
        self.load_existing_data()

        # Filter out already processed products
        unprocessed_products = [
            p for p in products if p["product_url"] not in self.processed_urls]

        if len(unprocessed_products) != len(products):
            print(
                f"⏭️ Skipping {len(products) - len(unprocessed_products)} already processed products")
            print(f"📊 Products to process: {len(unprocessed_products)}")

        if not unprocessed_products:
            print("✅ All products already processed!")
            return

        # Process in parallel
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_product = {
                executor.submit(self.process_single_product, product, f"T{i % self.max_workers}"): product
                for i, product in enumerate(unprocessed_products)
            }

            # Process completed jobs
            for future in as_completed(future_to_product):
                try:
                    result = future.result()
                    self.merge_results(result)

                    # Save progress every 5 completed products
                    if (self.success_count + self.error_count) % 5 == 0:
                        self.save_progress()
                        progress = (self.success_count + self.error_count) / \
                            len(unprocessed_products) * 100
                        print(
                            f"📈 Progress: {progress:.1f}% ({self.success_count} success, {self.error_count} errors)")

                except Exception as e:
                    print(f"❌ Future execution error: {e}")
                    self.error_count += 1

        # Final save
        self.save_progress()

        elapsed_time = time.time() - start_time
        print(f"\n🎉 Parallel scraping completed!")
        print(f"⏱️ Total time: {elapsed_time:.2f} seconds")
        print(f"📊 Success: {self.success_count} products")
        print(f"❌ Errors: {self.error_count} products")
        print(f"📝 Total reviews extracted: {len(self.all_reviews)}")
        print(f"⭐ Products with ratings: {len(self.product_ratings)}")
        print(f"💾 Results saved to: product_reviews_parallel.json and product_ratings_parallel.json")


def main_parallel():
    """Main function for parallel processing"""
    # Load products
    try:
        with open("productos_scraped_v0.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: productos_scraped_v0.json not found. Please run the product scraper first.")
        return

    print(f"🚀 PARALLEL REVIEW SCRAPER")
    print(f"📊 Loaded {len(products)} products")

    # Create scraper with 3 workers (adjust based on your system)
    scraper = ThreadSafeReviewScraper(max_workers=3)

    # Start parallel processing
    scraper.parallel_scrape(products)


if __name__ == "__main__":
    main_parallel()
