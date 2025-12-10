# Cloud Deployment & Operation Guide

This guide documents the current architecture and operational procedures for the Walmart-to-Shopify Affiliate/Dropshipping system. Use this to deploy and restart the system on a cloud server (e.g., AWS EC2, DigitalOcean, Heroku).

## 🚀 System Architecture

The system is designed for **high-throughput parallel processing**. Instead of a single script, we run multiple "Waves" of workers concurrently to maximize product discovery and import speed while respecting API rate limits.

### The 3 Waves
1.  **Wave 2 (Best Sellers)**
    *   **Script:** `import_wave2_bestsellers.py`
    *   **Launcher:** `launch_parallel.py`
    *   **Categories:** Electronics, Home, Toys, Sports, Automotive, Office, Patio.
    *   **Strategy:** Targets high-volume "Power Keywords" (e.g., TV, Laptop, Lego).

2.  **Wave 3 (Expansion)**
    *   **Script:** `import_wave3_expansion.py`
    *   **Launcher:** `launch_wave3.py`
    *   **Categories:** Vacuums, Sports (Deep Dive), Household.
    *   **Strategy:** Targets specific niches with deeper keyword lists.

3.  **Wave 4 (New Horizons)**
    *   **Script:** `import_wave4_expansion.py`
    *   **Launcher:** `launch_wave4.py`
    *   **Categories:** Beauty, Pets, Tools, Baby, Clothing.
    *   **Strategy:** Targets fresh, high-demand consumable and essential categories.

---

## 🛠️ Setup & Installation

### 1. Environment Setup
Ensure Python 3.10+ is installed.

```bash
# Clone the repository
git clone <your-repo-url>
cd walmart_affiliate

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (.env)
Create a `.env` file in the root directory with your credentials:

```ini
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
WALMART_API_KEY=... (if applicable, currently using public search)
```

---

## ▶️ Running the System

To start the full import engine (approx. 15 parallel workers), run the following commands. Using `nohup` or `screen`/`tmux` is recommended on a cloud server to keep processes running after disconnect.

### Option A: Quick Start (Terminal)
```bash
python3 launch_parallel.py &
python3 launch_wave3.py &
python3 launch_wave4.py &
```

### Option B: Robust Cloud Start (nohup)
This keeps the scripts running even if you close the SSH session.

```bash
nohup python3 launch_parallel.py > logs/wave2.out 2>&1 &
nohup python3 launch_wave3.py > logs/wave3.out 2>&1 &
nohup python3 launch_wave4.py > logs/wave4.out 2>&1 &
```

---

## 🧠 Key Logic & Features

### 1. Inventory Management (AutoDS)
*   **Logic:** The scripts automatically detect the **AutoDS Fulfillment Service** (`autods-prod-wwbybglb` or similar).
*   **Action:** When creating a product, it assigns the inventory management directly to AutoDS and sets the quantity to **50**.
*   **Why:** This prevents "Multiple Location" errors and ensures orders are routed correctly for fulfillment.

### 2. Pricing Strategy
*   **Formula:** `((Cost * 1.188) + 0.30) / 0.971`
*   **Breakdown:**
    *   `1.188`: Covers estimated tax and margin.
    *   `+ 0.30`: Fixed transaction fee.
    *   `/ 0.971`: Accounts for payment processing fees (2.9%).

### 3. Rate Limiting
*   **Shopify:** Scripts sleep for **10 seconds** between imports to stay within the leaky bucket limit.
*   **429 Errors:** If a "Too Many Requests" error occurs, the script automatically pauses for **30 seconds** before retrying.

### 4. Content Cleaning
*   **Descriptions:** Affiliate links are **removed** from the visible product description to keep the store professional.
*   **Metafields:** The affiliate link is stored securely in the product's **Metafields** (`walmart.affiliate_url`) for use in themes or buttons.

---

## 📊 Monitoring

To check progress on the server:

**Check Active Processes:**
```bash
ps aux | grep "import_wave"
```

**Count Products:**
```bash
python3 count_products.py
```

**View Logs:**
```bash
tail -f logs/wave3_vacuums.log
# or
tail -f logs/wave2.out
```

## 🛑 Stopping the System

To stop all workers:
```bash
pkill -f "import_wave"
pkill -f "launch_"
```
