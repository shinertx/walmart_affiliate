import os
import ssl
import certifi
import time
import shopify
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    raise SystemExit("Error: Shopify credentials missing.")

# Fix SSL Context for Shopify API
ssl_context = ssl.create_default_context(cafile=certifi.where())
import urllib.request
original_urlopen = urllib.request.urlopen

def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)
urllib.request.urlopen = patched_urlopen

session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

page_size = 50  # smaller page for test runs
since_id = None
updated_variants = 0
failed_variants = 0
# Optional test limit: set TEST_MAX_PRODUCTS to a positive integer to cap processed products.
# If unset or set to 0/negative, process all.
try:
    raw_limit = os.getenv("TEST_MAX_PRODUCTS", "")
    max_products = int(raw_limit) if raw_limit.strip() != "" else 0
except Exception:
    max_products = 0
processed_products = 0

print("Starting bulk inventory update to 50...")

while True:
    kwargs = {'limit': page_size}
    if since_id is not None:
        kwargs['since_id'] = since_id
    products = shopify.Product.find(**kwargs)
    if not products:
        break

    for p in products:
        for v in p.variants:
            try:
                # Ensure inventory is managed by Shopify
                v.inventory_management = 'shopify'
                # Set quantity to 50
                v.inventory_quantity = 50
                # Optional: prevent oversell
                v.inventory_policy = 'deny'
                # Save variant
                if v.save():
                    updated_variants += 1
                else:
                    failed_variants += 1
                # Gentle rate limit
                time.sleep(0.05)
            except Exception as e:
                failed_variants += 1
                print(f"Failed variant {v.id}: {e}")
        # small pause between products
        time.sleep(0.05)
        processed_products += 1
        if max_products > 0 and processed_products >= max_products:
            break

    since_id = products[-1].id
    # Basic progress output
    print(f"Progress: updated={updated_variants}, failed={failed_variants}, last_product_id={since_id}")
    if max_products > 0 and processed_products >= max_products:
        break

print("Bulk update complete.")
print(f"Updated variants: {updated_variants}")
print(f"Failed variants: {failed_variants}")
