import shopify
import os
import time
import ssl
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix SSL Context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Shopify Configuration
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("Error: SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN must be set in .env")
    exit(1)

# Initialize Shopify API
session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

# Monkey patch SSL context for urllib (used by pyactiveresource)
import urllib.request
original_urlopen = urllib.request.urlopen
def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)
urllib.request.urlopen = patched_urlopen

def purge_all_products():
    print("⚠️  WARNING: This will ARCHIVE ALL products in your Shopify store.")
    print("Waiting 5 seconds before starting... Press Ctrl+C to cancel.")
    time.sleep(5)
    
    print("🚀 Starting Purge...")
    
    # Fetch all products (using cursor pagination if needed, but simple loop for now)
    # Shopify API limits to 250 per page
    
    page = shopify.Product.find(limit=250)
    total_archived = 0
    
    while page:
        for product in page:
            if product.status != 'archived':
                try:
                    product.status = 'archived'
                    product.tags = "Purged-Reset"
                    if product.save():
                        print(f"📦 Archived: {product.title} (ID: {product.id})")
                        total_archived += 1
                    else:
                        print(f"❌ Failed to archive: {product.title}")
                except Exception as e:
                    print(f"❌ Error archiving {product.id}: {e}")
                
                # Rate limit protection
                time.sleep(0.2)
        
        if page.has_next_page():
            page = page.next_page()
        else:
            break
            
    print(f"\n✅ Purge Complete. Total Archived: {total_archived}")

if __name__ == "__main__":
    purge_all_products()
