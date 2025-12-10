# Walmart-to-Shopify Automated Dropshipping & Affiliate System

## 🎯 Project Goal
This system is a high-performance, automated engine designed to populate a Shopify store with tens of thousands of Walmart products. It operates as a hybrid **Dropshipping/Affiliate** model:
1.  **Product Discovery:** Scrapes high-quality, best-selling products from Walmart.com using the official API.
2.  **Import Engine:** Automatically creates products in Shopify with clean descriptions, images, and pricing.
3.  **Inventory Sync:** Connects directly to **AutoDS** for fulfillment and inventory management.
4.  **Affiliate Integration:** Generates and stores Walmart Affiliate links in product metafields for alternative monetization.

## 🚀 System Architecture: "The Waves"
To maximize throughput and avoid bottlenecks, the system runs multiple parallel "Waves" of workers, each targeting specific categories.

### 🌊 Wave 2: Best Sellers (Core)
*   **Script:** `import_wave2_bestsellers.py`
*   **Focus:** High-volume "Power Keywords" (Electronics, Home, Toys, Automotive).
*   **Goal:** Build the store's foundation with popular items.

### 🌊 Wave 3: Expansion (Niche)
*   **Script:** `import_wave3_expansion.py`
*   **Focus:** Deep-dive categories (Vacuums, Sports, Household).
*   **Goal:** Capture specific niches with high search intent.

### 🌊 Wave 4: New Horizons (Consumables)
*   **Script:** `import_wave4_expansion.py`
*   **Focus:** Recurring purchase items (Beauty, Pets, Baby, Tools).
*   **Goal:** Drive repeat traffic and volume.

---

## 🛠️ Operational Logic

### 1. Pricing Strategy
We apply a dynamic markup formula to ensure profitability after fees:
$$ \text{Price} = \frac{(\text{Cost} \times 1.188) + 0.30}{0.971} $$
*   **1.188:** Covers estimated tax (8%) and margin (10%).
*   **+0.30:** Fixed transaction fee.
*   **0.971:** Covers payment processing fees (2.9%).

### 2. Inventory & Fulfillment (AutoDS)
*   **Detection:** The system automatically detects the `AutoDS` fulfillment service handle.
*   **Assignment:** Products are assigned to AutoDS immediately upon creation.
*   **Stock:** Inventory is initialized to **50** to ensure availability.
*   **Conflict Resolution:** The system automatically disconnects the "Default" location to prevent "Multiple Location" errors.

### 3. Rate Limiting & Stability
*   **Shopify API:** Workers sleep for **10 seconds** between imports to respect the leaky bucket limit.
*   **Error Handling:** Automatically pauses for **30 seconds** if a `429 Too Many Requests` error is encountered.

---

## ☁️ Cloud Deployment Guide

### 1. Setup
```bash
# Clone repo
git clone <repo_url>
cd walmart_affiliate

# Install dependencies
pip install -r requirements.txt

# Configure .env
# Add SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN, WALMART_PRIVATE_KEY_PATH, etc.
```

### 2. Launching the Engine
To start all 15+ parallel workers in the background:

```bash
# Launch all waves
nohup python3 launch_parallel.py > logs/wave2.out 2>&1 &
nohup python3 launch_wave3.py > logs/wave3.out 2>&1 &
nohup python3 launch_wave4.py > logs/wave4.out 2>&1 &
```

### 3. Monitoring
*   **Check Status:** `ps aux | grep "import_wave"`
*   **Count Products:** `python3 count_products.py`
*   **View Logs:** `tail -f logs/wave2.out`

### 4. Stopping
```bash
pkill -f "import_wave"
pkill -f "launch_"
```

---

## 📂 File Structure
*   `src/walmart_api.py`: Core wrapper for Walmart API (Search, Affiliate Link Gen).
*   `import_wave*.py`: The worker scripts for each wave.
*   `launch_*.py`: The launcher scripts that manage parallel processes.
*   `count_products.py`: Utility to check total store count.
*   `inspect_location.py`: Utility to debug Shopify locations/fulfillment services.

---

## ⚠️ Important Notes
*   **Affiliate Links:** Stored in `product.metafields.walmart.affiliate_url`.
*   **Descriptions:** Cleaned to remove direct "Buy at Walmart" links from the visible body text.
*   **SSL/Certifi:** Scripts include a patch for Python SSL context to work reliably with Shopify's API on macOS/Linux.

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