# Canadian Tire Bikes Web Scraper

This project is a comprehensive web scraping solution that extracts bicycle products and customer reviews from Canadian Tire using advanced Selenium WebDriver techniques. The scraper focuses specifically on bikes and cycling products, providing detailed product information, pricing data, and customer sentiment analysis.

## 🎯 Project Overview

This scraper was designed to collect comprehensive data about bicycles sold on Canadian Tire's e-commerce platform. It extracts product listings, detailed specifications, customer reviews, and performs sentiment analysis to understand customer satisfaction patterns in the cycling market.

### Target Data
- **Product Focus**: Bicycles and cycling equipment exclusively
- **Search Scope**: Canadian Tire bikes search results
- **Data Depth**: Complete product catalog with reviews and ratings
- **Analysis**: Natural Language Processing and sentiment analysis on customer feedback

## 📋 Features & Capabilities

- **🚴 Bike-Specific Product Extraction**: Targets bicycle search results with comprehensive product data
- **⭐ Advanced Review Mining**: Extracts all customer reviews with automatic pagination handling
- **📱 Cross-Platform Compatibility**: Works with both desktop and mobile Canadian Tire interfaces
- **🔗 Complete Traceability**: Each review linked to its source product for data integrity
- **💰 Price & Discount Analysis**: Captures pricing, discounts, and promotional information
- **📊 Sentiment Analysis**: NLP-powered sentiment classification of customer reviews
- **🔄 Resume Capability**: Can continue interrupted scraping sessions
- **⚡ Parallel Processing**: Multi-threaded extraction for improved performance

## 🧠 Scraping Methodology

### 1. Search Strategy
- **Base URL**: `https://www.canadiantire.ca/en/search-results.html?q=bikes`
- **Approach**: Systematic extraction of all bike-related products from search results
- **Pagination**: Automatic handling of search result pagination to capture complete inventory

### 2. Product Discovery Process
```
Search Query: "bikes" → Product Listings → Individual Product Pages → Review Sections
```

### 3. Data Extraction Layers

#### Layer 1: Product Catalog
- Product titles and descriptions
- Pricing information (current price, original price, discounts)
- Product URLs and unique identifiers
- Brand classification
- Category assignment (mountain bikes, comfort bikes, kids bikes, etc.)

#### Layer 2: Customer Reviews
- Individual review content and ratings
- Reviewer information and verification status
- Review dates and helpfulness scores
- Product-specific review aggregations

#### Layer 3: Sentiment & NLP Analysis
- Sentence tokenization of review text
- Word-level analysis for keyword extraction
- Sentiment classification (positive, negative, neutral)
- Confidence scoring for sentiment predictions

### 4. Technical Implementation

#### Browser Automation
- **Technology**: Selenium WebDriver with Chrome
- **Handling**: Dynamic content loading via JavaScript execution
- **Reliability**: Robust element waiting and error handling
- **Mobile Support**: Automatic detection and handling of mobile accordion interfaces

#### Review Extraction Specifics
```python
# Canadian Tire uses Bazaarvoice for reviews
# Our scraper handles their specific pagination system:
1. Click review count button → Opens review section
2. Wait for dynamic content load → Reviews container appears  
3. Extract visible reviews → Parse individual review data
4. Navigate pagination → "Next Reviews" button clicking
5. Repeat until all reviews collected
```

## 🎯 Key Assumptions & Limitations

### Data Assumptions
1. **Search Scope**: Focuses exclusively on products returned by "bikes" search query
2. **Language**: Processes English and French reviews (Canadian bilingual content)
3. **Availability**: Only captures products currently listed and available
4. **Review Completeness**: Assumes all public reviews are accessible via pagination

### Technical Assumptions
1. **Site Structure**: Based on Canadian Tire's current DOM structure (as of 2025)
2. **Bazaarvoice Integration**: Relies on current review system implementation
3. **Rate Limiting**: Implements respectful delays to avoid triggering anti-bot measures

