# Walmart Affiliate API Testing Tool & Shopify Integration

This project tests the throughput and performance of Walmart's Affiliate API to determine optimal batch sizes for product catalog retrieval and identify API limits. It also provides a **Shopify integration** to import Walmart products directly to your Shopify store.

## ✨ Features

- **API Performance Testing**: Test Walmart API throughput and find optimal batch sizes
- **Shopify Integration**: Import up to 25,000 Walmart products to your Shopify store
- **Smart Filtering**: Focus on specific categories (Electronics, Baby items, etc.)
- **Quality Control**: Filter out third-party sellers, keeping only Walmart-sold products
- **Automatic Transformation**: Convert Walmart product data to Shopify format
- **Duplicate Prevention**: Avoid importing the same product twice

## 🚀 Quick Start

1. **Run the setup script:**
```bash
./setup.sh
```

2. **Add your API credentials to `.env`:**
```bash
# Walmart API credentials
WALMART_CONSUMER_ID=your_consumer_id_here
WALMART_PRIVATE_KEY_PATH=path/to/your/private_key.pem
PUBLISHER_ID=your_publisher_id_here  # Optional
CAMPAIGN_ID=your_campaign_id_here    # Optional  
AD_ID=your_ad_id_here                # Optional

# Shopify API credentials (for product import)
SHOPIFY_SHOP_NAME=your-shop-name
SHOPIFY_ACCESS_TOKEN=your_shopify_access_token
```

3. **Test your connection:**
```bash
python quick_test.py
```

4. **Run batch testing:**
```bash
python main.py
```

## 📋 Requirements

