# Shopify Import Guide

## Quick Setup Guide for Importing 25,000 Walmart Products to Shopify

This guide walks you through importing Walmart products to your Shopify store.

---

## Prerequisites

### 1. Walmart API Credentials

You need Walmart Affiliate API credentials:

1. Sign up at [Walmart Developer Portal](https://developer.walmart.com/)
2. Create an API application
3. Generate RSA key pair:
   ```bash
   # Generate private key
   openssl genrsa -out walmart_private_key.pem 2048
   
   # Generate public key
   openssl rsa -in walmart_private_key.pem -pubout -out walmart_public_key.pem
   ```
4. Upload the public key to Walmart Developer Portal
5. Get your Consumer ID from the portal

### 2. Shopify API Credentials

You need a Shopify store with API access:

1. Log in to your Shopify Admin
2. Go to **Settings** → **Apps and sales channels** → **Develop apps**
3. Click **Create an app**
4. Name it "Walmart Product Importer"
5. Click **Configure Admin API scopes**
6. Enable these scopes:
   - `write_products` - Create and update products
   - `read_products` - Read product information
7. Click **Install app**
8. Copy the **Admin API access token**
9. Note your **shop name** (e.g., "my-store" from "my-store.myshopify.com")

---

## Installation

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/shinertx/walmart_affiliate.git
cd walmart_affiliate

# Run setup script
./setup.sh
```

### Step 2: Configure Environment

Create a `.env` file with your credentials:

```bash
# Copy the example file
cp .env.example .env

# Edit the file
nano .env  # or use your preferred editor
```

Add your credentials:

```env
# Walmart API
WALMART_CONSUMER_ID=your_consumer_id_here
WALMART_PRIVATE_KEY_PATH=/path/to/walmart_private_key.pem
WALMART_PRIVATE_KEY_VERSION=1
PUBLISHER_ID=your_publisher_id
CAMPAIGN_ID=your_campaign_id
AD_ID=your_ad_id

# Shopify API
SHOPIFY_SHOP_NAME=my-store
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2024-01
```

---

## Usage

### Test Connections First

Always test your API connections before starting the import:

```bash
python walmart_to_shopify_importer.py --test-only
```

You should see:
```
Testing API connections...
✅ Walmart API connection successful
✅ Shopify API connection successful
✅ All connections successful!
```

### Import Products

#### Basic Import (25,000 products from Electronics & Baby)

```bash
python walmart_to_shopify_importer.py
```

#### Custom Import Examples

```bash
# Import 1,000 products (for testing)
python walmart_to_shopify_importer.py --count 1000

# Import from different categories
python walmart_to_shopify_importer.py --categories "Electronics,Baby,Toys,Home"

# Import 10,000 products with larger batch size
python walmart_to_shopify_importer.py --count 10000 --batch-size 200
```

---

## What Gets Filtered Out

The importer automatically filters products to ensure quality:

### ✅ Products INCLUDED:
- Electronics category products
- Baby category products
- Sold by Walmart (not third-party sellers)
- Available online
- Valid price information
- Complete product data

### ❌ Products EXCLUDED:
- Third-party marketplace sellers
- Out of stock items
- Products without valid pricing
- Products outside selected categories
- Incomplete product information

---

## Import Process

The import happens in 3 steps:

### Step 1: Fetch Products from Walmart
- Retrieves products in batches (default: 100 per batch)
- Respects API rate limits
- Logs all requests

### Step 2: Filter Products
- Validates product data
- Checks categories
- Filters third-party sellers
- Removes duplicates

### Step 3: Import to Shopify
- Transforms data to Shopify format
- Creates products with images
- Adds tags and metadata
- Tracks progress and errors

---

## Monitoring Progress

### Real-Time Logs

Watch the console output for real-time progress:

```
[1/15230] Importing: Samsung Galaxy Buds...
  ✅ Created product in Shopify (ID: 8234567890)
[2/15230] Importing: Fisher-Price Baby Swing...
  ✅ Created product in Shopify (ID: 8234567891)
...
[100/15230] PROGRESS UPDATE:
  Imported: 98
  Failed: 2
  Skipped (duplicates): 0
```

### Log Files

Check detailed logs in the `logs/` directory:
```bash
# View the most recent log
tail -f logs/import_*.log
```

### Statistics

After completion, check `import_stats/` for detailed reports:

```bash
cat import_stats/import_stats_*.json
```

Example statistics:
```json
{
  "timestamp": "2025-12-04T10:30:00",
  "target_count": 25000,
  "categories": ["Electronics", "Baby"],
  "statistics": {
    "total_fetched": 25000,
    "validation_failed": 1250,
    "category_filtered": 6820,
    "third_party_filtered": 1700,
    "imported": 15230,
    "failed": 0,
    "skipped_duplicates": 0
  }
}
```

---

## Troubleshooting

### "Walmart API connection failed"
- Verify your `WALMART_CONSUMER_ID` is correct
- Check that your private key path is correct
- Ensure the public key is uploaded to Walmart portal
- Verify your private key has correct permissions (readable)

### "Shopify API connection failed"
- Check your `SHOPIFY_SHOP_NAME` (without `.myshopify.com`)
- Verify your `SHOPIFY_ACCESS_TOKEN`
- Ensure your Shopify app has correct permissions
- Check that the app is installed on your store

### "Rate limited (429 errors)"
- The importer automatically handles rate limiting
- If persistent, increase delays in `.env`:
  ```env
  SHOPIFY_RATE_LIMIT_DELAY=1.0
  DELAY_BETWEEN_REQUESTS=2.0
  ```

### "Not enough products after filtering"
- Try different categories
- Check that products exist in those categories
- Reduce filtering strictness (modify code if needed)

### "Import taking too long"
- Importing 25,000 products takes time (several hours)
- Run in a `tmux` or `screen` session for long imports
- Start with smaller batches to test first

---

## Performance Tips

### 1. Start Small
Test with a small batch first:
```bash
python walmart_to_shopify_importer.py --count 100
```

### 2. Use Screen/Tmux for Large Imports
```bash
# Start a screen session
screen -S walmart_import

# Run the import
python walmart_to_shopify_importer.py

# Detach with Ctrl+A, D
# Reattach later with: screen -r walmart_import
```

### 3. Monitor System Resources
Large imports require:
- Stable internet connection
- Sufficient disk space for logs
- Memory for processing (minimal)

### 4. Schedule Off-Peak
Run during off-peak hours to avoid:
- Competing with customer traffic
- Higher API load
- Potential rate limiting

---

## Product Data Mapping

### Walmart → Shopify Mapping

| Walmart Field | Shopify Field | Notes |
|--------------|---------------|-------|
| itemId | variant.sku | Used as unique identifier |
| name | title | Truncated to 255 chars |
| salePrice | variant.price | Used if available |
| msrp | variant.compare_at_price | Original price |
| brandName | vendor | Product brand |
| categoryPath | product_type | Last category used |
| upc | variant.barcode | For inventory tracking |
| mediumImage | images[0] | Primary image |
| shortDescription | First paragraph | HTML formatted |
| longDescription | Body HTML | Full description |
| features | Bullet list | HTML list |

### Metafields Added

All products include metadata:
- `walmart.item_id` - Original Walmart item ID
- `walmart.product_url` - Link to Walmart product
- `walmart.upc` - UPC/GTIN code
- `walmart.model_number` - Model number if available

---

## Post-Import Tasks

After importing products:

### 1. Review Products in Shopify Admin
- Check product titles and descriptions
- Verify images loaded correctly
- Review pricing

### 2. Set Inventory Levels
- The importer doesn't set inventory quantities
- Update inventory in Shopify Admin or via API
- Consider inventory management tools

### 3. Organize with Collections
- Create collections by category
- Add products to collections
- Set up featured products

### 4. Configure Shipping
- Set up shipping profiles
- Configure shipping rates
- Test checkout process

### 5. Optimize for SEO
- Review product titles for SEO
- Add meta descriptions
- Optimize images with alt text

---

## Support

For issues or questions:
1. Check the main README.md
2. Review logs in `logs/` directory
3. Check import statistics in `import_stats/`
4. File an issue on GitHub

---

## Best Practices

1. **Always test connections first** with `--test-only`
2. **Start with small batches** (100-1000 products)
3. **Monitor the first few imports** to ensure quality
4. **Keep logs** for troubleshooting
5. **Backup your Shopify store** before large imports
6. **Review products** after import for accuracy
7. **Set up proper collections** and navigation
8. **Update inventory levels** after import

---

## Legal Considerations

- Ensure you have rights to sell products listed
- Follow Walmart's affiliate terms of service
- Comply with Shopify's terms of service
- Check product licensing requirements
- Verify pricing and availability regularly

---

Happy importing! 🚀
