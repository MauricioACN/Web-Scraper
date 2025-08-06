import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# List of search URLs
search_urls = [
    "https://www.canadiantire.ca/en/search-results.html?q=bikes"
]


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


def extract_products_from_search(driver, search_url):
    """Extract all products from a search page"""
    print(f"Accessing: {search_url}")
    driver.get(search_url)

    # Wait for the page to load
    time.sleep(5)

    products = []

    try:
        # Try different selectors to find products
        product_selectors = [
            "article",
            "[data-testid*='product']",
            ".product-card",
            ".product-tile",
            "[class*='product']"
        ]

        product_elements = []
        for selector in product_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(
                        f"Found {len(elements)} products with selector: {selector}")
                    product_elements = elements
                    break
            except:
                continue

        if not product_elements:
            print("No products found. Saving HTML for debug...")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return products

        # Extract information from each product
        for i, element in enumerate(product_elements):
            try:
                product = {}

                # Debugging: Save HTML of the element
                if i < 3:  # Only for the first 3 elements
                    print(f"=== DEBUG ELEMENT {i+1} ===")
                    print(
                        f"Element HTML: {element.get_attribute('outerHTML')[:500]}...")

                # Search for product title
                title = None
                title_selectors = [
                    "h1", "h2", "h3", "h4", "[class*='title']", "[class*='name']", "a[title]"]
                for selector in title_selectors:
                    try:
                        title_element = element.find_element(
                            By.CSS_SELECTOR, selector)
                        title = title_element.text.strip()
                        if title:
                            if i < 3:
                                print(
                                    f"Title found with '{selector}': {title}")
                            break
                    except:
                        if i < 3:
                            print(f"No title found with '{selector}'")
                        continue

                # Search for product link
                product_url = None
                link_selectors = ["a[href*='pdp']",
                                  "a[href*='product']", "a[href]"]
                for selector in link_selectors:
                    try:
                        link_element = element.find_element(
                            By.CSS_SELECTOR, selector)
                        product_url = link_element.get_attribute("href")
                        if product_url and ("pdp" in product_url or "product" in product_url):
                            if i < 3:
                                print(
                                    f"URL found with '{selector}': {product_url}")
                            break
                    except:
                        if i < 3:
                            print(f"No link found with '{selector}'")
                        continue

                # Search for price (optional)
                price = None
                price_selectors = [
                    ".price", "[class*='price']", "[data-testid*='price']"]
                for selector in price_selectors:
                    try:
                        price_element = element.find_element(
                            By.CSS_SELECTOR, selector)
                        price = price_element.text.strip()
                        if price:
                            break
                    except:
                        continue

                if title and product_url:
                    product = {
                        "title": title,
                        "product_url": product_url,
                        "price": price,
                        "search_url": search_url
                    }
                    products.append(product)
                    print(f"Product {i+1}: {title}")

            except Exception as e:
                print(f"Error extracting product {i+1}: {e}")
                continue

    except Exception as e:
        print(f"General error extracting products: {e}")

    return products


def extract_product_details(driver, product_url):
    """Extract specific details from a product page"""
    print(f"Extracting details from: {product_url}")

    try:
        driver.get(product_url)
        time.sleep(3)

        details = {}

        # Product title
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
            details["detailed_title"] = title
        except:
            details["detailed_title"] = None

        # Price
        try:
            price_selectors = [
                ".price", "[class*='price']", "[data-testid*='price']"]
            price = None
            for selector in price_selectors:
                try:
                    price_element = driver.find_element(
                        By.CSS_SELECTOR, selector)
                    price = price_element.text.strip()
                    if price:
                        break
                except:
                    continue
            details["detailed_price"] = price
        except:
            details["detailed_price"] = None

        # SKU or product code
        try:
            sku_selectors = ["[class*='sku']",
                             "[data-testid*='sku']", "[class*='model']"]
            sku = None
            for selector in sku_selectors:
                try:
                    sku_element = driver.find_element(
                        By.CSS_SELECTOR, selector)
                    sku = sku_element.text.strip()
                    if sku:
                        break
                except:
                    continue
            details["sku"] = sku
        except:
            details["sku"] = None

        # Description
        try:
            description_selectors = [".description",
                                     "[class*='description']", "[class*='detail']"]
            description = None
            for selector in description_selectors:
                try:
                    desc_element = driver.find_element(
                        By.CSS_SELECTOR, selector)
                    description = desc_element.text.strip()
                    if description:
                        break
                except:
                    continue
            details["description"] = description
        except:
            details["description"] = None

        return details

    except Exception as e:
        print(f"Error extracting product details: {e}")
        return {}


def main():
    """Main scraper function"""
    driver = setup_driver()
    all_products = []

    try:
        # Process each search URL
        for search_url in search_urls:
            print(f"\n=== Processing search: {search_url} ===")

            # Extract products from search page
            search_products = extract_products_from_search(
                driver, search_url)
            print(f"Found {len(search_products)} products")

            # Extract details from each product
            for i, product in enumerate(search_products):
                print(f"\nProcessing product {i+1}/{len(search_products)}")

                # Extract product details
                details = extract_product_details(
                    driver, product["product_url"])

                # Combine basic information with details
                complete_product = {**product, **details}
                all_products.append(complete_product)

                # Small pause between products
                time.sleep(2)

        # Save results to JSON
        with open("productos_scraped.json", "w", encoding="utf-8") as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        print(f"\n=== SCRAPING COMPLETED ===")
        print(f"Total products processed: {len(all_products)}")
        print(f"Results saved to: productos_scraped.json")

    except Exception as e:
        print(f"Error in main process: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
