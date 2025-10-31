# Walmart Affiliate API Testing Tool

This project tests the throughput and performance of Walmart's Affiliate API to determine optimal batch sizes for product catalog retrieval and identify API limits.

## 🚀 Quick Start

1. **Run the setup script:**
```bash
./setup.sh
```

2. **Add your API credentials to `.env`:**
```bash
WALMART_API_KEY=your_api_key_here
PUBLISHER_ID=your_publisher_id_here  # Optional
CAMPAIGN_ID=your_campaign_id_here    # Optional  
AD_ID=your_ad_id_here               # Optional
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
├── main.py              # Main testing script
├── quick_test.py         # Quick API connection test
├── setup.sh             # Automated setup script
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── src/
│   ├── walmart_api.py   # API client class
│   ├── batch_tester.py  # Batch testing logic
│   └── config.py        # Configuration management
└── results/            # Test output files
```

## 🔍 Troubleshooting

### Common Issues

**"API connection test failed"**
- Check your `WALMART_API_KEY` in `.env`
- Verify you have internet connection
- Ensure API key is valid and active

**"Import errors"**
- Run `./setup.sh` to install dependencies
- Activate virtual environment: `source venv/bin/activate`

**"Rate limited / 429 errors"**
- The tool automatically handles rate limiting with exponential backoff
- Increase `delay_between_requests` in config if needed

**"SSL/Certificate errors"**
- Update certificates: `pip install --upgrade certifi`

## 📚 API Documentation

For full Walmart API documentation, visit:
- [Walmart Developer Portal](https://developer.walmart.com/)
- [Affiliate API Documentation](https://developer.walmart.com/api/us/affiliate)

## 📄 License

This project is for testing and educational purposes. Ensure compliance with Walmart's API Terms of Service.