### Business Logic Assumptions
1. **Product Classification**: Categorizes products based on title keywords and descriptions
2. **Price Analysis**: Considers displayed prices as current market pricing
3. **Review Authenticity**: Treats all displayed reviews as legitimate customer feedback
4. **Seasonality**: Data represents point-in-time snapshot, not seasonal trends

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

## 📖 Usage & Workflow

### Step 1: Extract Bike Products
```bash
python simple_scraper.py
```
**Process**: Scrapes Canadian Tire bikes search results
**Output**: `productos_scraped_v0.json` (Complete bike product catalog)
**Duration**: ~5-10 minutes depending on inventory size

### Step 2: Extract Customer Reviews
```bash
python review_scraper.py
```
**Process**: Visits each product page and extracts all customer reviews
**Output**: `product_reviews.json` (Complete review dataset)
**Duration**: ~2-4 hours for full catalog (depends on review volume)

### Step 3: Clean & Enhance Data
```bash
python clean_products.py
```
**Process**: Normalizes data, extracts pricing info, categorizes products
**Output**: `productos_cleaned.json` (Enhanced product data)

### Step 4: NLP Processing
```bash
cd NLP
python basic_nlp_processing.py
```
**Process**: Tokenizes review text into sentences and words
**Database**: Updates MongoDB with NLP-processed reviews

### Step 5: Sentiment Analysis
```bash
cd NLP
python sentiment_analysis.py
```
**Process**: Analyzes customer sentiment using VADER and TextBlob
**Database**: Adds sentiment scores to each review in MongoDB

## 📊 Data Structure & Schema

### Bikes Catalog (`productos_cleaned.json`)
```json
[
  {
    "product_id": "0710110p",
    "title": "Supercycle Reaction Hardtail Mountain Bike for All Ages, 26-in, Black",
    "brand": "Supercycle",
    "category": "mountain_bikes",
    "product_url": "https://www.canadiantire.ca/en/pdp/...",
    "price": 159.99,
    "raw_price": "$159.99",
    "discount": {
      "discount_percentage": 17,
      "discount_amount": 90.0,
      "original_price": 529.99,
      "ends_date": "August 07, 2025",
      "has_discount": true
    },
    "average_rating": 4.1,
    "total_reviews": 11,
    "description": "Full product description...",
    "sku": "Product SKU and identifier",
    "created_at": "2025-08-05T23:35:19.563908",
    "updated_at": "2025-08-05T23:35:19.563914"
  }
]
```

### Customer Reviews (`product_reviews.json`)
```json
[
  {
    "review_id": "bv-review-353384562",
    "product_url": "https://www.canadiantire.ca/en/pdp/...",
    "rating": 1,
    "title": "Bike Return Policy",
    "body": "I'm not very happy with the policy of Canadian tire...",
    "date": "2 days ago",
    "reviewer": "Greg",
    "verified_purchaser": true,
    "helpful_count": 0
  }
]
```

### NLP-Enhanced Reviews (MongoDB)
```json
{
  "_id": "ObjectId",
  "review_id": "bv-review-353384562",
  "product_url": "https://www.canadiantire.ca/...",
  "rating": 1,
  "title": "Bike Return Policy",
  "body": "Complete review text...",
  "reviewer": "Greg",
  "verified_purchaser": true,
  "sentences": [
    "I'm not very happy with the policy of Canadian tire.",
    "I purchased a bike, couldn't ride it and tried to take it back.",
    "I was told I can't return it because I rode it."
  ],
  "words": ["I", "'m", "not", "very", "happy", "with", "the", "policy", ...],
  "sentiment_analysis": {
    "sentiment": "negative",
    "confidence_score": 0.856,
    "combined_score": -0.642,
    "vader_scores": {
      "compound": -0.659,
      "positive": 0.0,
      "negative": 0.342,
      "neutral": 0.658
    },
    "textblob_polarity": -0.625,
    "method": "vader_textblob_combined"
  },
  "nlp_processed_at": "2025-08-05T23:XX:XX",
  "sentiment_updated_at": "2025-08-05T23:XX:XX"
}
```

## 🏗️ Architecture & Design Patterns

### 1. Modular Design
- **Separation of Concerns**: Each script handles a specific extraction phase
- **Data Pipeline**: Clear progression from raw scraping to processed insights
- **Error Handling**: Robust exception management at each processing stage

