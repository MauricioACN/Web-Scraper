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
    # Keep browser visible for testing
    # options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def test_review_extraction(driver, product_url, product_title):
    """Test extraction of specific review data from identified containers"""
    print(f"\n{'='*80}")
    print(f"TESTING REVIEW EXTRACTION")
    print(f"{'='*80}")
    print(f"URL: {product_url}")
    print(f"Product: {product_title}")
    print(f"{'='*80}")

    driver.get(product_url)
    time.sleep(5)  # Let page fully load

    # Test 1: Extract from div.nl-reviews__list
    print("\n1. TESTING div.nl-reviews__list CONTAINERS:")
    review_lists = driver.find_elements(
        By.CSS_SELECTOR, "div.nl-reviews__list")
    print(f"   Found {len(review_lists)} div.nl-reviews__list containers")

    extracted_reviews = []

    for i, review_list in enumerate(review_lists):
        print(f"\n   Analyzing container {i+1}:")
        print(
            f"   Container HTML snippet: {review_list.get_attribute('outerHTML')[:200]}...")

        # Look for individual reviews within this container
        review_items = review_list.find_elements(By.CSS_SELECTOR, "*")
        print(f"   Found {len(review_items)} child elements")

        # Try different selectors within this container
        review_selectors = [
            ".review-item",
            ".review-card",
            "[class*='review']",
            "li",
            "div"
        ]

        for selector in review_selectors:
            try:
                items = review_list.find_elements(By.CSS_SELECTOR, selector)
                if items and len(items) > 0 and len(items) < 20:  # Reasonable number
                    print(
                        f"   Found {len(items)} items with selector '{selector}' in this container")

                    # Test extracting data from first few items
                    for j, item in enumerate(items[:3]):
                        print(
                            f"\n   --> Testing item {j+1} with '{selector}':")
                        review_data = extract_review_data_from_element(
                            item, j+1)
                        if review_data["has_content"]:
                            extracted_reviews.append(review_data)
                    break
            except Exception as e:
                print(f"   Error with selector '{selector}': {e}")
                continue

    # Test 2: Extract from div.nl-product-card__reviews
    print(f"\n\n2. TESTING div.nl-product-card__reviews CONTAINER:")
    product_reviews = driver.find_elements(
        By.CSS_SELECTOR, "div.nl-product-card__reviews")
    print(
        f"   Found {len(product_reviews)} div.nl-product-card__reviews containers")

    for i, container in enumerate(product_reviews):
        print(f"\n   Analyzing product review container {i+1}:")
        print(f"   Container text: {container.text.strip()[:200]}...")
        print(
            f"   Container HTML: {container.get_attribute('outerHTML')[:300]}...")

        # This might contain summary info rather than individual reviews
        # Look for links to full reviews or summary data
        links = container.find_elements(By.CSS_SELECTOR, "a")
        for link in links:
            href = link.get_attribute("href")
            text = link.text.strip()
            print(f"   Found link: '{text}' -> {href}")

    # Test 3: Look for specific review data patterns
    print(f"\n\n3. TESTING SPECIFIC REVIEW DATA PATTERNS:")

    # Look for star ratings
    star_selectors = [
        "[class*='star']",
        "[class*='rating']",
        "[aria-label*='star']",
        ".stars"
    ]

    for selector in star_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(
                    f"   Found {len(elements)} star/rating elements with '{selector}'")
                for i, elem in enumerate(elements[:3]):
                    aria_label = elem.get_attribute("aria-label")
                    text = elem.text.strip()
                    classes = elem.get_attribute("class")
                    print(
                        f"     Element {i+1}: aria-label='{aria_label}', text='{text}', class='{classes}'")
        except:
            continue

    # Look for dates
    date_selectors = [
        "[class*='date']",
        "time",
        "[datetime]"
    ]

    for selector in date_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(
                    f"   Found {len(elements)} date elements with '{selector}'")
                for i, elem in enumerate(elements[:3]):
                    datetime_attr = elem.get_attribute("datetime")
                    text = elem.text.strip()
                    print(
                        f"     Date {i+1}: datetime='{datetime_attr}', text='{text}'")
        except:
            continue

    print(f"\n\n{'='*80}")
    print(f"EXTRACTION TEST SUMMARY:")
    print(f"Total meaningful reviews extracted: {len(extracted_reviews)}")
    for i, review in enumerate(extracted_reviews):
        print(f"Review {i+1}: {review}")
    print(f"{'='*80}")

    return extracted_reviews


