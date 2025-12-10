# Walmart Affiliate API Testing & Access Guide

This project helps you access Walmart's Affiliate API using RSA-signed requests and tests throughput (batch sizes, response times, and limits).

## 🚀 Quick Start

1) Run the setup script

```bash
./setup.sh
```

2) Create and add your Walmart Affiliate API credentials to `.env`

Required
- WALMART_CONSUMER_ID: Your Consumer ID from the Walmart Developer Portal
- WALMART_PRIVATE_KEY_VERSION: Key version shown next to your uploaded public key (usually "1")
- WALMART_PRIVATE_KEY_PATH: Absolute path to the RSA private key that pairs with the uploaded public key

Optional
- WALMART_PRIVATE_KEY: Base64-encoded DER of your private key (use instead of WALMART_PRIVATE_KEY_PATH)
- PUBLISHER_ID, CAMPAIGN_ID, AD_ID: Affiliate tracking parameters if you have them

You can start from `.env.example` and fill in the values.

3) Test your connection

```bash
python quick_test.py
```

4) Run batch testing

```bash
python main.py
```

## 📋 Requirements

- Python 3.8+
- Walmart Developer account with access to the US Affiliate Product API
- RSA key pair (2048-bit); public key uploaded in Developer Portal; private key available locally
- Internet connection

## 🎯 What This Tool Tests

### API Endpoints
- Catalog (paginated items): `https://developer.api.walmart.com/api-proxy/service/affil/product/v2/paginated/items`
- Items (by IDs/UPC/GTIN): `https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items`

Auth: Requests are signed with RSA-SHA256 using headers:
- WM_CONSUMER.ID
- WM_CONSUMER.INTIMESTAMP (ms since epoch)
- WM_SEC.KEY_VERSION
- WM_SEC.AUTH_SIGNATURE (base64 RSA-SHA256 signature over the canonical string)

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
  },
}
```

## 🛠️ Project Structure

```
walmart_affiliate/
├── main.py                  # Main testing script
├── quick_test.py            # Quick API connection test
├── setup.sh                 # Automated setup script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template (RSA-based)
├── src/
│   ├── walmart_api.py       # API client with RSA-signed auth
│   ├── batch_tester.py      # Batch testing logic
│   └── config.py            # Configuration management
└── results/                 # Test output files
```

## 🔐 How Signing Works

We build a canonical string by sorting and joining these header values with newlines and a trailing newline:

```
WM_CONSUMER.ID
WM_CONSUMER.INTIMESTAMP
WM_SEC.KEY_VERSION
```

The RSA-SHA256 signature of that string becomes `WM_SEC.AUTH_SIGNATURE` (base64). If any of the values are wrong (e.g., wrong key version, missing timestamp, private key doesn’t match uploaded public key), requests will be rejected.

## 🔍 Troubleshooting

### Common Issues

**"API connection test failed"**
- Ensure `.env` has WALMART_CONSUMER_ID
- Verify WALMART_PRIVATE_KEY_PATH points to the correct private key file (PEM) or set WALMART_PRIVATE_KEY (base64 DER)
- Confirm the uploaded public key in the portal matches your private key; verify Key Version
- Check network connectivity

**"Import errors"**
- Run `./setup.sh` to install dependencies
- Activate virtual environment: `source venv/bin/activate`

**"Rate limited / 429 errors"**
- The tool automatically handles rate limiting with exponential backoff
- Increase `DELAY_BETWEEN_REQUESTS` in `.env` or config if needed

**"SSL/Certificate errors"**
- Update certificates: `pip install --upgrade certifi`

## 📚 API Documentation

For full Walmart API documentation, visit:
- Walmart Developer Portal: https://developer.walmart.com/
- Affiliate Product APIs: https://developer.walmart.com/api/us/affiliate

Portal steps (high level):
1) Create an app for US Affiliate Product API
2) Generate/upload a 2048-bit RSA public key (PEM/DER)
3) Note your Consumer ID and Key Version
4) Use the matching private key locally via WALMART_PRIVATE_KEY_PATH or WALMART_PRIVATE_KEY

## 📄 License

This project is for testing and educational purposes. Ensure compliance with Walmart’s API Terms of Service.