### 2. Data Flow
```
Canadian Tire Website
       ↓
  Product Scraper (simple_scraper.py)
       ↓
  Review Scraper (review_scraper.py)  
       ↓
  Data Cleaner (clean_products.py)
       ↓
  MongoDB Loader (setup_database.py)
       ↓
  NLP Processor (basic_nlp_processing.py)
       ↓
  Sentiment Analyzer (sentiment_analysis.py)
       ↓
  Analytics & Insights
```

### 3. Quality Assurance
- **Data Validation**: Schema validation at each processing step
- **Duplicate Prevention**: Review ID tracking to prevent duplicates
- **Progress Tracking**: Resumable operations with state persistence
- **Error Logging**: Comprehensive logging for debugging and monitoring

## 🔧 Configuration & Customization

### Performance Optimization
```python
# In review_scraper.py - Enable headless mode for faster processing
options.add_argument("--headless")

# Adjust pagination limits based on requirements
reviews = handle_review_pagination(driver, max_pages=5)  # Increase for more reviews

# Parallel processing for large datasets
python parallel_review_scraper.py  # Multi-threaded version
```

### MongoDB Configuration
```python
# Update connection string in NLP scripts
uri = "mongodb+srv://username:password@cluster.mongodb.net/..."

# Database and collection names
database: canadian_tire_scraper
collections: products, reviews
```

### Search Customization
```python
# Modify search terms in simple_scraper.py
search_url = "https://www.canadiantire.ca/en/search-results.html?q=bikes"
# Could be changed to: "mountain+bikes", "kids+bikes", etc.
```

## 🛠️ Technical Troubleshooting

### Common Issues & Solutions

#### 1. ChromeDriver Compatibility
```bash
# Update ChromeDriver
pip install --upgrade webdriver-manager
```

#### 2. Review Loading Timeouts
```python
# Increase timeout in wait_for_reviews_section_to_load()
def wait_for_reviews_section_to_load(driver, timeout=60):  # Increase from 30
```

#### 3. Bazaarvoice Element Changes
If Canadian Tire updates their review system:
- Check CSS selectors in `click_on_review_count()`
- Update pagination selectors in `handle_review_pagination()`
- Verify review container IDs in `extract_individual_reviews()`

#### 4. MongoDB Connection Issues
```bash
# Check network connectivity and credentials
# Verify cluster whitelist includes your IP
# Confirm database permissions
```

### Performance Monitoring
```python
# Track extraction metrics
print(f"Products extracted: {len(products)}")
print(f"Reviews per minute: {reviews_count / elapsed_minutes}")
print(f"Success rate: {successful_extractions / total_attempts * 100}%")
```

## 📁 Project Structure & Files

```
Web-Scraper/
├── simple_scraper.py          # Main product extraction script
├── review_scraper.py          # Review extraction with pagination
├── parallel_review_scraper.py # Multi-threaded review extraction
├── clean_products.py          # Data normalization and enhancement
├── setup_database.py          # MongoDB integration and data loading
├── productos_scraped_v0.json  # Raw product data
├── productos_cleaned.json     # Enhanced product data
├── product_reviews.json       # Complete review dataset
├── product_ratings_summary.json # Aggregated rating data
├── requirements.txt           # Python dependencies
├── NLP/
│   ├── basic_nlp_processing.py      # Text tokenization and processing
│   ├── sentiment_analysis.py       # Sentiment classification
│   └── reprocess_all_sentiments.py # Batch sentiment reprocessing
└── README.md                  # This documentation
```

## ⚠️ Important Disclaimers

1. **Legal Compliance**: This scraper is designed for educational and research purposes
2. **Rate Respectful**: Includes appropriate delays and follows best practices
3. **Site Changes**: May require updates if Canadian Tire modifies their site structure
4. **Data Currency**: Captures point-in-time data; prices and availability change frequently
5. **Review Authenticity**: Does not verify authenticity of customer reviews
6. **Bike Focus**: Optimized specifically for bicycle products; may require modification for other categories