def extract_review_data_from_element(element, item_number):
    """Extract review data from a single element"""
    review_data = {
        "item_number": item_number,
        "has_content": False,
        "rating": None,
        "title": None,
        "body": None,
        "date": None,
        "reviewer": None,
        "element_info": {
            "tag": element.tag_name,
            "class": element.get_attribute("class"),
            "text_length": len(element.text.strip())
        }
    }

    try:
        element_text = element.text.strip()
        print(f"       Element text: {element_text[:100]}..." if len(
            element_text) > 100 else f"       Element text: {element_text}")
        print(
            f"       Element tag: {element.tag_name}, class: {element.get_attribute('class')}")

        # Look for rating within this element
        try:
            rating_elem = element.find_element(
                By.CSS_SELECTOR, "[class*='star'], [class*='rating'], [aria-label*='star']")
            rating_text = rating_elem.get_attribute(
                "aria-label") or rating_elem.text
            if rating_text:
                import re
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    review_data["rating"] = int(rating_match.group(1))
                    print(f"       Found rating: {review_data['rating']}")
        except:
            pass

        # Look for title within this element
        try:
            title_selectors = ["h1", "h2", "h3",
                               "h4", "[class*='title']", ".title"]
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(
                        By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title and len(title) > 2:
                        review_data["title"] = title
                        print(f"       Found title: {title}")
                        break
                except:
                    continue
        except:
            pass

        # Look for date within this element
        try:
            date_elem = element.find_element(
                By.CSS_SELECTOR, "[class*='date'], time, [datetime]")
            date = date_elem.text.strip() or date_elem.get_attribute("datetime")
            if date:
                review_data["date"] = date
                print(f"       Found date: {date}")
        except:
            pass

        # Look for reviewer name
        try:
            name_selectors = ["[class*='author']",
                              "[class*='name']", "[class*='user']"]
            for selector in name_selectors:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, selector)
                    name = name_elem.text.strip()
                    if name and len(name) > 1:
                        review_data["reviewer"] = name
                        print(f"       Found reviewer: {name}")
                        break
                except:
                    continue
        except:
            pass

        # Consider the element text as body if it's substantial
        if len(element_text) > 20:
            review_data["body"] = element_text[:200] + \
                "..." if len(element_text) > 200 else element_text
            print(
                f"       Using element text as body (length: {len(element_text)})")

        # Determine if this element has meaningful review content
        if (review_data["rating"] or
            review_data["title"] or
            review_data["date"] or
            review_data["reviewer"] or
                (review_data["body"] and len(review_data["body"]) > 20)):
            review_data["has_content"] = True

    except Exception as e:
        print(f"       Error extracting data: {e}")

    return review_data


def main():
    """Main testing function"""
    # Load first product for testing
    try:
        with open("productos_scraped_v0.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: productos_scraped_v0.json not found.")
        return

    driver = setup_driver()

    try:
        # Test with the first product only
        product = products[0]
        print(f"Testing review extraction with first product...")

        reviews = test_review_extraction(
            driver,
            product["product_url"],
            product["title"]
        )

        # Save test results
        test_results = {
            "product": product,
            "extracted_reviews": reviews,
            "test_timestamp": time.time()
        }

        with open("review_extraction_test.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)

        print(f"\nTest results saved to: review_extraction_test.json")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    main()
