# Canadian Tire Web Scraper

This project extracts products and reviews from Canadian Tire using Selenium WebDriver.

## 📋 Features

- **Product extraction**: Gets product list with titles, prices and URLs
- **Review extraction**: Extracts all product reviews with automatic pagination
- **Specific search**: Finds reviews by author (e.g: Greg) or specific content
- **Mobile accordion handling**: Compatible with mobile and desktop versions
- **Traceability**: Each review includes the source product URL

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Web-Scraper
```

### 2. Create virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Chrome
- Make sure you have Google Chrome installed
- The driver is automatically downloaded with webdriver-manager

## 📖 Usage

### Extract products
```bash
python simple_scraper.py
```
Generates: `productos_scraped_v0.json`

### Extract reviews from all products
```bash
python review_scraper.py
```
Generates: `product_reviews.json`

## 📊 Data Structure

### Products (`productos_scraped_v0.json`)
```json
[
  {
    "title": "Product name",
    "price": "$123.99",
    "product_url": "https://www.canadiantire.ca/..."
  }
]
```

### Reviews (`product_reviews.json`)
```json
[
  {
    "review_id": "bv-review-123456",
    "product_url": "https://www.canadiantire.ca/...",
    "rating": 5,
    "title": "Review title",
    "body": "Review content",
    "date": "2 days ago",
    "reviewer": "Reviewer name",
    "verified_purchaser": true,
    "helpful_count": 3
  }
]
```

## 🔧 Configuration

### Headless mode (no window)
In `review_scraper.py`, uncomment the line:
```python
options.add_argument("--headless")
```

### Pagination page limit
In the `main()` function, adjust:
```python
reviews = handle_review_pagination(driver, max_pages=3)  # Change number
```

## 🎯 Specific Use Cases

### Search reviews by specific user
The scraper automatically searches for "Greg" reviews and reports when found.

### Process single product
Modify the URL in the code to test with a specific product.

### Resume extraction
The scraper automatically skips already processed products if `product_reviews.json` exists.

## 🛠️ Troubleshooting

### ChromeDriver error
```bash
# Update webdriver-manager
pip install --upgrade webdriver-manager
```

### Review timeout
Increase timeout in `wait_for_reviews_section_to_load()`:
```python
def wait_for_reviews_section_to_load(driver, timeout=60):  # Increase from 30 to 60
```

### Elements not found
The scraper is optimized for Canadian Tire's current structure. If they change the structure, CSS selectors may need adjustments.

## 📁 Project Files

- `simple_scraper.py` - Extracts products
- `review_scraper.py` - Extracts reviews (main file)
- `productos_scraped_v0.json` - Extracted products
- `product_reviews.json` - Extracted reviews
- `requirements.txt` - Dependencies

## 💡 Important Notes

- The scraper respects Canadian Tire's structure and handles Bazaarvoice-specific pagination
- Includes delays between requests to be respectful to the server
- Automatically saves progress to prevent data loss
- Compatible with Canadian Tire's mobile interface accordions
