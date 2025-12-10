import os
import ssl
import certifi
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

# Iterate through products and aggregate inventory across variants
page_size = 250
since_id = None

products_with_stock = 0
products_without_stock = 0
variants_in_stock = 0
variants_out_stock = 0

def has_stock(product):
    # Sum all variant inventory_quantity (Shopify-managed)
    total = 0
    for v in product.variants:
        qty = getattr(v, 'inventory_quantity', None)
        if qty is None:
            continue
        total += int(qty)
    return total > 0, total

while True:
    kwargs = {'limit': page_size}
    if since_id is not None:
        kwargs['since_id'] = since_id
    products = shopify.Product.find(**kwargs)
    if not products:
        break

    for p in products:
        in_stock, total = has_stock(p)
        if in_stock:
            products_with_stock += 1
        else:
            products_without_stock += 1
        for v in p.variants:
            qty = getattr(v, 'inventory_quantity', None)
            if qty is None:
                continue
            if int(qty) > 0:
                variants_in_stock += 1
            else:
                variants_out_stock += 1

    # Advance pagination using the last product ID
    since_id = products[-1].id

print("Shopify Inventory Summary:")
print(f"  Products with stock: {products_with_stock}")
print(f"  Products without stock: {products_without_stock}")
print(f"  Variants in stock: {variants_in_stock}")
print(f"  Variants out of stock: {variants_out_stock}")
