# Quick Start: Import 25,000 Walmart Products to Shopify

This is a 5-minute quick start guide to get you importing products immediately.

## Prerequisites ✓

- Python 3.7+ installed
- Walmart API credentials (Consumer ID + Private Key)
- Shopify store with Admin API access token

## Step 1: Setup (2 minutes)

```bash
# Clone and setup
git clone https://github.com/shinertx/walmart_affiliate.git
cd walmart_affiliate
./setup.sh
```

## Step 2: Configure (2 minutes)

Create `.env` file with your credentials:

```bash
# Walmart API
WALMART_CONSUMER_ID=your_consumer_id_here
WALMART_PRIVATE_KEY_PATH=/path/to/walmart_private_key.pem

# Shopify API
SHOPIFY_SHOP_NAME=my-store
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx
```

**Get Shopify credentials:**
1. Shopify Admin → Settings → Apps → Develop apps
2. Create app with `write_products` and `read_products` permissions
3. Copy Access Token and Shop Name

## Step 3: Test Connection (30 seconds)

```bash
python walmart_to_shopify_importer.py --test-only
```

Expected output:
```
✅ Walmart API connection successful
✅ Shopify API connection successful
```

## Step 4: Import Products (1 minute to start)

### Option A: Full Import (25,000 products)
```bash
python walmart_to_shopify_importer.py
```

### Option B: Test Import (100 products)
```bash
python walmart_to_shopify_importer.py --count 100
```

### Option C: Custom Import
```bash
# 1,000 Electronics and Baby products
python walmart_to_shopify_importer.py --count 1000 --categories "Electronics,Baby"
```

## What Happens During Import

1. **Fetches** products from Walmart in batches
2. **Filters** by category (Electronics, Baby by default)
3. **Excludes** third-party sellers (Walmart only)
4. **Validates** product data quality
5. **Transforms** to Shopify format
6. **Creates** products in your Shopify store

## Monitor Progress

Watch real-time progress in console:
```
[1/15230] Importing: Samsung Galaxy Buds...
  ✅ Created product in Shopify (ID: 8234567890)
[2/15230] Importing: Fisher-Price Baby Swing...
  ✅ Created product in Shopify (ID: 8234567891)
...
```

## Check Results

After import completes:

1. **Shopify Admin**: View imported products
2. **Logs**: Check `logs/import_*.log` for details
3. **Statistics**: See `import_stats/import_stats_*.json` for metrics

## Common Commands

```bash
# Test only (no import)
python walmart_to_shopify_importer.py --test-only

# Import 1,000 products
python walmart_to_shopify_importer.py --count 1000

# Different categories
python walmart_to_shopify_importer.py --categories "Toys,Home,Sports"

# Help
python walmart_to_shopify_importer.py --help
```

## Expected Import Times

- **100 products**: ~3 minutes
- **1,000 products**: ~30 minutes
- **10,000 products**: ~5 hours
- **25,000 products**: ~12-15 hours

*Run in background for large imports*

## Troubleshooting

**"Connection failed"**
- Check credentials in `.env`
- Verify Shopify app permissions
- Ensure private key path is correct

**"Rate limited"**
- Normal - automatic retry happens
- Increase delays if persistent:
  ```bash
  SHOPIFY_RATE_LIMIT_DELAY=1.0
  ```

**"No products imported"**
- Check category filters
- Verify products exist in categories
- Review logs for details

## What Gets Imported

✅ **Included:**
- Walmart-sold products (no third-party)
- Electronics category products
- Baby category products
- Products available online
- Complete product data

❌ **Excluded:**
- Third-party marketplace sellers
- Out of stock items
- Products without prices
- Incomplete product data
- Products outside selected categories

## Next Steps

1. **Review Products**: Check Shopify Admin
2. **Set Inventory**: Update stock levels
3. **Create Collections**: Organize products
4. **Configure Shipping**: Set shipping rates
5. **Test Checkout**: Verify everything works

## Full Documentation

- **Setup Guide**: See `SHOPIFY_IMPORT_GUIDE.md`
- **Technical Details**: See `IMPLEMENTATION_SUMMARY.md`
- **General Info**: See `README.md`

## Support

- Check logs in `logs/` directory
- Review statistics in `import_stats/`
- File issues on GitHub

---

**That's it!** You're ready to import 25,000 Walmart products to Shopify. 🚀

For detailed documentation, see the other guide files in this repository.
