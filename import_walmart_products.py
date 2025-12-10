import sys
import os
from pathlib import Path
import time
import json
import ssl
import certifi
from dotenv import load_dotenv
import shopify

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

# Fix SSL Context for Shopify API
ssl_context = ssl.create_default_context(cafile=certifi.where())
import urllib.request
original_urlopen = urllib.request.urlopen
def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)
urllib.request.urlopen = patched_urlopen

# Configuration
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("Error: Shopify credentials missing.")
    exit(1)

# Initialize Shopify
session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

# Initialize Walmart
walmart_client = WalmartAPIClient()

def calculate_price(cost):
    """
    Pricing Formula:
    ((Cost * 1.08 Tax * 1.10 Markup) + 0.30 Fee) / (1 - 0.029 Processing)
    Simplified: (Cost * 1.188 + 0.30) / 0.971
    """
    if not cost: return 0.0
    target = (cost * 1.188 + 0.30) / 0.971
    return round(target, 2)

def import_products(query, category_name, limit=50):
    print(f"\n🔍 Searching Walmart for '{query}' in category '{category_name}'...")
    
    # Search Walmart
    # Note: The search method in walmart_api.py might need 'numItems' or similar param
    # We will try to fetch 'limit' items. The API might paginate.
    # For this version, we'll request 'numItems' up to 25 (max per page usually) and loop if needed
    # But to keep it simple and safe, we'll just ask for 25 first.
    
    response = walmart_client.search(query, numItems=min(limit, 25))
    
    if not response['success']:
        print(f"❌ Walmart Search Failed: {response.get('error')}")
        return

    items = response['data'].get('items', [])
    print(f"   Found {len(items)} items. Filtering...")
    
    imported_count = 0
    
    for item in items:
        try:
            # 1. Filter: Sold by Walmart (First Party)
            marketplace = item.get('marketplace')
            seller_info = item.get('sellerInfo', '')
            
            is_walmart = (marketplace is False) or ("walmart" in seller_info.lower())
            
            if not is_walmart:
                print(f"   Skipping {item.get('itemId')} (3rd Party: {seller_info})")
                continue
                
            # 2. Filter: In Stock
            if item.get('stock') != 'Available':
                print(f"   Skipping {item.get('itemId')} (Out of Stock)")
                continue
                
            # 3. Prepare Data
            walmart_id = str(item['itemId'])
            title = item.get('name')
            description = item.get('longDescription') or item.get('shortDescription') or ""
            cost = item.get('salePrice')
            images = item.get('imageEntities', [])
            
            if not cost:
                continue
                
            target_price = calculate_price(cost)
            
            # 4. Create in Shopify
            # Check if exists first to avoid duplicates (optional, but good practice)
            # For now, we assume clean slate or we just create new ones.
            
            product = shopify.Product()
            product.title = title
            product.body_html = description
            product.vendor = "Walmart"
            product.product_type = category_name
            product.tags = f"Walmart-Import, {category_name}, Sold-by-Walmart"
            product.status = "active"
            
            # Images
            if images:
                product.images = [{"src": img.get('largeImage')} for img in images if img.get('largeImage')]
            elif item.get('largeImage'):
                 product.images = [{"src": item.get('largeImage')}]

            # Variant (Price & SKU)
            variant = shopify.Variant()
            variant.price = target_price
            variant.sku = walmart_id
            variant.inventory_management = "shopify"
            variant.inventory_policy = "deny" # Don't sell if OOS
            variant.inventory_quantity = 10 # Default starting stock
            
            product.variants = [variant]
            
            if product.save():
                print(f"✅ Imported: {title[:30]}... (SKU: {walmart_id}) @ ${target_price}")
                imported_count += 1
            else:
                print(f"❌ Failed to save {title[:30]}...")
                
            # Rate limit
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error processing item: {e}")

    print(f"✨ Import Complete for '{query}'. Imported {imported_count} items.")

if __name__ == "__main__":
    print("🚀 Starting Wave 1 Import (Electronics, Toys, Baby)...")
    
    # Electronics (High Ticket)
    import_products("PlayStation 5 Console", "Electronics", limit=25)
    import_products("Xbox Series X", "Electronics", limit=25)
    import_products("Nintendo Switch OLED", "Electronics", limit=25)
    import_products("Samsung 4K TV", "Electronics", limit=25)
    import_products("Apple iPad", "Electronics", limit=25)
    import_products("HP Laptop", "Electronics", limit=25)
    
    # Toys (Holiday)
    import_products("Lego Set", "Toys", limit=25)
    import_products("Barbie Dreamhouse", "Toys", limit=25)
    import_products("Hot Wheels", "Toys", limit=25)
    import_products("Nerf Gun", "Toys", limit=25)
    import_products("Board Games", "Toys", limit=25)
    
    # Baby (Evergreen)
    import_products("Pampers Diapers", "Baby", limit=25)
    import_products("Huggies Diapers", "Baby", limit=25)
    import_products("Graco Car Seat", "Baby", limit=25)
    import_products("Baby Stroller", "Baby", limit=25)
    
    print("\n✅ Wave 1 Import Batch Complete!")
