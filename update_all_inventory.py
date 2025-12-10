import os
import ssl
import certifi
import csv
import time
from dotenv import load_dotenv
import shopify

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

def safe_save(resource, retries=3):
    """Saves a Shopify resource with rate limit handling."""
    for attempt in range(retries):
        try:
            return resource.save()
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                wait_time = (attempt + 1) * 2
                print(f"      ⚠️ Rate limit hit. Sleeping {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    return False

def update_all_inventory():
    print("🚀 Starting Bulk Inventory Update & Tracking Log...")
    print("   Target: Set all items to Quantity = 50")
    print("   Tracking: Saving 'inventory_tracker.csv' for future price updates.")
    
    # Prepare CSV for tracking
    csv_file = "inventory_tracker.csv"
    # We append to existing file if it exists to support resuming
    mode = 'a' if os.path.isfile(csv_file) else 'w'
    
    with open(csv_file, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(["Shopify_ID", "Walmart_ID_SKU", "Title", "Current_Price", "Inventory_Set_To"])
        
        # Use cursor pagination to iterate all products
        page_size = 50
        try:
            products = shopify.Product.find(limit=page_size)
        except Exception as e:
            print(f"Error fetching first page: {e}")
            return

        total_processed = 0
        
        while products:
            for product in products:
                try:
                    updated = False
                    walmart_id = ""
                    price = ""
                    
                    for variant in product.variants:
                        old_qty = variant.inventory_quantity
                        if old_qty != 50:
                            variant.inventory_quantity = 50
                            updated = True
                        
                        walmart_id = variant.sku
                        price = variant.price
                    
                    if updated:
                        safe_save(product)
                        time.sleep(0.5) # Small delay after save
                    
                    # Log for tracking
                    writer.writerow([product.id, walmart_id, product.title, price, 50])
                    total_processed += 1
                    
                    if total_processed % 50 == 0:
                        print(f"   ⏳ Processed {total_processed} items...")
                        
                except Exception as e:
                    print(f"   ❌ Error processing {product.id}: {e}")
            
            # Next page
            if products.has_next_page():
                try:
                    # Exponential backoff for pagination
                    time.sleep(1.0) 
                    products = products.next_page()
                except Exception as e:
                    if "429" in str(e):
                        print("   ⚠️ Rate limit on pagination. Sleeping 5s...")
                        time.sleep(5)
                        try:
                            products = products.next_page()
                        except:
                            print("   ❌ Failed to fetch next page after retry.")
                            break
                    else:
                        print(f"   ⚠️ Pagination error: {e}")
                        break
            else:
                break
                
    print(f"\n✨ Complete! Processed {total_processed} items.")
    print(f"📝 Tracking data saved to {csv_file}")

if __name__ == "__main__":
    update_all_inventory()
