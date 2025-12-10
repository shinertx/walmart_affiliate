import sys
import os
from pathlib import Path
import json
import time
import re
import requests
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

# Shopify Configuration
SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("❌ Error: Shopify credentials not found in .env file.")
    sys.exit(1)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def clean_html(raw_html):
    if not raw_html:
        return ""
    # Basic cleanup, but Shopify supports HTML so we keep it mostly intact
    # Just removing some potential bad characters if needed
    return raw_html

def generate_handle(title):
    handle = title.lower()
    handle = re.sub(r'[^a-z0-9\s-]', '', handle)
    handle = re.sub(r'\s+', '-', handle)
    return handle[:255]

def create_shopify_product(item):
    title = item.get('name', 'Unknown PlayStation Item')
    description = item.get('shortDescription') or item.get('longDescription') or title
    price = item.get('salePrice')
    msrp = item.get('msrp')
    item_id = str(item.get('itemId'))
    
    # Get the best image
    image_url = item.get('largeImage') or item.get('mediumImage') or item.get('thumbnailImage')
    
    if not price:
        print(f"   ⚠️ Skipping '{title}' - No price found.")
        return False

    product_payload = {
        "product": {
            "title": title,
            "body_html": description,
            "vendor": "Sony",
            "product_type": "Gaming Console",
            "tags": "PlayStation, PS5, Console, Gaming, Walmart, AutoDS",
            "status": "active",
            "variants": [
                {
                    "price": str(price),
                    "compare_at_price": str(msrp) if msrp else None,
                    "sku": item_id,
                    "inventory_management": "shopify",
                    "inventory_policy": "deny",
                    "fulfillment_service": "manual",
                    "inventory_quantity": 10,
                    "requires_shipping": True,
                    "taxable": True
                }
            ],
            "images": [
                {"src": image_url}
            ] if image_url else []
        }
    }

    # Check if product exists by SKU (to avoid duplicates)
    # Note: Searching by SKU isn't a direct endpoint, usually we search by handle or tag.
    # For simplicity in this "push all" request, we'll try to create. 
    # If we wanted to be safer, we'd search first.
    
    response = requests.post(f"{BASE_URL}/products.json", headers=HEADERS, json=product_payload)
    
    if response.status_code == 201:
        print(f"   ✅ Created: {title}")
        return True
    elif response.status_code == 429:
        print("   ⏳ Rate limited. Sleeping 2s...")
        time.sleep(2)
        return create_shopify_product(item) # Retry
    else:
        print(f"   ❌ Failed to create '{title}': {response.text}")
        return False

def main():
    client = WalmartAPIClient()
    
    queries = [
        "PlayStation 5 Console",
        "PlayStation 5 Slim",
        "PlayStation 5 Bundle"
    ]
    
    all_items = {} 
    
    print("🔍 Fetching PlayStation products from Walmart...")
    
    for query in queries:
        print(f"   Searching for '{query}'...")
        for page in range(2): # Fetch 2 pages per query
            start_index = page * 25 + 1
            try:
                search_url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
                headers = client._get_headers()
                params = {
                    'query': query,
                    'numItems': 25,
                    'start': start_index
                }
                
                response = requests.get(search_url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    for item in items:
                        item_id = str(item.get('itemId'))
                        if item_id not in all_items:
                            all_items[item_id] = item
            except Exception as e:
                print(f"   ❌ Error fetching: {e}")

    print(f"📦 Found {len(all_items)} unique items. Starting upload to Shopify...")
    
    success_count = 0
    for i, (item_id, item) in enumerate(all_items.items(), 1):
        print(f"[{i}/{len(all_items)}] Uploading...", end="\r")
        if create_shopify_product(item):
            success_count += 1
        # Small delay to be nice to the API
        time.sleep(0.5)
        
    print(f"\n🎉 Finished! Successfully uploaded {success_count} products to Shopify.")
    print("👉 These products should now be visible in your Shopify Admin and ready to sync to TikTok.")

if __name__ == "__main__":
    main()