- Python 3.7+
- Walmart API key (get from [Walmart Developer Portal](https://developer.walmart.com/))
- Internet connection

## 🎯 What This Tool Tests

### API Endpoint
- **Catalog Product API**: `https://developer.api.walmart.com/api-proxy/service/affil/product/v2/paginated/items`
- **Purpose**: Retrieve paginated product catalog with various filtering options
- **Key Parameter**: `count` - Number of items per API call (we test different values)

### Testing Goals
1. **Maximum Batch Size**: Find the highest `count` value the API accepts
2. **Optimal Performance**: Identify the batch size with best throughput (items/second)
3. **Response Times**: Measure how batch size affects response time
4. **Data Volume**: Track response sizes and bandwidth usage
5. **Rate Limits**: Identify any API throttling or limits

## 🧪 Usage Examples

### Basic Testing
```bash
# Standard test with default batch sizes [1, 5, 10, 25, 50, 100, 200, 400, 500, 1000]
python main.py

# Test maximum limits (tries very large batch sizes)
python main.py --mode limits

# Test with custom batch sizes
python main.py --custom-sizes 1,10,50,100,500

# Run multiple iterations for more reliable results
python main.py --iterations 3
```

### Category-Specific Testing  
```bash
# Test electronics category specifically
python main.py --category 3944

# Test multiple categories
python main.py --mode category
```

### Output Control
```bash
# Skip chart generation (faster)
python main.py --no-charts
```

## 🛍️ Shopify Product Import

Import Walmart products directly to your Shopify store with intelligent filtering.

### Prerequisites

1. **Walmart API Credentials**: Set up in `.env` file
2. **Shopify Store**: You need a Shopify store with admin access
3. **Shopify Access Token**: Create a private app or use API credentials

### Getting Shopify Credentials

1. Go to your Shopify Admin
2. Navigate to **Settings > Apps and sales channels > Develop apps**
3. Create a new app with the following permissions:
   - `write_products` - To create products
   - `read_products` - To check for duplicates
4. Copy the **Access Token** and your **Shop Name**

### Import Usage

```bash
# Test connections only (recommended first step)
python walmart_to_shopify_importer.py --test-only

# Import 25,000 products (default: Electronics and Baby categories)
python walmart_to_shopify_importer.py

# Import specific number of products
python walmart_to_shopify_importer.py --count 1000

# Customize categories
python walmart_to_shopify_importer.py --categories "Electronics,Baby,Toys"

# Import with custom batch size for Walmart API
python walmart_to_shopify_importer.py --count 10000 --batch-size 200
```

### Import Features

- **Smart Filtering**:
  - Filters by specified categories (default: Electronics, Baby)
  - Excludes third-party sellers (Walmart-only products)
  - Validates product data quality
  - Prevents duplicate imports

- **Automatic Transformation**:
  - Converts Walmart product structure to Shopify format
  - Maps product images, descriptions, and specifications
  - Creates proper variants and SKUs
  - Adds searchable tags and categories

- **Progress Tracking**:
  - Real-time import progress logs
  - Detailed statistics saved to JSON
  - Error handling and retry logic
  - Rate limiting to respect API limits

### Import Statistics

After import, check the `import_stats/` directory for detailed reports:
- Total products fetched
- Filtering breakdown
- Success/failure counts
- Duplicate detection stats

### Example Import Session

```
🛒 Starting Walmart to Shopify Import
============================================================
Testing API connections...
✅ Walmart API connection successful
✅ Shopify API connection successful

📦 Step 1: Fetching products from Walmart...
Fetching 25000 products in 250 batches
Retrieved 100 items from Walmart API
...

🔍 Step 2: Filtering products...
Products after filtering: 15230
  - Validation failed: 1250
  - Category filtered: 6820
  - Third-party filtered: 1700

📤 Step 3: Importing 15230 products to Shopify...
[1/15230] Importing: Samsung Galaxy Buds...
  ✅ Created product in Shopify (ID: 8234567890)
...
```

## 📊 Results & Analysis

The tool generates several output files in the `results/` directory:

### Files Generated
- **JSON**: Raw test data with full metadata
- **CSV**: Tabular data for easy analysis in Excel/Google Sheets  
- **PNG**: Performance charts and visualizations
- **LOG**: Detailed request/response logs

### Key Metrics Tracked
- **Success Rate**: % of successful requests per batch size
- **Throughput**: Items retrieved per second
- **Response Time**: Total request duration
- **Response Size**: Data volume (bytes/MB)
- **Actual vs Requested**: How many items actually returned

### Sample Output
```
📈 ANALYSIS RESULTS
==========================================
📊 Success Rate by Batch Size:
   1 items: 100.0%
   5 items: 100.0%
   10 items: 100.0%
   25 items: 100.0%
   50 items: 100.0%
   100 items: 100.0%
   200 items: 95.0%
   400 items: 90.0%

🎯 Optimal Batch Size: 100 items
   Max Throughput: 45.2 items/second
   Response Time: 2.21s
   Data Size: 1.2 MB

📏 Maximum Successful Batch: 400 items
```

## ⚙️ Configuration

The tool uses `config.json` for advanced settings:

```json
{
  "testing": {
    "default_batch_sizes": [1, 5, 10, 25, 50, 100, 200, 400, 500, 1000],
    "iterations_per_size": 1,
    "delay_between_requests": 2.0
  },
  "api": {
    "request_timeout": 30,
    "max_retries": 3
  }
}
```

## 🛠️ Project Structure

```
walmart_affiliate/
├── main.py                          # API batch testing script
├── walmart_to_shopify_importer.py   # Shopify product importer
├── quick_test.py                    # Quick API connection test
├── setup.sh                         # Automated setup script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── src/
│   ├── walmart_api.py               # Walmart API client
│   ├── shopify_client.py            # Shopify API client
│   ├── product_transformer.py       # Product data transformer
│   ├── batch_tester.py              # Batch testing logic
│   └── config.py                    # Configuration management
├── results/                         # API test output files
├── logs/                            # Import logs
└── import_stats/                    # Import statistics
```

## 🔍 Troubleshooting

### Common Issues

**"API connection test failed"**
- Check your `WALMART_CONSUMER_ID` and private key in `.env`
- Verify you have internet connection
- Ensure API credentials are valid and active

**"Shopify connection failed"**
- Verify `SHOPIFY_SHOP_NAME` and `SHOPIFY_ACCESS_TOKEN` in `.env`
- Ensure your Shopify app has correct permissions (`write_products`, `read_products`)
- Check that your shop name is correct (without `.myshopify.com`)

**"Import errors"**
- Run `./setup.sh` to install dependencies
- Activate virtual environment: `source venv/bin/activate`

**"Rate limited / 429 errors"**
- The tool automatically handles rate limiting with exponential backoff
- Increase `SHOPIFY_RATE_LIMIT_DELAY` in `.env` if needed
- Walmart API: Increase `delay_between_requests` in config

**"SSL/Certificate errors"**
- Update certificates: `pip install --upgrade certifi`

**"No products passing filters"**
- Check category names are correct (case-insensitive)
- Verify products are available in specified categories
- Try broader category filters or reduce filtering criteria

## 📚 API Documentation

For full Walmart API documentation, visit:
- [Walmart Developer Portal](https://developer.walmart.com/)
- [Affiliate API Documentation](https://developer.walmart.com/api/us/affiliate)

## 📄 License

This project is for testing and educational purposes. Ensure compliance with Walmart's API Terms of Service.