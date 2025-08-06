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
    # Keep browser visible for investigation
    # options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def analyze_product_page_structure(driver, product_url, product_title):
    """Analyze the structure of a product page to understand review organization"""
    print(f"\n{'='*80}")
    print(f"ANALYZING PRODUCT PAGE STRUCTURE")
    print(f"{'='*80}")
    print(f"URL: {product_url}")
    print(f"Expected Product: {product_title}")
    print(f"{'='*80}")

    driver.get(product_url)
    time.sleep(5)  # Let page fully load

    analysis_results = {
        "product_url": product_url,
        "expected_title": product_title,
        "analysis": {}
    }

    # 1. Check page title and main product info
    print("\n1. MAIN PRODUCT INFORMATION:")
    try:
        page_title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        print(f"   Page H1 Title: {page_title}")
        print(
            f"   Matches Expected: {page_title.lower() in product_title.lower() or product_title.lower() in page_title.lower()}")
        analysis_results["analysis"]["page_title"] = page_title
        analysis_results["analysis"]["title_matches"] = page_title.lower(
        ) in product_title.lower()
    except:
        print("   Could not find page title")
        analysis_results["analysis"]["page_title"] = None

    # 2. Look for product SKU/ID
    print("\n2. PRODUCT IDENTIFICATION:")
    sku_selectors = ["[class*='sku']", "[class*='model']",
                     "[data-product-id]", "[class*='item-number']"]
    for selector in sku_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements[:3]:  # Check first 3 elements
                text = elem.text.strip() or elem.get_attribute(
                    "data-product-id") or elem.get_attribute("id")
                if text:
                    print(f"   Found SKU/ID with '{selector}': {text}")
                    analysis_results["analysis"]["product_sku"] = text
                    break
        except:
            continue

    # 3. Analyze overall page structure
    print("\n3. PAGE STRUCTURE ANALYSIS:")
    main_sections = driver.find_elements(
        By.CSS_SELECTOR, "main, .main, #main, .content, .product-details")
    print(f"   Found {len(main_sections)} main content sections")

    # 4. Look for review sections specifically
    print("\n4. REVIEW SECTION ANALYSIS:")
    review_section_selectors = [
        ".reviews",
        ".review-section",
        "[class*='review']",
        "#reviews",
        ".ratings-reviews",
        ".customer-reviews"
    ]

    for selector in review_section_selectors:
        try:
            sections = driver.find_elements(By.CSS_SELECTOR, selector)
            if sections:
                print(
                    f"   Found {len(sections)} elements with selector '{selector}'")
                for i, section in enumerate(sections[:3]):  # Analyze first 3
                    section_text = section.text.strip(
                    )[:100] + "..." if len(section.text.strip()) > 100 else section.text.strip()
                    print(f"     Section {i+1}: {section_text}")
        except:
            continue

    # 5. Look for related products sections
    print("\n5. RELATED PRODUCTS ANALYSIS:")
    related_selectors = [
        ".related-products",
        ".recommended",
        ".similar-products",
        "[class*='recommendation']",
        ".cross-sell",
        ".upsell"
    ]

    for selector in related_selectors:
        try:
            sections = driver.find_elements(By.CSS_SELECTOR, selector)
            if sections:
                print(
                    f"   Found {len(sections)} related product sections with '{selector}'")
                analysis_results["analysis"]["has_related_products"] = True
        except:
            continue

    # 6. Detailed review element analysis
    print("\n6. DETAILED REVIEW ELEMENTS ANALYSIS:")
    review_elements = driver.find_elements(
        By.CSS_SELECTOR, "[class*='review']")
    print(f"   Total elements with 'review' in class: {len(review_elements)}")

    review_types = {}
    for i, elem in enumerate(review_elements[:10]):  # Analyze first 10
        try:
            classes = elem.get_attribute("class")
            tag_name = elem.tag_name
            elem_id = elem.get_attribute("id") or "no-id"
            parent_classes = elem.find_element(
                By.XPATH, "..").get_attribute("class") or "no-parent-class"

            key = f"{tag_name}.{classes}"
            if key not in review_types:
                review_types[key] = {
                    "count": 0,
                    "sample_content": elem.text.strip()[:50] + "..." if elem.text.strip() else "no-text",
                    "sample_id": elem_id,
                    "parent_class": parent_classes
                }
            review_types[key]["count"] += 1
        except:
            continue

    print("\n   Review Element Types Found:")
    for element_type, info in review_types.items():
        print(f"     {element_type}: {info['count']} instances")
        print(f"       Sample content: {info['sample_content']}")
        print(f"       Sample ID: {info['sample_id']}")
        print(f"       Parent class: {info['parent_class']}")
        print()

    # 7. Look for review navigation/pagination
    print("\n7. REVIEW NAVIGATION ANALYSIS:")
    nav_selectors = [".pagination", ".page-nav",
                     "[class*='page']", ".load-more", ".show-more"]
    for selector in nav_selectors:
        try:
            nav_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if nav_elements:
                print(
                    f"   Found {len(nav_elements)} navigation elements with '{selector}'")
        except:
            continue

    # 8. Save page source for manual inspection
    timestamp = int(time.time())
    filename = f"page_analysis_{timestamp}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"\n8. Page source saved to: {filename}")
    analysis_results["analysis"]["saved_html"] = filename

    return analysis_results


def main():
    """Main investigation function"""
    # Load some products to analyze
    try:
        with open("productos_scraped_v0.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: productos_scraped_v0.json not found.")
        return

    driver = setup_driver()

    try:
        # Analyze first 3 products in detail
        analysis_results = []
        for i, product in enumerate(products[:3]):
            print(f"\n\nAnalyzing product {i+1}/3...")
            result = analyze_product_page_structure(
                driver,
                product["product_url"],
                product["title"]
            )
            analysis_results.append(result)

            # Pause between analyses
            input(
                "\nPress Enter to continue to next product analysis (or Ctrl+C to stop)...")

        # Save analysis results
        with open("review_structure_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE!")
        print("Results saved to: review_structure_analysis.json")
        print("Check the saved HTML files for detailed page structure inspection.")
        print(f"{'='*80}")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
